#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import re
import sys
import tempfile
import logging
import importlib
from collections import deque
from abc import abstractmethod

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFontMetrics, QPixmap, QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QSlider,
)

from tsugite.utils import resolve_field_path

logger = logging.getLogger(__name__)

def lazy_import_module(widget_name, module_name):
    """ Lazy imports: only load these when widget is created """
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        logger.critical(f"{widget_name} required {module_name}. You can install it: pip install {module_name}")
        sys.exit(1)

class WidgetFactory:
    """Factory for creating widgets from YAML definitions."""

    registry = {
        "const_label":  lambda cfg: ConstLabelWidget(cfg),
        "BoundLabel":   lambda cfg: BoundLabel(cfg),
        "EnumStatusLabel":  lambda cfg: EnumStatusLabel(cfg),
        "ParamWidget":  lambda cfg: ParamWidget(cfg),
        "HealthLabel":  lambda cfg: HealthLabel(cfg),
        "BoundImage":   lambda cfg: BoundImage(cfg),
        "PlotWidget" :  lambda cfg: PlotWidget(cfg),
        "GpsWidget":    lambda cfg: GpsWidget(cfg),
        "ButtonWidget": lambda cfg: ButtonWidget(cfg),
        "table":        lambda cfg: TableWidget(cfg),
        "slider":       lambda cfg: SliderWidget(cfg),
        "PublisherWidget":  lambda cfg: PublisherWidget(cfg),
        "CanGraphWidget": lambda cfg: CanGraphWidget(cfg),
    }

    @classmethod
    def create(cls, widget_cfg: dict):
        wtype = widget_cfg.get("type", "")
        if wtype in cls.registry:
            return cls.registry[wtype](widget_cfg)
        # return a valid BaseWidget (ConstLabelWidget expects a dict cfg)
        return ConstLabelWidget({"text": f"{wtype} - Unknown widget type"})

class BaseWidget(QWidget):
    """Abstract base class for all widgets."""

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.init_ui()

    @abstractmethod
    def init_ui(self):
        """Initialize widget UI."""
        raise NotImplementedError

    def update_data(self, data):
        """Optional: Update widget data (e.g., sensor readings)."""
        pass

    @staticmethod
    def _apply_value_transforms(value, field_type=None, multiplier=None, offset=None):
        """Apply optional multiplier, offset, and type conversion to a value."""
        try:
            # Apply linear transform first
            if multiplier is not None:
                value = value * multiplier
            if offset is not None:
                value = value + offset

            # Apply explicit type conversion
            if field_type:
                if field_type == "int":
                    value = int(value)
                elif field_type == "float":
                    value = float(value)
                elif field_type == "bool":
                    value = bool(value)
                else:
                    logger.warning(f"Unsupported field_type: {field_type}")
        except Exception as e:
            logger.error(f"Value transform failed ({field_type}, {multiplier}, {offset}): {e}")
        return value

class ConstLabelWidget(BaseWidget):
    """Simple text/label widget."""

    def init_ui(self):
        self.label = QLabel(self.cfg.get("text"))
        self.layout.addWidget(self.label)

    def update_data(self, data):
        if isinstance(data, str):
            self.label.setText(data)
        elif isinstance(data, dict) and "text" in data:
            self.label.setText(str(data["text"]))


class BoundLabel(QLabel):
    """
    A label that updates from one or more communicator topics.

    Supports:
      - Nested fields: e.g. "timestamp.usec"
      - Indexed fields: e.g. "accelerometer_integral[0]"
      - Mixed paths: e.g. "data.vector[2].x"

    YAML forms:
      topic: dronecan.uavcan.protocol.NodeStatus
      field: uptime_sec
      default: "N/A"          # optional
      ---
      topics: [dronecan.uavcan.protocol.NodeStatus, uavcan.node.Heartbeat]
      fields: [uptime_sec, uptime]
      node_id: 42
      default: "-"
    """

    def __init__(self, cfg):
        default_text = cfg.get("default", cfg.get("text", "-"))
        super().__init__(str(default_text))

        communicator = cfg.get("communicator")
        if not communicator:
            return

        self.default_text = str(default_text)
        self.communicator = communicator
        node_id = cfg.get("node_id", None)
        topics = cfg.get("topics")
        fields = cfg.get("fields")
        info = cfg.get("info")

        if info and node_id is not None:
            communicator.subscribe_get_info(node_id, info, self.setText)
            return

        if topics and fields:
            self.topic_field_pairs = list(zip(topics, fields))
        else:
            topic = cfg.get("topic")
            field = cfg.get("field")
            self.topic_field_pairs = [(topic, field)] if topic and field else []

        for topic, field in self.topic_field_pairs:
            communicator.subscribe(
                topic,
                lambda t, msg, f=field: self._on_msg(msg, f),
                node_id
            )

    def _on_msg(self, msg, field):
        value = resolve_field_path(msg, field)
        if value is None:
            # keep showing previous value, or reset to default if you prefer:
            self.setText(self.default_text)
            return

        if isinstance(value, float):
            text = f"{value:.3g}"
        elif isinstance(value, (list, tuple)):
            text = ", ".join(f"{v:.3g}" if isinstance(v, float) else str(v) for v in value)
        else:
            text = str(value)

        self.setText(text)

class EnumStatusLabel(QLabel):
    """
    Color-coded enum label for CAN/DroneCAN/Cyphal fields.

    Supports single or multiple topic/field pairs.

    YAML examples:
      # Single source
      type: EnumStatusLabel
      topic: uavcan.node.Heartbeat
      field: health
      node_id: 10
      mapping:
        None: {text: "OFF",  color: "red"}
        0:    {text: "OK",   color: "green"}
        1:    {text: "WARN", color: "yellow"}
        2:    {text: "ERR",  color: "purple"}
        3:    {text: "CRIT", color: "red"}

      # Multi-source (DroneCAN + Cyphal)
      type: EnumStatusLabel
      topics: [dronecan.uavcan.protocol.NodeStatus, cyphal.uavcan.node.Heartbeat]
      fields: [health, health.value]
      node_id: 42
      mapping: { ...same as above... }
    """

    def __init__(self, cfg):
        super().__init__(cfg.get("text", "-"))
        self.communicator = cfg.get("communicator")
        if not self.communicator:
            return

        self.node_id = cfg.get("node_id")

        # Multi-topic/field support
        topics = cfg.get("topics")
        fields = cfg.get("fields")
        if topics and fields:
            self.topic_field_pairs = list(zip(topics, fields))
        else:
            topic = cfg.get("topic")
            field = cfg.get("field")
            self.topic_field_pairs = [(topic, field)] if topic and field else []

        # Normalize mapping keys
        raw_mapping = cfg.get("mapping", {})
        self.mapping = {}
        for k, v in raw_mapping.items():
            if k in (None, "None", "null", "NULL"):
                self.mapping[None] = v
            else:
                try:
                    self.mapping[int(k)] = v
                except (TypeError, ValueError):
                    self.mapping[k] = v

        self.offline_entry = self.mapping.get(None, {"text": "OFF", "color": "red"})

        # Initial style
        self._apply_style(self.offline_entry["text"], self.offline_entry["color"])

        # Subscribe to all topic/field pairs
        for topic, field in self.topic_field_pairs:
            self.communicator.subscribe(
                topic,
                lambda t, msg, f=field: self._on_msg(msg, f),
                self.node_id,
            )

    def _on_msg(self, msg, field):
        value = resolve_field_path(msg, field)
        entry = self.mapping.get(value, self.offline_entry)
        self._apply_style(entry["text"], entry["color"])

    def _apply_style(self, text: str, color: str):
        """Force color regardless of parent styles."""
        self.setText(text)
        self.setStyleSheet(f"color: {color} !important; font-weight: bold;")

class HealthLabel(EnumStatusLabel):
    """
    Specialized EnumStatusLabel for standard UAVCAN/Cyphal node health.

    YAML example:
      type: HealthLabel
      node_id: 42
    """

    def __init__(self, cfg):
        base_cfg = dict(cfg)

        base_cfg.setdefault("topics", [
            "dronecan.uavcan.protocol.NodeStatus",
            "cyphal.uavcan.node.Heartbeat"
        ])
        base_cfg.setdefault("fields", [
            "health",
            "health.value"
        ])
        base_cfg.setdefault("mapping", {
            None: {"text": "OFF",  "color": "red"},
            0:    {"text": "OK",   "color": "green"},
            1:    {"text": "WARN", "color": "yellow"},
            2:    {"text": "ERR",  "color": "purple"},
            3:    {"text": "CRIT", "color": "red"},
        })

        super().__init__(base_cfg)

class ParamWidget(BaseWidget):
    """
    Editable parameter widget that both fetches and allows updating a parameter.

    YAML example:
      type: ParamWidget
      param: "pwm1.min"
      node_id: 51
      editable: true
      refresh: 2.0   # optional: refresh interval in seconds
    """

    def init_ui(self):
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit

        cfg = self.cfg
        self.param = cfg.get("param")
        self.node_id = cfg.get("node_id")
        self.editable = bool(cfg.get("editable", True))
        self.communicator = cfg.get("communicator")

        # Layout
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)

        # Editable value field
        self.input = QLineEdit()
        self.input.setAlignment(Qt.AlignLeft)
        self.input.setFixedWidth(80)
        self.input.setEnabled(self.editable)
        h.addWidget(self.input)

        self.layout.addLayout(h)

        # State
        self._last_value = None
        self._user_editing = False

        # Signals for user edits
        self.input.editingFinished.connect(self._on_user_edit)
        self.input.returnPressed.connect(self._on_user_edit)

        if not self.communicator or not self.param or self.node_id is None:
            self.input.setText("N/A")
            return

        self.communicator.subscribe_param(self.node_id, self.param, self.input.setText)

    def _on_user_edit(self):
        """Handle manual edit by user."""
        text = self.input.text().strip()
        if not text or not self.communicator:
            return

        self._user_editing = False
        try:
            val = float(text) if "." in text else int(text)
        except ValueError:
            logger.warning(f"Invalid value for {self.param}: {text}")
            return

        read_value = str(self.communicator.set_param(self.node_id, self.param, val))
        self.input.setText(read_value)
        self._last_value = str(val)

    def focusInEvent(self, event):
        """Mark as user editing to prevent background refreshes."""
        self._user_editing = True
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Write value when leaving the field."""
        self._user_editing = False
        self._on_user_edit()
        super().focusOutEvent(event)


class ButtonWidget(BaseWidget):
    """
    A configurable button that performs different actions.

    YAML example:
      type: ButtonWidget
      text: "Save all parameters"
      action: noop | save_all | reboot | update_firmware
      node_id: 63
    """

    def init_ui(self):
        self.button = QPushButton(self.cfg.get("text", "Button"))
        self.layout.addWidget(self.button)

        self.action = self.cfg.get("action", "noop")
        self.node_id = self.cfg.get("node_id")
        self.communicator = self.cfg.get("communicator")

        self._blink_timer = None
        self._blink_on = False

        def execute_command_callback():
            self.communicator.execute_command(node_id=self.node_id, command=self.action)
        self.button.clicked.connect(execute_command_callback)

        if self.action == "save_all":
            self.communicator.register_action(self.node_id, self.action, self.start_hint)

    def start_hint(self, duration: float | None = None):
        """Start blinking the button to attract user's attention."""
        if self._blink_timer is not None:
            return

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start(500)
        logger.debug("Blinking started for button '%s'", self.button.text())

        if duration is not None and duration > 0:
            QTimer.singleShot(int(duration * 1000), self.stop_hint)

    def stop_hint(self):
        """Stop blinking and restore the button style."""
        if self._blink_timer:
            self._blink_timer.stop()
            self._blink_timer = None
        self.button.setStyleSheet("")
        self.button.style().unpolish(self.button)
        self.button.style().polish(self.button)
        self.button.update()
        self._blink_on = False
        logger.debug("Blinking stopped for button '%s'", self.button.text())

    def _toggle_blink(self):
        """Toggle between two visual styles."""
        self._blink_on = not self._blink_on
        if self._blink_on:
            self.button.setStyleSheet("background-color: #fff4b3; color: black; font-weight: bold;")
        else:
            self.button.setStyleSheet("")

        self.button.style().unpolish(self.button)
        self.button.style().polish(self.button)
        self.button.update()

class RowWidget(QWidget):
    """Dynamic table row with flexible columns based on header definition.

    Cells may be:
      - QWidget instances (used directly)
      - dict: a widget config (must include "type"; WidgetFactory.create will be used)
      - list: a sequence of widget configs or widgets (rendered horizontally inside the cell)
      - scalar: treated as text and wrapped by ConstLabelWidget

    The optional communicator is injected into nested widget configs when present.
    """

    def __init__(self, fields: list[str], values: dict | list, widths=None, bold=False, communicator=None):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        style_suffix = "font-weight: bold;" if bold else ""
        self.fields = fields
        self.widths = widths or []
        self.communicator = communicator

        # Normalize data
        if isinstance(values, dict):
            cell_values = [values.get(key, "") for key in fields]
        else:
            cell_values = [v for v in values]

        max_height = 0
        for i, (key, cell_value) in enumerate(zip(fields, cell_values)):
            widget = None

            # If the cell is already a QWidget, use it directly
            if isinstance(cell_value, QWidget):
                widget = cell_value

            # If the cell is a dict with 'widgets' key -> composite cell
            elif isinstance(cell_value, dict) and "widgets" in cell_value and isinstance(cell_value["widgets"], list):
                container = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(6)
                # create each inner widget
                for sub in cell_value["widgets"]:
                    sub_cfg = dict(sub) if isinstance(sub, dict) else sub
                    if isinstance(sub_cfg, dict) and self.communicator and "communicator" not in sub_cfg:
                        sub_cfg["communicator"] = self.communicator
                    sub_widget = sub_cfg if isinstance(sub_cfg, QWidget) else WidgetFactory.create(sub_cfg) if isinstance(sub_cfg, dict) else ConstLabelWidget({"text": str(sub_cfg)})
                    h.addWidget(sub_widget)
                    try:
                        hint = sub_widget.sizeHint().height()
                        if hint > max_height:
                            max_height = hint
                    except Exception:
                        pass
                container.setLayout(h)
                widget = container

            # If the cell is a list -> render each element inside a container
            elif isinstance(cell_value, list):
                container = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(6)
                for sub in cell_value:
                    if isinstance(sub, QWidget):
                        sub_widget = sub
                    elif isinstance(sub, dict):
                        sub_cfg = dict(sub)
                        if self.communicator and "communicator" not in sub_cfg:
                            sub_cfg["communicator"] = self.communicator
                        sub_widget = WidgetFactory.create(sub_cfg)
                    else:
                        sub_widget = ConstLabelWidget({"text": str(sub)})
                    h.addWidget(sub_widget)
                    try:
                        hint = sub_widget.sizeHint().height()
                        if hint > max_height:
                            max_height = hint
                    except Exception:
                        pass
                container.setLayout(h)
                widget = container

            # If the cell is a dict -> treat as a single widget config
            elif isinstance(cell_value, dict):
                cfg = dict(cell_value)
                if self.communicator and "communicator" not in cfg:
                    cfg["communicator"] = self.communicator
                widget = WidgetFactory.create(cfg)

            # fallback: treat as scalar text
            else:
                widget = ConstLabelWidget({"text": str(cell_value)})

            # Apply styling (best-effort; widgets may override)
            try:
                # Skip styling for color-aware widgets
                if isinstance(widget, (EnumStatusLabel, BoundLabel, BoundImage)):
                    pass
                else:
                    color = self._text_color(key, str(cell_value), bold)
                    widget.setStyleSheet(f"color: {color}; {style_suffix} padding: 0; margin: 0;")
            except Exception:
                pass

            # Apply width if requested
            if i < len(self.widths):
                try:
                    widget.setFixedWidth(self.widths[i])
                except Exception:
                    pass

            layout.addWidget(widget)
            # update max height from sizeHint
            try:
                hint = widget.sizeHint().height()
                # Clamp images to a reasonable max row height
                if isinstance(widget, QLabel) and widget.pixmap() is not None:
                    hint = min(hint, 32)  # e.g. max 32 px high
                if hint > max_height:
                    max_height = hint
            except Exception:
                pass

        self.setLayout(layout)
        # keep rows compact but large enough for contents
        if max_height > 0:
            self.setFixedHeight(max(20, max_height + 2))
        else:
            self.setFixedHeight(20)

    def _text_color(self, key: str, text: str, bold: bool) -> str:
        if bold:
            return "#ccc"
        s = str(text).lower()
        if key in ("status", "update"):
            if "ok" in s:
                return "#00ff88"
            elif "off" in s:
                return "#ff4444"
            elif "warn" in s:
                return "#ffaa00"
        return "white"


class TableWidget(BaseWidget):
    """Generic table widget using header dict for field mapping, with auto column width.

    Cells inside rows may be provided as widget configs (dict with 'type') or plain scalars.
    TableWidget will inject the parent/ panel communicator into nested widget configs when present.
    """

    def __init__(self, cfg: dict):
        # keep cfg/communicator for nested widgets in cells
        self.cfg = cfg
        self.communicator = cfg.get("communicator")
        self.header_dict = cfg.get("header", {})
        self.fields = list(self.header_dict.keys())
        self.header_labels = list(self.header_dict.values())
        self.rows = cfg.get("rows", [])

        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.init_ui()

    def compute_column_widths(self, font_metrics):
        """Compute max text width for each column.

        If a cell is a dict with a 'text' key, use that text. Otherwise fall back
        to string conversion. Also handle lists/composite cells by inspecting
        their first text-like element.
        """
        widths = [0] * len(self.fields)

        for i, label in enumerate(self.header_labels):
            widths[i] = max(widths[i], font_metrics.horizontalAdvance(str(label)))

        for row in self.rows:
            for i, key in enumerate(self.fields):
                val = row.get(key, "")
                text = ""
                # extract representative text if it's a widget config or composite
                if isinstance(val, dict):
                    if "text" in val:
                        text = val.get("text")
                    elif "widgets" in val and isinstance(val["widgets"], list) and val["widgets"]:
                        first = val["widgets"][0]
                        text = first.get("text", str(first)) if isinstance(first, dict) else str(first)
                    else:
                        text = val.get("label", val.get("name", ""))
                elif isinstance(val, list) and val:
                    first = val[0]
                    if isinstance(first, dict):
                        text = first.get("text", first.get("name", ""))
                    else:
                        text = str(first)
                else:
                    text = str(val)

                widths[i] = max(widths[i], font_metrics.horizontalAdvance(text))

        # small padding for cell margins
        return [w + 16 for w in widths]

    def init_ui(self):
        fm = QFontMetrics(self.font())
        col_widths = self.compute_column_widths(fm)

        if self.header_labels:
            header_row = RowWidget(self.fields, self.header_labels, widths=col_widths, bold=True, communicator=self.communicator)
            header_row.setStyleSheet("background-color: #222;")
            self.layout.addWidget(header_row)

        for row in self.rows:
            self.layout.addWidget(RowWidget(self.fields, row, widths=col_widths, communicator=self.communicator))

class BoundImage(QLabel):
    """
    A widget that displays one of two images depending on a field value
    from a subscribed topic.

    YAML example:
      type: BoundImage
      topics: [dronecan.uavcan.equipment.actuator.Status]
      fields: [power_rating_pct]
      node_id: 51
      threshold: 30
      image_low: "assets/low.png"
      image_high: "assets/high.png"
    """

    def __init__(self, cfg):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.communicator = cfg.get("communicator")
        if not self.communicator:
            return

        self.node_id = cfg.get("node_id")
        self.threshold = float(cfg.get("threshold", 30))
        self.image_low_path = cfg.get("image_low", "assets/low.png")
        self.image_high_path = cfg.get("image_high", "assets/high.png")

        # Load images
        self.image_low = QPixmap(self.image_low_path)
        self.image_high = QPixmap(self.image_high_path)

        if not self.image_low or self.image_low.isNull():
            logger.warning(f"Missing image_low: {self.image_low_path}")
        if not self.image_high or self.image_high.isNull():
            logger.warning(f"Missing image_high: {self.image_high_path}")

        # Initially show the "low" image
        self.current_image = self.image_low
        self.setPixmap(self._fit_pixmap(self.image_low))

        # Subscribe
        topics = cfg.get("topics")
        fields = cfg.get("fields")
        if topics and fields:
            self.topic_field_pairs = list(zip(topics, fields))
        else:
            topic = cfg.get("topic")
            field = cfg.get("field")
            self.topic_field_pairs = [(topic, field)] if topic and field else []

        for topic, field in self.topic_field_pairs:
            self.communicator.subscribe(
                topic,
                lambda t, msg, f=field: self._on_msg(msg, f),
                self.node_id,
            )

    def _fit_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Scale image only if it exceeds the widget's current size."""
        if not pixmap or pixmap.isNull():
            return QPixmap()

        target_w = self.width() or 100
        target_h = self.height() or 100
        img_w = pixmap.width()
        img_h = pixmap.height()

        # Only scale down if needed
        if img_w > target_w or img_h > target_h:
            return pixmap.scaled(
                target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        return pixmap

    def resizeEvent(self, event):
        """Ensure image fits new cell size on resize."""
        if self.current_image and not self.current_image.isNull():
            self.setPixmap(self._fit_pixmap(self.current_image))
        super().resizeEvent(event)

    def _on_msg(self, msg, field):
        """Update image based on topic value."""
        value = msg.get(field) if isinstance(msg, dict) else getattr(msg, field, None)
        if value is None:
            return

        try:
            val = float(value)
        except (ValueError, TypeError):
            return

        new_image = self.image_high if val >= self.threshold else self.image_low
        if new_image.cacheKey() != self.current_image.cacheKey():
            self.current_image = new_image
            self.setPixmap(self._fit_pixmap(self.current_image))

    def sizeHint(self):
        """Return scaled image size or a reasonable default."""
        if self.current_image and not self.current_image.isNull():
            img_size = self.current_image.size()
            # Clamp to current widget or parent size to avoid oversized rows
            w = min(img_size.width(), self.width() or 32)
            h = min(img_size.height(), self.height() or 32)
            return QSize(w, h)
        return QSize(24, 24)


class GpsWidget(BaseWidget):
    """Widget showing GPS coordinates on a folium map (loaded lazily)."""

    def init_ui(self):
        self.folium = lazy_import_module("GpsWidget", "folium")

        self.QWebEngineView = getattr(
            importlib.import_module("PySide6.QtWebEngineWidgets"), "QWebEngineView"
        )
        self.QWebEngineSettings = getattr(
            importlib.import_module("PySide6.QtWebEngineCore"), "QWebEngineSettings"
        )

        self.communicator = self.cfg.get("communicator")
        self.topic = self.cfg.get("topic")
        self.field_lat = self.cfg.get("field_lat", "lat")
        self.field_lon = self.cfg.get("field_lon", "lon")
        self.node_id = self.cfg.get("node_id")

        self.view = self.QWebEngineView()
        self.view.settings().setAttribute(self.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        self.view.settings().setAttribute(self.QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.layout.addWidget(self.view)

        self.initial_lat = 0
        self.initial_lon = 0
        self._map_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html").name

        self._update_map(self.initial_lat, self.initial_lon)

        if self.communicator and self.topic:
            self.communicator.subscribe(self.topic, self._on_msg, self.node_id)

    def _update_map(self, lat, lon):
        """Render a small Folium map centered at (lat, lon)."""
        folium = self.folium
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker(
            [lat, lon],
            tooltip=f"{lat:.6f}, {lon:.6f}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)
        m.save(self._map_file)
        self.view.setUrl(f"file://{self._map_file}")

    def _on_msg(self, topic, msg):
        lat = getattr(msg, self.field_lat, None) if not isinstance(msg, dict) else msg.get(self.field_lat)
        lon = getattr(msg, self.field_lon, None) if not isinstance(msg, dict) else msg.get(self.field_lon)
        if lat is None or lon is None:
            return
        self._update_map(lat, lon)

class PlotWidget(BaseWidget):
    """Real-time plotting widget that subscribes to topic fields and draws live data."""

    def init_ui(self):
        self.pg = lazy_import_module("PlotWidget", "pyqtgraph")
        self.communicator = self.cfg.get("communicator")
        self.topics = self.cfg.get("topics") or [self.cfg.get("topic")]
        self.fields = self.cfg.get("fields") or [self.cfg.get("field")]
        self.names = self.cfg.get("names", self.fields)
        self.node_id = self.cfg.get("node_id")
        self.window = int(self.cfg.get("window", 200))
        self.refresh_rate = float(self.cfg.get("refresh_rate", 20))
        self.title = self.cfg.get("title", None)
        self.xlabel = self.cfg.get("xlabel", "Samples")
        self.ylabel = self.cfg.get("ylabel", "Value")

        # Prepare data storage
        self.data = {f: deque(maxlen=self.window) for f in self.fields}
        self.xdata = deque(maxlen=self.window)
        self.counter = 0

        # Setup pyqtgraph widget
        self.plot_widget = self.pg.PlotWidget()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        if self.title:
            self.plot_widget.setTitle(self.title)
        self.plot_widget.setLabel("bottom", self.xlabel)
        self.plot_widget.setLabel("left", self.ylabel)
        self.plot_widget.addLegend(offset=(10, 10))

        # Create curves
        self.curves = {}
        colors = ["y", "c", "m", "g", "r", "b"]

        for i, (f, name) in enumerate(zip(self.fields, self.names)):
            pen = self.pg.mkPen(colors[i % len(colors)], width=2)
            self.curves[f] = self.plot_widget.plot([], [], pen=pen, name=name)

        self.layout.addWidget(self.plot_widget)

        # Subscribe to topics
        if self.communicator and self.topics:
            for topic in self.topics:
                self.communicator.subscribe(topic, lambda t, msg: self._on_msg(msg), self.node_id)

        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_plot)
        self.timer.start(int(1000 / self.refresh_rate))

    def _on_msg(self, msg):
        """Handle incoming messages and store values."""
        from re import split as resplit

        self.counter += 1
        self.xdata.append(self.counter)

        for f in self.fields:
            val = resolve_field_path(msg, f)
            if isinstance(val, (int, float)):
                self.data[f].append(val)
            else:
                self.data[f].append(float("nan"))

    def _update_plot(self):
        """Redraw curves with latest samples."""
        for f, curve in self.curves.items():
            y = list(self.data[f])
            if not y:
                continue
            x = list(self.xdata)[-len(y):]
            curve.setData(x, y)

class SliderWidget(BaseWidget):
    """Slider widget bound to a communicator topic/field.

    Config keys:
      - topic: topic name to listen/push to
      - field: field name inside messages
      - min, max, step, initial: integer slider range
      - unit: optional unit string displayed after value
      - text: optional label text
      - field_type: optional (int, float, bool)
      - multiplier: optional numeric multiplier
      - offset: optional numeric offset
    """

    def init_ui(self):
        cfg = self.cfg
        self.topic = cfg.get("topic")
        self.field = cfg.get("field")
        self.unit = cfg.get("unit", "")
        self.min = int(cfg.get("min", 0))
        self.max = int(cfg.get("max", 100))
        self.step = int(cfg.get("step", 1))
        self.value = int(cfg.get("initial", self.min))
        self.field_type = cfg.get("field_type")
        self.multiplier = cfg.get("multiplier")
        self.offset = cfg.get("offset")

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        self.label = QLabel()
        fm = QFontMetrics(self.label.font())
        widest_text = f"{self.max}{self.unit}"
        label_width = fm.horizontalAdvance(widest_text) + 10
        self.label.setFixedWidth(label_width)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label.setText(f"{self.value}{self.unit}")
        h.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.min, self.max)
        self.slider.setSingleStep(self.step)
        self.slider.setValue(self.value)
        self.slider.valueChanged.connect(self._on_value_changed)
        h.addWidget(self.slider, 1)

        self.layout.addLayout(h)

        self.communicator = cfg.get("communicator")
        if self.communicator and self.topic:
            try:
                self.communicator.advertise(self.topic, self.field)
            except Exception as err:
                logger.critical(err)

    def _on_value_changed(self, value):
        if not self.communicator or not self.topic:
            self.label.setText("Err")
            return

        self.label.setText(f"{value}{self.unit}")

        value = self._apply_value_transforms(
            value,
            field_type=self.field_type,
            multiplier=self.multiplier,
            offset=self.offset,
        )

        self.communicator.set_publisher_field(topic=self.topic, field=self.field, value=value)

class PublisherWidget(BaseWidget):
    """
    Editable field that periodically publishes a value to a topic/field.

    Config keys:
      - topic, field, node_id, text, unit, frequency, initial (as before)
      - field_type: optional (int, float, bool)
      - multiplier: optional numeric multiplier
      - offset: optional numeric offset
    """

    def init_ui(self):
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit

        cfg = self.cfg
        self.topic = cfg.get("topic")
        self.field = cfg.get("field")
        self.node_id = cfg.get("node_id")
        self.text_label = cfg.get("text", "")
        self.unit = cfg.get("unit", "")
        self.frequency = float(cfg.get("frequency", 10.0))
        self.value = float(cfg.get("initial", 0))
        self.field_type = cfg.get("field_type")
        self.multiplier = cfg.get("multiplier")
        self.offset = cfg.get("offset")
        self.communicator = cfg.get("communicator")

        # Layout setup
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)

        if self.text_label:
            label = QLabel(self.text_label)
            h.addWidget(label)

        self.input = QLineEdit(str(self.value))
        self.input.setFixedWidth(80)
        self.input.setAlignment(Qt.AlignLeft)
        h.addWidget(self.input)

        if self.unit:
            unit_label = QLabel(self.unit)
            unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            h.addWidget(unit_label)

        self.layout.addLayout(h)

        if not self.communicator or not self.topic or not self.field:
            logger.warning("PublisherWidget: communicator/topic/field not set.")
            return

        try:
            self.communicator.advertise(self.topic, self.field, frequency=self.frequency)
        except Exception as err:
            logger.critical(f"Failed to advertise publisher {self.topic}.{self.field}: {err}")
            return

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._publish_current_value)
        self.timer.start(int(1000 / self.frequency))

        self.input.editingFinished.connect(self._on_user_edit)
        self.input.returnPressed.connect(self._on_user_edit)

    def _on_user_edit(self):
        """Update current value when user edits the field."""
        text = self.input.text().strip()
        if not text:
            return
        try:
            self.value = float(text)
        except ValueError:
            logger.warning(f"Invalid input for {self.topic}.{self.field}: '{text}'")
            return
        self._publish_current_value()

    def _publish_current_value(self):
        """Send the current value through communicator."""
        if not self.communicator or not self.topic or not self.field:
            return

        value = self._apply_value_transforms(
            self.value,
            field_type=self.field_type,
            multiplier=self.multiplier,
            offset=self.offset,
        )

        try:
            self.communicator.set_publisher_field(self.topic, self.field, value)
        except Exception as e:
            logger.error(f"Failed to publish {self.topic}.{self.field}: {e}")

class CanGraphWidget(BaseWidget):
    """Visualizes CAN topology (nodes, hubs, connections) as a graph."""

    def init_ui(self):
        self.pg = lazy_import_module("CanGraphWidget", "pyqtgraph")
        self.communicator = self.cfg.get("communicator")
        self.topology = self.cfg.get("topology", {})
        self.refresh_rate = float(self.cfg.get("refresh_rate", 2))

        # Prepare graph view
        self.graph_widget = self.pg.GraphItem()
        self.plot = self.pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
        self.plot.addItem(self.graph_widget)
        self.layout.addWidget(self.plot)

        # Periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_graph)
        self.timer.start(int(1000 / self.refresh_rate))

        self.text_items = []

        self._update_graph()

    def _update_graph(self):
        """Draw or refresh graph based on topology."""
        elements = self.topology.get("elements", [])
        connections = self.topology.get("connections", [])

        # Build node map
        ids = [str(e["id"]) for e in elements]
        names = [e.get("name", str(e["id"])) for e in elements]
        colors = []
        for e in elements:
            if e.get("type") in ("mixer", "hub", "repeater"):
                colors.append((150, 150, 255, 255))  # bluish
            else:
                colors.append((150, 255, 150, 255))  # greenish

        n = len(ids)
        pos = {i: (i % 5, i // 5) for i in range(n)}  # simple grid layout
        adj = []
        for c in connections:
            if len(c) == 2 and str(c[0]) in ids and str(c[1]) in ids:
                i1, i2 = ids.index(str(c[0])), ids.index(str(c[1]))
                adj.append((i1, i2))

        # Convert to arrays
        import numpy as np
        pos_array = np.array([pos[i] for i in range(n)])
        adj_array = np.array(adj)
        symbols = ["o" if "node" in elements[i]["type"] else "s" for i in range(n)]
        brushes = [self.pg.mkBrush(*c) for c in colors]

        self.graph_widget.setData(
            pos=pos_array,
            adj=adj_array,
            symbol=symbols,
            size=20,
            pxMode=True,
            brush=brushes,
            pen="w",
            texts=names,
            textPen="w"
        )

        # Clear old labels
        for t in self.text_items:
            self.plot.removeItem(t)
        self.text_items.clear()

        # Add text labels near each node
        for (x, y), name in zip(pos_array, names):
            label = self.pg.TextItem(text=name, color=(230, 230, 230), anchor=(0.5, -0.3))
            label.setPos(x, y)
            self.plot.addItem(label)
            self.text_items.append(label)

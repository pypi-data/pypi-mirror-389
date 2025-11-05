#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
DroneCAN node
"""

# Pylint notes:
# - dronecan exposes members dynamically (generated DSDL), which confuses static analysis.
# pylint: disable=no-member


import os
import re
import sys
import time
import logging
import argparse
import importlib
from typing import Callable, Any

from tsugite.backend.backend import BaseBackend, BackendInitializationError
from tsugite.backend.registry import NodesRegistry, Publisher, NodeId, ParamValue
from tsugite.utils import make_field_setter

logger = logging.getLogger("dronecan_backend")

try:
    import serial
except ModuleNotFoundError:
    logger.critical("DroneCAN required: pip install pyserial")
    sys.exit(1)

try:
    import warnings
    # Silence DroneCAN’s internal deprecation warning
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
    import dronecan
except ModuleNotFoundError:
    logger.critical("DroneCAN required: pip install pydronecan setuptools==80.9.0")
    sys.exit(1)


BLINK_DURATION = 15
WRITE_ATTEMPTS = 3


class DronecanBackend(BaseBackend):
    def __init__(self, iface: str = "slcan:/dev/ttyACM0", node_id: NodeId = 100) -> None:
        try:
            self.node = dronecan.make_node(
                iface, node_id=node_id, bitrate=1_000_000, baudrate=1_000_000
            )
        except serial.SerialException as e:
            raise BackendInitializationError(f"Failed to open interface {iface}: {e}") from e

        self.pubs = {}
        self._param_value: ParamValue = None
        self.registry = NodesRegistry()
        self.node.add_handler(dronecan.uavcan.protocol.NodeStatus, self._node_status_callback)

    #
    # Topics API: subscribe and publish
    #
    def subscribe(self, topic: str, callback: Callable[[str, Any], None], node_id: NodeId = None) -> None:
        if not isinstance(topic, str):
            raise ValueError("Topic must be a str")

        data_type = DronecanBackend._topic_to_data_type(topic)
        if not data_type:
            return

        def _handler(msg) -> None:
            if node_id is None or msg.transfer.source_node_id == node_id:
                callback(data_type, msg.message)

        self.node.add_handler(data_type, _handler)

    def advertise(self, topic: str, field: str, frequency: float = 1.0) -> None:
        data_type = DronecanBackend._topic_to_data_type(topic)
        if not data_type:
            return

        if not isinstance(field, str):
            raise ValueError("Field must be a string")

        if topic not in self.pubs:
            self.pubs[topic] = Publisher(msg=data_type(), frequency=frequency)
            logger.info("Add publisher: %s", topic)

            # Apply hacks for some topics
            if topic == "dronecan.uavcan.equipment.esc.RawCommand":
                self.pubs[topic].msg.cmd = [int(0)] * 8
            elif topic == "dronecan.uavcan.equipment.actuator.ArrayCommand":
                for _ in range(4):
                    self.pubs[topic].msg.commands.append(self.pubs[topic].msg.commands.new_item())
        else:
            self.pubs[topic] = self.pubs[topic]

        self.pubs[topic].fields[field] = make_field_setter(self.pubs[topic].msg, field)
        logger.info("Add publisher field setter: %s.%s", topic, field)

    def set_publisher_field(self, topic: str, field: str, value: Any) -> None:
        if topic not in self.pubs:
            logger.warning("Topic '%s' not registered for periodic publishing", topic)
            return

        if field not in self.pubs[topic].fields:
            logger.warning("Field '%s' not registered for topic '%s'", field, topic)
            return

        self.pubs[topic].fields[field](value)

    #
    # Parameters API: read and write
    #
    def subscribe_param(self, node_id: int, param_name: str, setText: Callable) -> None:
        param = self.registry.ensure_param(node_id, param_name)
        param.setters.append(setText)

    def set_param(self, node_id: NodeId, param_name: str, value: Any) -> ParamValue:
        def getset_write_callback(msg: dronecan.node.TransferEvent):
            if not isinstance(msg, dronecan.node.TransferEvent):
                logger.warning("Write param: msg %s is not TransferEvent", msg)
                return
            self._param_value = DronecanBackend._decode_uavcan_protocol_param_value(msg.response.value)

        req = dronecan.uavcan.protocol.param.GetSet.Request()
        req.name = param_name

        if isinstance(value, int):
            req.value.integer_value = value
        elif isinstance(value, str):
            req.value.string_value = value

        self._param_value = None
        for _ in range(WRITE_ATTEMPTS):
            self.node.request(req, node_id, getset_write_callback)
            self.tick(0.01)
            if self._param_value:
                break

        if self._param_value is not None:
            node = self.registry.ensure_node(node_id)
            if node.save_required_callback:
                node.save_required_callback(BLINK_DURATION)

        logger.info("Write param: node %s %s=%s", node_id, param_name, value)
        return self._param_value

    #
    # GetInfo API: subscribe
    #
    def subscribe_get_info(self, node_id: int, field: str, callback: Callable[[str, Any], None]) -> None:
        node = self.registry.ensure_node(node_id)
        field_entry = node.info["fields"].setdefault(field, {"value": None, "setters": []})
        field_entry["setters"].append(callback)

    #
    # Commands API
    #
    def execute_command(self, node_id: int, command: str) -> None:
        commands = {
            "reboot":   self._execute_reboot,
            "save_all": self._execute_save_all,
            "upgrade":  self._execute_upgrade,
        }

        if command not in commands:
            logger.warning("Execute command: %s not supported.", command)
            return

        commands[command](node_id)

    def register_action(self, node_id: int, action, callback):
        if action == "save_all":
            node = self.registry.ensure_node(node_id)
            node.save_required_callback = callback

    def tick(self, dt: float) -> None:
        try:
            self.node.spin(0.01)
        except KeyboardInterrupt:
            logger.info("Terminated by user.")
            sys.exit(0)
        except NotImplementedError:
            logger.critical("NotImplementedError. Check python-can == 4.3 is installed.")
            sys.exit(1)
        except dronecan.transport.TransferError:
            pass
        except dronecan.driver.common.DriverError:
            logger.critical("dronecan.driver.common.DriverError")
            sys.exit(1)
        except ValueError as e:
            logger.error("ValueError: %s", e)
        except dronecan.driver.common.TxQueueFullError as e:
            logger.error("TxQueueFullError: %s", e)
        except serial.serialutil.SerialException as e:
            logger.critical("SerialException: %s", e)
            sys.exit(1)

        # periodic publishers
        for _, pub in self.pubs.items():
            current_time = time.time()
            if current_time - pub.timestamp >= 1 / pub.frequency:
                try:
                    # print(pub.msg)
                    self.node.broadcast(pub.msg)
                except dronecan.driver.common.TxQueueFullError as e:
                    logger.critical("TxQueueFullError: %s", e)
                    sys.exit(1)
                pub.timestamp = current_time

        # handle params and info refresh
        crnt_time = time.time()
        requests_per_this_cycle_left = 1
        for node_id, node in self.registry:
            info = node.info
            if info and not info.get("fetched", False):
                recently_requested = info.get("request_time", 0) + 2.0 >= crnt_time
                if not recently_requested and NodesRegistry.is_online(node):
                    self._request_get_info(node_id)
                    requests_per_this_cycle_left -= 1
                    if requests_per_this_cycle_left <= 0:
                        break

            for param_name, param in node.params.items():
                if not NodesRegistry.is_online(node):
                    param.request_attempts_left = 5
                    continue
                if param.getset_response_time > node.boot_time:
                    param.request_attempts_left = 5
                    continue
                if param.getset_request_time + 1.0 >= crnt_time:
                    param.request_attempts_left = 5
                    continue
                if not param.request_attempts_left:
                    continue

                param.getset_request_time = crnt_time
                param.request_attempts_left -= 1
                self._request_param(node_id, param_name)
                requests_per_this_cycle_left -= 1
                if requests_per_this_cycle_left <= 0:
                    break

    @staticmethod
    def _decode_uavcan_protocol_param_value(value: dronecan.transport.CompoundValue) -> ParamValue:
        if value is None:
            return None
        if hasattr(value, "boolean_value"):
            return bool(value.boolean_value)
        if hasattr(value, "integer_value"):
            return int(value.integer_value)
        if hasattr(value, "real_value"):
            return float(value.real_value)
        if hasattr(value, "string_value"):
            string = value.string_value
            return str(string) if len(string) > 0 and string[0] != 255 else ""
        return None

    @staticmethod
    def _topic_to_data_type(topic: str):
        if not isinstance(topic, str):
            raise ValueError("Topic must be a string")

        if not topic.startswith("dronecan."):
            logger.debug("Skipping '%s' (not DroneCAN topic)", topic)
            return None

        try:
            parts = topic.split(".")
            module = importlib.import_module(parts[0])
            data_type = module
            for p in parts[1:]:
                data_type = getattr(data_type, p)
        except (ModuleNotFoundError, AttributeError) as e:
            logger.error("Failed to resolve topic '%s': %s", topic, e)
            return None

        return data_type

    def _execute_reboot(self, node_id: int):
        def _callback(msg: dronecan.uavcan.protocol.RestartNode.Response):
            if msg is None:
                return
        req = dronecan.uavcan.protocol.RestartNode.Request()
        req.magic_number = 0xACCE551B1E
        self.node.request(req, node_id, _callback)
        self.tick(0.01)
        logger.info("Execute action: reboot node %d.", node_id)

    def _execute_save_all(self, node_id: int):
        def _callback(msg: dronecan.uavcan.protocol.param.ExecuteOpcode.Response):
            if msg is None:
                return

        req = dronecan.uavcan.protocol.param.ExecuteOpcode.Request()
        req.opcode = 0    # Save all parameters to non-volatile storage
        req.argument = 0  # Reserved, keep zero
        self.node.request(req, node_id, _callback)
        self.tick(0.01)
        logger.info("Execute action: save_all node %d.", node_id)

    def _execute_upgrade(self, node_id: int):
        logger.warning("Action 'upgrade' is not supported yet.")

    def _request_get_info(self, node_id: int):
        req = dronecan.uavcan.protocol.GetNodeInfo.Request()
        self.node.request(req, node_id, self._get_info_callback)
        self.registry.ensure_node(node_id).info["request_time"] = time.time()
        self.tick(0.01)

    def _request_param(self, node_id: int, param_name: str) -> None:
        if not isinstance(node_id, int):
            raise ValueError(f"node_id {node_id} is not int")
        if not isinstance(param_name, str):
            raise ValueError(f"param_name {param_name} is not str")

        registry = self.registry

        def getset_read_callback(msg: dronecan.node.TransferEvent):
            if not isinstance(msg, dronecan.node.TransferEvent):
                # It happens sometime
                logger.warning("Read param: msg %s is not TransferEvent", msg)
                return

            node_id = msg.transfer.source_node_id

            node = registry.get_node(node_id)
            if not node:
                logger.critical("Read param: not node")
                return

            response_name = msg.response.name.decode("utf-8").rstrip("\x00")
            if len(response_name) == 0:
                logger.warning("Read param: node %s doesn't have %s", node_id, param_name)
                # Unfortunatelly, the response doesn't say which exactly parameter doesn't exist!
                # Better to make responses with the name and empty value in such cases!
                # But let's try this hack:
                node.params[param_name].not_exist = True
                node.params[param_name].getset_response_time = time.time()
                for setText in node.params[param_name].setters:
                    setText("N/A")
                return

            if response_name not in node.params:
                # It happens sometime
                logger.critical("Read param: response_name not in node.params")
                return

            param = node.params[response_name]
            param.getset_response_time = time.time()
            param.value = DronecanBackend._decode_uavcan_protocol_param_value(msg.response.value)
            param.default_value = DronecanBackend._decode_uavcan_protocol_param_value(msg.response.default_value)
            param.max_value = DronecanBackend._decode_uavcan_protocol_param_value(msg.response.max_value)
            param.min_value = DronecanBackend._decode_uavcan_protocol_param_value(msg.response.min_value)

            for setText in param.setters:
                setText(str(param.value))

        req = dronecan.uavcan.protocol.param.GetSet.Request()
        req.name = param_name
        self.node.request(req, node_id, getset_read_callback)

    def _node_status_callback(self, msg: dronecan.node.TransferEvent):
        node = self.registry.ensure_node(msg.transfer.source_node_id)
        node.nodestatus_time = time.time()
        node.uptime = msg.message.uptime_sec
        node.boot_time = max(node.boot_time, node.nodestatus_time - msg.message.uptime_sec)

    def _get_info_callback(self, transfer: dronecan.node.TransferEvent):
        if transfer is None:
            return

        node_id = transfer.transfer.source_node_id

        fetched_info = {}
        fetched_info["name"] = transfer.response.name.decode("utf-8").rstrip("\x00")
        fetched_info["node_id"] = node_id

        sw_major = transfer.response.software_version.major
        sw_minor = transfer.response.software_version.minor
        vcs_commit = hex(transfer.response.software_version.vcs_commit)[2:]
        fetched_info["software_version"] = f"v{sw_major}.{sw_minor}-{vcs_commit}"

        hw_major = transfer.response.hardware_version.major
        hw_minor = transfer.response.hardware_version.minor
        fetched_info["hardware_version"] = f"v{hw_major}.{hw_minor}"

        unique_id = bytes(transfer.response.hardware_version.unique_id)
        fetched_info["unique_id"] = "".join(f"{b:02X}" for b in unique_id)

        info = self.registry.ensure_node(node_id).info
        info["fetched"] = True
        for key, value in fetched_info.items():
            entry = info["fields"].setdefault(key, {"value": None, "setters": []})
            entry["value"] = value
            for setText in entry["setters"]:
                setText(str(value))

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    default_iface = "slcan:COM3@1000000" if os.name == "nt" else "slcan:/dev/ttyACM0"
    parser.add_argument("-i", "--iface", type=str, default=default_iface,
                        help="CAN interface, e.g. 'socketcan:can0' or 'slcan:/dev/ttyACM0@1000000'")
    parser.add_argument("-n", "--node-id", type=int, default=100,
                        help="DroneCAN node ID (default: 100)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    backend = DronecanBackend(iface=args.iface, node_id=args.node_id)
    backend.subscribe("dronecan.uavcan.protocol.NodeStatus",
                      lambda topic, msg: logger.info("NodeStatus: %s: %s", topic, msg))
    while True:
        backend.tick(0.01)


if __name__ == "__main__":
    main()

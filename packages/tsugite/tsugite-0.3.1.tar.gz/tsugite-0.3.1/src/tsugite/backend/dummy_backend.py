#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
from typing import Any, Callable, Union

from tsugite.backend.backend import BaseBackend
from tsugite.backend.registry import NodeId, ParamValue

class DummyBackend(BaseBackend):
    """Framework-independent communicator mock.
    Call `tick(dt)` periodically (e.g. every 0.01 s at 100 Hz).
    Internally emits Heartbeat messages once per second.
    """

    def __init__(self):
        self._subscribers = {}

        self._heartbeat_counter = 0
        self._last_heartbeat = time.time()

    #
    # Topic api: subscribe and publish
    #
    def subscribe(self, topic: str, callback: Callable[[str, Any], None], node_id=None):
        self._subscribers.setdefault(topic, []).append(callback)
    def advertise(self, topic: str, field: str, frequency: float = 10.0) -> None:
        super().advertise(topic, field, frequency)
    def set_publisher_field(self, topic: str, field: str, value) -> None:
        super().set_publisher_field(topic, field, value)

    #
    # Parameters API: read and write
    #
    def subscribe_param(self, node_id: int, param_name: str, setText: Callable) -> None:
        super().subscribe_param(node_id, param_name, setText)
    def set_param(self, node_id: NodeId, param_name: str, value: Any) -> ParamValue:
        return super().set_param(node_id, param_name, value)

    #
    # GetInfo API: subscribe
    #
    def subscribe_get_info(self, node_id: int, field: str, callback: Callable) -> None:
        """Bound get info"""
        super().subscribe_get_info(node_id, field, callback)

    #
    # Commands API
    #
    def execute_command(self, node_id: int, command: str) -> None:
        """Execute command"""
        super().execute_command(node_id, command)

    def register_action(self, node_id: int, action, callback) -> None:
        """Execute action"""

    def tick(self, dt: float):
        """Called periodically (e.g., 100 Hz)."""
        recv_msgs = {}

        # Emit Heartbeat every second
        now = time.time()
        if now - self._last_heartbeat >= 1.0:
            self._heartbeat_counter += 1
            self._last_heartbeat = now
            recv_msgs["Heartbeat"] = {"uptime_sec": self._heartbeat_counter}

        for recv_msg in recv_msgs:
            for cb in self._subscribers.get(recv_msg, []):
                cb(recv_msg, recv_msgs[recv_msg])

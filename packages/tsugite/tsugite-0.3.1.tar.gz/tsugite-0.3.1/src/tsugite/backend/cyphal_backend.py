#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Cyphal backend
"""

import sys
import time
import asyncio
import logging
import threading
from typing import Callable, Any

from tsugite.backend.backend import BaseBackend, BackendInitializationError
from tsugite.backend.registry import NodeId, ParamValue

logger = logging.getLogger("cyphal_backend")

try:
    import pycyphal
    import pycyphal.application
    import uavcan.node
    import uavcan.node.Heartbeat_1_0
except ModuleNotFoundError:
    logger.critical("Cyphal backend requires 'pycyphal' package: pip install pycyphal")
    sys.exit(1)

class CyphalBackend(BaseBackend):
    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        self.node = None
        time.sleep(5)

    def _run_event_loop(self):
        asyncio.run(self._main())

    async def _main(self):
        node_info = uavcan.node.GetInfo_1_0.Response(
            uavcan.node.Version_1_0(major=1, minor=0),
            name="io.github.ponomarevda.tsugite"
        )
        self.node = pycyphal.application.make_node(node_info)
        self.node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self.node.start()

        def on_heartbeat(msg: uavcan.node.Heartbeat_1_0, transfer: pycyphal.transport.TransferFrom) -> None:
            print(f"Heartbeat from {transfer.source_node_id}: uptime={msg.uptime}")

        sub = self.node.make_subscriber(uavcan.node.Heartbeat_1_0)
        sub.receive_in_background(on_heartbeat)
        while self._running:
            await asyncio.sleep(1.0)
            print("Hello")

    def shutdown(self):
        self._running = False

    #
    # Topic api: subscribe and publish
    #
    def subscribe(self, topic: str, callback: Callable[[str, Any], None], node_id=None):
        print(f"Add cyphal sub {topic} {node_id}")
        def cb(msg: Any, transfer: pycyphal.transport.TransferFrom) -> None:
            print(f"Recv from {transfer.source_node_id}: uptime={msg.uptime}")
            callback(topic, msg)
        sub = self.node.make_subscriber(uavcan.node.Heartbeat_1_0)
        sub.receive_in_background(cb)
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
        super().subscribe_get_info(node_id, field, callback)

    #
    # Commands API
    #
    def execute_command(self, node_id: int, command: str) -> None:
        super().execute_command(node_id, command)

    def register_action(self, node_id: int, action, callback) -> None:
        pass

    def tick(self, dt: float):
        pass

if __name__ == "__main__":
    a = CyphalBackend()
    for _ in range(10):
        time.sleep(10)

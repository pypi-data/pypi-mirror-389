#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
from typing import Dict, List, Callable, Optional, Union, Any
from dataclasses import dataclass, field

NodeId = Optional[int]
ParamValue = Optional[Union[bool, int, float, str]]

@dataclass
class Param:
    value: ParamValue = None
    default_value: ParamValue = None
    min_value: ParamValue = None
    max_value: ParamValue = None
    setters: List[Callable] = field(default_factory=list)
    getset_response_time: float = 0.0
    getset_request_time: float = 0.0
    request_attempts_left: int = 5
    not_exist: Optional[bool] = None


@dataclass
class Node:
    nodestatus_time: float = 0.0
    uptime: float = 0.0
    boot_time: float = 0.0
    params: Dict[str, Param] = field(default_factory=dict)
    info: Dict[str, dict] = field(default_factory=lambda: {
        "fields": {},
        "fetched": False,
        "request_time": 0
    })
    save_required_callback: Optional[Callable] = None


@dataclass
class Publisher:
    msg: Any
    frequency: float
    timestamp: float = time.time()
    fields: dict = field(default_factory=dict)


class NodesRegistry:
    def __init__(self):
        self._nodes: Dict[int, Node] = {}

    def get_node(self, node_id: int) -> Optional[Node]:
        if node_id not in self._nodes:
            return None
        return self._nodes[node_id]

    def ensure_node(self, node_id: int) -> Node:
        if node_id not in self._nodes:
            self._nodes[node_id] = Node()
        return self._nodes[node_id]

    def ensure_param(self, node_id: int, param_name: str) -> Param:
        node = self.ensure_node(node_id)
        if param_name not in node.params:
            node.params[param_name] = Param()
        return node.params[param_name]

    @staticmethod
    def is_online(node: Node) -> bool:
        return node.nodestatus_time + 2.0 >= time.time()

    def __iter__(self):
        return iter(self._nodes.items())

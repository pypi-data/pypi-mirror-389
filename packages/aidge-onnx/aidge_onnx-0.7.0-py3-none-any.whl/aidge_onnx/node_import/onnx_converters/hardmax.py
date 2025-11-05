"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional
import numpy as np

import aidge_core
import onnx

from aidge_onnx.utils import get_node_attributes
from aidge_onnx.node_import import auto_register_import

@auto_register_import("hardmax")
def import_hardmax(onnx_node:onnx.NodeProto, input_nodes:List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)

    axis = None
    if 'axis' in onnx_attrs:
        axis = onnx_attrs['axis']
        del onnx_attrs['axis']
    else:
        aidge_core.Log.warn("Couldn't find attribute axis for operator hardmax.")
        return None

    if len(onnx_attrs) > 0:
        aidge_core.Log.warn(f"Unsupported attribute(s): {onnx_attrs.keys()} for operator hardmax.")
        return None

    hardmax_node = aidge_core.Hardmax(axis, name=node_name)
    aidge_core.Log.notice(f"- {node_name} ({onnx_node.op_type})")
    return hardmax_node

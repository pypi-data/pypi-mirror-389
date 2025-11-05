"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional

import aidge_core
import onnx
from onnx import NodeProto
from aidge_core import Log
from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

@auto_register_import("topk")
def import_topk(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    topk_attrs: dict = {"axis": -1, "largest": True, "sorted": True}

    if 'axis' in onnx_attrs:
        topk_attrs['axis'] = onnx_attrs['axis']
        del onnx_attrs['axis']

    if 'largest' in onnx_attrs:
        topk_attrs['largest'] = onnx_attrs['largest']
        del onnx_attrs['largest']

    if 'sorted' in onnx_attrs:
        topk_attrs['sorted'] = onnx_attrs['sorted']
        del onnx_attrs['sorted']

    if(len(onnx_attrs) > 0):
        Log.warn(f"Warning: Attribute {onnx_attrs.keys()} is not supported for operator topk.")
        return None

    My_op = aidge_core.TopKOp(**topk_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(My_op,name=node_name)

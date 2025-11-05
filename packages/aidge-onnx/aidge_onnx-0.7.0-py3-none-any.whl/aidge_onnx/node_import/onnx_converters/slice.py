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

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("slice")
def import_slice(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    slice_attrs: dict = {"name" : node_name}

    if opset < 10:
        for key in ('starts','ends','axes'):
            if key in onnx_attrs:
                slice_attrs[key] = onnx_attrs[key]
                del onnx_attrs[key]
    else: # in opsets >= 10, attributes are moved to inputs, axes and steps are optional
        for ite, (ele, optional) in enumerate((('starts', False), ('ends', False), ('axes', True), ('steps', True)), start=1):
            if ite >= len(input_nodes) and not optional:
                raise RuntimeError("Error: malformed ONNX: Slice: missing non optional input #{ide} named {ele}")
            if ite < len(input_nodes) and input_nodes[ite] is not None:
                slice_attrs[ele] = input_nodes[ite][0].get_operator().get_output(input_nodes[ite][1])

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Slice' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    slice_node = aidge_core.Slice(**slice_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return slice_node

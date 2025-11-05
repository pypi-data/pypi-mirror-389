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
from aidge_core import Log

@auto_register_import("clip")
def import_clip(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.output[0]
    attrs = {attr.name : attr for attr in onnx_node.attribute}
    onnx_attr_default: dict = {}
    if opset and opset < 6 and 'consumed_inputs' in attrs:
        del attrs['consumed_inputs']

    if(opset and opset < 11):
        if 'max' in attrs:
            onnx_attr_default['max'] = attrs['max']
            del attrs['max']
        if 'min' in attrs:
            onnx_attr_default['min'] = attrs['min']
            del attrs['min']
        valmin = onnx_attr_default['min'].f
        valmax = onnx_attr_default['max'].f
        clip = aidge_core.Clip(min=valmin,max=valmax)
        Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
        return clip

    if(len(attrs) > 0):
        Log.warn(f"Warning: Attribute {attrs.keys()} is not supported for operator Clip.")
        return None

    clip = aidge_core.Clip()
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return clip

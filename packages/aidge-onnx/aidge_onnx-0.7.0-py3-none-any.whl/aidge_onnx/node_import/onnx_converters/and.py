"""
Copyright (c) 2024 CEA-List

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
from aidge_onnx.utils import warn_unsupported_attr
from aidge_core import Log

@auto_register_import("and")
def import_and(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = {attr.name : attr for attr in onnx_node.attribute} #raw attributes get as no value will be accessed

    if opset < 7:

        if 'axis' in onnx_attrs:
            #Attribute not supported in Aidge
            del onnx_attrs['axis']
            warn_unsupported_attr('axis','And',opset)
            return None

        if 'broadcast' in onnx_attrs:
            #Attribute not supported in Aidge
            del onnx_attrs['broadcast']
            warn_unsupported_attr('broadcast','And',opset)
            return None

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'And' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    my_node = aidge_core.And(name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return my_node

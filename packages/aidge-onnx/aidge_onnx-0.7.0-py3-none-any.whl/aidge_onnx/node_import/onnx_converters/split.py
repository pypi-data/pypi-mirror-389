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
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("split")
def import_split(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    split_attrs: dict = {'axis': 0}# + conditional attr split

    if 'axis' in onnx_attrs:
        split_attrs['axis'] = onnx_attrs['axis']
        del onnx_attrs['axis']

    if opset < 11 and 'split' in onnx_attrs:
        split_attrs['split'] = onnx_attrs['split']
        del onnx_attrs['split']
    elif len(input_nodes) > 1 and input_nodes[1] is not None:
        split_attrs['split'] = input_nodes[1][0].get_operator().get_output(input_nodes[1][1])

    if opset >= 18 and 'num_outputs' in onnx_attrs:
        split_attrs['nb_outputs'] = onnx_attrs['num_outputs']
        del onnx_attrs['num_outputs']

    if 'nb_outputs' in split_attrs and 'split' in split_attrs:
        raise RuntimeError("Error: malformed ONNX: Split: can't specify both split and nb_outputs")

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Split' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    if 'split' in split_attrs:
        split_attrs['nb_outputs'] = len(split_attrs['split'])
    elif onnx_node.output is not None:
        split_attrs['nb_outputs'] = len(onnx_node.output)

    if 'nb_outputs' not in split_attrs:
        Log.warn("Warning: cannot load 'split' node, at least one of the following must be provided:\n- attr 'num_outputs'\n- attr 'split'\n- input 'split'.\nThis node will be filled by a GenericOperator.")
        return None

    my_node = aidge_core.Split(**split_attrs, name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return my_node

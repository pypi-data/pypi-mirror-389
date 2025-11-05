"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional
from onnx import NodeProto
import aidge_core
import onnx

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("reducesum")
def import_reducesum(onnx_node: NodeProto,
                      input_nodes: List[Tuple[aidge_core.Node, int]],
                      opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of pairs of Aidge Nodes which constitute the input
        of the current node and their associated output index linking to the
        current Node.
    :type input_nodes: List[aidge_core.Node, int]
    :param opset: Indicate opset version of the ONNX model, `default=None`
    :type opset: int, optional
    """
    # Convert provided attributes from node to a dictionary
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    reducesum_attrs : dict = {"axes" : [],"keep_dims" : 1, "noop_with_empty_axes" : 0}

    if 'keepdims' in onnx_attrs:
        reducesum_attrs['keep_dims'] = onnx_attrs['keepdims']
        del onnx_attrs['keepdims']

    if opset < 18 and 'axes' in onnx_attrs:
        reducesum_attrs['axes'] = onnx_attrs['axes']
        del onnx_attrs['axes']
    else:
        #try to get axes as input
        if input_nodes[1] is not None:
            reducesum_attrs['axes'] = input_nodes[1][0].get_operator().get_output(input_nodes[1][1])

        if 'noop_with_empty_axes' in onnx_attrs:
            reducesum_attrs['noop_with_empty_axes'] = onnx_attrs['noop_with_empty_axes']
            del onnx_attrs['noop_with_empty_axes']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'ReduceSum' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    my_op = aidge_core.ReduceSumOp(**reducesum_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(my_op, name = node_name)

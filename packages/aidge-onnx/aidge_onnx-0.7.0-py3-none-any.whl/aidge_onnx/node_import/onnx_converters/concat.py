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

@auto_register_import("concat")
def import_concat(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of pairs of Aidge Nodes which constitute the input
        of the current node and their associated output index linking to the
        current Node.
    :type input_nodes: List[aidge_core.Node, int]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    concat_attrs: dict = {"axis": None,"nb_inputs":len(input_nodes)}
    #### Attributes
    #  axis : int
    #    Which axis to concat on.
    #### Inputs
    #  inputs (variadic) : T
    #    List of tensors for concatenation
    #### Outputs
    #  concat_result : T
    #    Concatenated tensor
    if opset < 4:
        #### Attributes
        #  axis : int (default is 1)
        #    Which axis to concat on.
        concat_attrs["axis"] = 1

    if 'axis' in onnx_attrs:
        concat_attrs["axis"] = onnx_attrs['axis']
        del onnx_attrs['axis']

    if concat_attrs["axis"] is None:
        Log.warn("Warning: Operator 'Concat' must have 'axis' attribute. This node will be filled by a GenericOperator.")
        return None

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Concat' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    my_op = aidge_core.ConcatOp(**concat_attrs)

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(my_op, name = node_name)

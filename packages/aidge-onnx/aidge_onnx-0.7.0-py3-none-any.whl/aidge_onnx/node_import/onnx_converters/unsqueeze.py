"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Tuple, Optional

import aidge_core
from aidge_core import Log
import onnx
from onnx import NodeProto
from aidge_onnx.node_import import auto_register_import

@auto_register_import("unsqueeze")
def import_unsqueeze(
    onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int
) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[Tuple[aidge_core.Node, int]]
    :param opset: Optional opset version
    :type opset: int
    :return: Converted Aidge node
    :rtype: aidge_core.Node
    """
    node_name = onnx_node.output[0]
    attrs = {attr.name: attr for attr in onnx_node.attribute}

    axes: List[int] = []
    if opset is not None and opset < 13:
        #### Inputs
        #  data (heterogenous) : T
        #    Original tensor
        #### Attributes
        # axes (heterogeneous) - tensor(int64):
        #     List of integers indicating the dimensions to be inserted.
        #     Negative value means counting dimensions from the back.
        #     Accepted range is [-r, r-1] where r = rank(expanded).
        #### NOTE
        # opset < 13 is opset < 11 with support for negative index values
        if "axes" in attrs:
            axes = attrs["axes"].ints
            del attrs["axes"]
        else:
            Log.warn("Could not find attribute 'axes' for operator unsqueeze.")
            return None
    else:
        if len(input_nodes) < 2:
            Log.warn(f"Warning: for operator 'Unsqueeze' with opset {opset} requires 2 inputs.\nThis node will be filled by a GenericOperator.")
            return None
        if input_nodes[1] is not None:
            axes = input_nodes[1][0].get_operator().get_output(input_nodes[1][1])

    if len(attrs) > 0:
        #### Inputs
        # data (heterogeneous) - T:
        #     Original tensor
        # axes (heterogeneous) - tensor(int64):
        #     List of integers indicating the dimensions to be inserted. Negative value means counting dimensions from the back. Accepted range is [-r, r-1] where r = rank(expanded).
        Log.warn(f"Unsupported attribute(s): {attrs.keys()} for operator unsqueeze.")
        return None

    #### outputs
    # expanded (heterogeneous) - T:
    #     Reshaped tensor with same data as input.
    unsqueeze_node = aidge_core.Unsqueeze(axes=axes, name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return unsqueeze_node


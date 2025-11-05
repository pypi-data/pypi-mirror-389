"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Optional, Tuple

import aidge_core
from aidge_core import Log
import onnx
from onnx import NodeProto

from aidge_onnx.node_import import auto_register_import


@auto_register_import("squeeze")
def import_squeeze(
    onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int
) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.output[0]
    attrs = {attr.name: attr for attr in onnx_node.attribute}

    axes: List[int] = []
    if opset is not None and opset < 13:
        #### Inputs
        # data (heterogeneous) - T:
        #     Tensors with at least max(dims) dimensions.
        #### Attributes
        # axes - INTS :
        #     List of integers indicating the dimensions to squeeze. Negative value means counting dimensions from the back. Accepted range is [-r, r-1] where r = rank(data).
        #### Outputs
        # squeezed (heterogeneous) - T:
        #     Reshaped tensor with same data as input.
        #### NOTE
        # opset < 13 is like opset < 11 with support for negative index values
        if "axes" in attrs:
            axes = attrs["axes"].ints
            del attrs["axes"]
        else:
            # axes is optional for opset < 13
            axes = []
    else:
        if len(input_nodes)>1 and input_nodes[1] is not None: # if axes is available at import time, set the node attr
            axes = input_nodes[1][0].get_operator().get_output(input_nodes[1][1])

    if len(attrs) > 0:
        #### Inputs
        # Between 1 and 2 inputs.
        # data (heterogeneous) - T:
        #     Tensors with at least max(dims) dimensions.
        # axes (optional, heterogeneous) - tensor(int64):
        #     List of integers indicating the dimensions to squeeze. Negative value means counting dimensions from the back. Accepted range is [-r, r-1] where r = rank(data).
        #### Outputs
        # squeezed (heterogeneous) - T:
        #     Reshaped tensor with same data as input.
        Log.warn(f"Unsupported attribute(s): {attrs.keys()} for operator squeeze with opset {opset}.")
        return None

    squeeze_node = aidge_core.Squeeze(axes=axes, name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return squeeze_node


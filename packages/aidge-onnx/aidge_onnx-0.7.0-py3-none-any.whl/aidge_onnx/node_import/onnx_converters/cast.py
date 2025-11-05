"""
Copyright (c) 2025 CEA-List

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
from aidge_onnx.dtype_converter import onnx_to_aidge
import aidge_onnx.dtype_converter

from aidge_core import Log


@auto_register_import("cast")
def import_cast(
    onnx_node: NodeProto,
    input_nodes: List[Tuple[aidge_core.Node, int]],
    opset: int,
) -> aidge_core.Node:
    """
    Import the Cast operation from ONNX to Aidge.

    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[Tuple[aidge_core.Node, int]]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    :return: Aidge node representing the Cast operation
    :rtype: aidge_core.Node
    """

    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)

    # Extract the 'to' attribute which specifies the target data type
    if "to" not in onnx_attrs:
        Log.warn(
            f"Warning: 'to' attribute is required for Cast operation in node {node_name}"
        )
        return None

    target_type = onnx_attrs["to"]

    # Convert ONNX data type to Aidge data type
    try:
        aidge_target_type = onnx_to_aidge(target_type)
    except ValueError as e:
        Log.warn(f"Warning: {e} for Cast operation in node {node_name}")
        return None

    # Create the Aidge CastOp node
    cast_op = aidge_core.CastOp(target_type=aidge_target_type)
    my_node = aidge_core.Node(cast_op, name=node_name)

    Log.info(
        f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]"
    )
    return my_node

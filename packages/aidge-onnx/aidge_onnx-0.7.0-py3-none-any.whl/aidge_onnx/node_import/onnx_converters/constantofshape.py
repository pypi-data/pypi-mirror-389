"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Tuple, Optional

import aidge_core
from aidge_core import Log
import onnx
from onnx import numpy_helper, NodeProto
from aidge_onnx.node_import import auto_register_import


@auto_register_import("constantofshape")
def import_constant(
    onnx_node: NodeProto,
    input_nodes: List[Tuple[aidge_core.Node, int]],
    opset: int,
) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.output[0]
    onnx_attrs = {attr.name : attr for attr in onnx_node.attribute}
    attrs = {"value" : aidge_core.Tensor(float(0.0))}

    if "value" not in onnx_attrs:
        Log.warn("Missing \"value\" attribute in onnx_node ConstantOfShape with opset {opset}.")
        return None

    onnx_attrs["value"] = numpy_helper.to_array(onnx_attrs["value"].t)
    if onnx_attrs["value"].shape != (1,):
        Log.error(
            "ConstantOfShape : malformed attribute value, should be of dimension (1,), got {}",
            onnx_attrs["value"].shape,
        )
        return None
    Log.info(f"val type: {onnx_attrs['value'].dtype}")
    attrs["value"] = aidge_core.Tensor(onnx_attrs["value"])

    constant_of_shape_node = aidge_core.ConstantOfShape(attrs["value"], node_name)

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return constant_of_shape_node


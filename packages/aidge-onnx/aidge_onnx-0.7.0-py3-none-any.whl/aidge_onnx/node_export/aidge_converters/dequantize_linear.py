"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
import onnx
from onnx import helper, TensorProto
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional
from aidge_onnx.dtype_converter import aidge_to_onnx

@auto_register_export("Dequantizer")
def export_dequantize_linear(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()
    onnx_nodes = []
    current_scale = None
    for scale_operator in micro_graph.get_nodes():
        if scale_operator.type() == "Mul":
            #First scaling operation will have as parent 1 the scale producer
            current_scale = scale_operator.get_parent(1).get_operator().get_output(0)
            break

    if current_scale is None:
        aidge_core.Log.warn(f"Failed to convert {aidge_node.name()}[{aidge_node.type()}], could not determine the scaling factor.")
        return None

    initializer_list.append(
        helper.make_tensor(
            aidge_node.name()+"_scale_tensor",
            aidge_to_onnx(current_scale.dtype),
            [],
            current_scale
        )
    )
    node_inputs_name.append(aidge_node.name()+"_scale_tensor")

    dequantize_linear = helper.make_node(
        name = aidge_node.name(),
        op_type = "DequantizeLinear",
        inputs = node_inputs_name,
        outputs =  node_outputs_name)

    onnx_nodes = [dequantize_linear]
    return onnx_nodes

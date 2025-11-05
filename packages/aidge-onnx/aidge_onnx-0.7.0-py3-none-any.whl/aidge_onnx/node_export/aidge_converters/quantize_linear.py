"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
import aidge_onnx.dtype_converter
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional

@auto_register_export("Quantizer")
def export_quantize_linear(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    #This node can have multiple origins to take into account:
    #1- Node made by Aidge's quantization: Quantizer, metaop made from mul-> round are combinations equivalent to onnx's quantizelinear
    #2- Imported Quantized ONNX model: QuantizeLinear Metaoperator made in the import of a quantized onnx model

    #They will probably will be mutualize in a future aidge version

    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()
    onnx_nodes = []
    out_dtype = aidge_node.get_operator().get_output(0).dtype
    onnx_target_type = aidge_onnx.dtype_converter.aidge_to_onnx(out_dtype)

    current_scale = None
    for scale_operator in micro_graph.get_ordered_nodes():
        if scale_operator.type() in ["Mul","Div"]:
            #First scaling operation will have as parent 1 the scale producer
            current_scale = scale_operator.get_parent(1).get_operator().get_output(0)
            break
    if current_scale is None:
        aidge_core.Log.warn(f"Failed to convert {aidge_node.name()}[{aidge_node.type()}], could not determine the scaling factor.")
        return None

    if "Mul" in [node.type() for node in micro_graph.get_nodes()]:
        #If QuantizeLinear has Mul operator Scaling factor has to be inverted (ONNX uses Div operation)
        temp_tensor = aidge_core.Tensor(1)

        temp_tensor.set_datatype(current_scale.dtype)
        current_scale = temp_tensor/current_scale

        # creation of the constant node
        onnx_input_type = aidge_onnx.dtype_converter.aidge_to_onnx(current_scale.dtype)

        initializer_list.append(
            helper.make_tensor(aidge_node.name()+"_scale_tensor",
                onnx_input_type,
                [],
                current_scale
            )
        )
        node_inputs_name.append(aidge_node.name()+"_scale_tensor")
    else:
        aidge_core.Log.warn("Currently only floating point scaling factor is supported.")
        return None
    #zero point is required to determine dtype output so one has to be created
    initializer_list.append(
        helper.make_tensor(
            aidge_node.name()+"_zero_point_tensor",
            onnx_target_type,
            [],
            [0]
        )
    )

    node_inputs_name.append(aidge_node.name()+"_zero_point_tensor")

    quantize_linear = helper.make_node(name = aidge_node.name(),
                                       op_type = "QuantizeLinear",
                                       inputs = node_inputs_name,
                                       outputs = node_outputs_name)
    onnx_nodes.append(quantize_linear)

    return onnx_nodes

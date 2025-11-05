"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional

@auto_register_export("Conv1D", "Conv2D", "Conv3D", "ConvDepthWise1D", "ConvDepthWise2D", "ConvDepthWise3D")
def export_conv(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()
    #If bias not set, remove bias as an input
    if (
        aidge_node.input(2)[0]
        and not aidge_node.input(2)[0].get_operator().get_output(0).impl
    ):
        node_inputs_name.remove(aidge_node.input(2)[0].name() + "_out0")
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Conv",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
        helper.make_attribute(
            "dilations",
            aidge_operator.attr.get_attr("dilation_dims")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "group",
            aidge_operator.nb_channels() if "DepthWise" in aidge_node.type() else 1
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "kernel_shape",
            aidge_operator.attr.get_attr("kernel_dims")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "strides",
            aidge_operator.attr.get_attr("stride_dims")
    ))
    return [onnx_node]

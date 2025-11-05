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

@auto_register_export("PaddedConvDepthWise2D")
def export_padded_conv(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()
    conv_op, pad_op = None, None
    for node in micro_graph.get_nodes():
        if node.type() == "ConvDepthWise1D" or node.type() == "ConvDepthWise2D" or node.type() == "ConvDepthWise3D":
            conv_op = node.get_operator()
        elif node.type() == "Pad":
            pad_op = node.get_operator()
        else:
            raise RuntimeError(f"Unsupported node type: {node.type()} inside PaddedConv.")
    #If bias not set, remove bias as an input
    if aidge_node.input(2)[0] is None:
        node_inputs_name.remove('') # should have no name
    elif not aidge_node.input(2)[0].get_operator().get_output(0).impl:
        node_inputs_name.remove(aidge_node.input(2)[0].name()+"_out0")

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Conv",
        inputs=node_inputs_name[:3], # ignore Pad extra inputs
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
        helper.make_attribute(
            "dilations",
            conv_op.attr.get_attr("dilation_dims")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "group",
            conv_op.nb_channels() # Group size = nb channel out for convdw
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "kernel_shape",
            conv_op.attr.get_attr("kernel_dims")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "strides",
            conv_op.attr.get_attr("stride_dims")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "pads",
            pad_op.attr.get_attr("pads")
    ))

    return [onnx_node]

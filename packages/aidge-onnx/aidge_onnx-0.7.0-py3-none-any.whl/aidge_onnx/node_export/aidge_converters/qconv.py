"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
import onnx
from onnx import helper
from aidge_onnx.node_export import auto_register_export
import aidge_onnx.dtype_converter
from typing import List, Optional

@auto_register_export("QLinearConv")
def export_quantified_Conv(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    convs_types_list = ["Conv1D", "Conv2D", "Conv3D",
                        "ConvDepthWise1D", "ConvDepthWise2D", "ConvDepthWise3D",
                        "PaddedConv1D", "PaddedConv2D", "PaddedConv3D",
                        "PaddedConvDepthWise2D"]

    onnx_nodes = []
    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()
    has_bias = True

    #getters of conv operator and scaling operator from the metaoperator
    Conv_op = None
    Conv_type = None
    for node in micro_graph.get_nodes():
        #conditions may change as operator types are currently being modified
        if node.type() in convs_types_list:
            Conv_op = node
            Conv_type = node.type()

            break
        elif node.type() not in ["Quantizer","Producer","QuantizeLinear","Cast","Dequantizer","DequantizeLinear"]:
            raise RuntimeError(f"Unsupported node type: {node.type()} inside QLinearConv.")


    def inverse_tensor(tensor):
        temp_tensor = aidge_core.Tensor(1)
        temp_tensor.set_datatype(tensor.dtype)
        return temp_tensor/tensor

    def make_quantizelinear(base_name, sf_value,inverse_sf, input_name):
        if inverse_sf:
            sf_value = inverse_tensor(sf_value)
        scale_node = make_constant_node(base_name+"_scale",prequant_dtype,[],sf_value)

        quant_input_names =[input_name,base_name+"_scale_out"]
        if opset < 21:
            zero_point_node = make_constant_node(base_name+"_zeropoint",quant_dtype,[],[0])
            quant_input_names.append(base_name+"_zeropoint_out")

            quant_linear_node = helper.make_node(name=base_name,
                                                op_type="QuantizeLinear",
                                                inputs=quant_input_names,
                                                outputs=[base_name+"_out"])
            return zero_point_node, scale_node, quant_linear_node

        quant_linear_node = helper.make_node(name=base_name,
                                            op_type="QuantizeLinear",
                                            inputs=quant_input_names,
                                            outputs=[base_name+"_out"],
                                            output_dtype = quant_dtype)
        return scale_node, quant_linear_node

    def make_constant_node(base_name, tensor_dtype,tensor_dims,tensor_value):
        constant_node = helper.make_node(
                name=base_name,
                op_type="Constant",
                inputs=[],
                outputs=[base_name+"_out"])
        constant_node.attribute.append(helper.make_attribute("value",
                                                            helper.make_tensor(base_name+"_tensor",
                                                                            tensor_dtype,
                                                                            tensor_dims,
                                                                            tensor_value)))
        return constant_node

    def folding(data_prod, scale_prod, quant_node):
        n_data_prod = data_prod.clone()
        n_scale_prod = scale_prod.clone()
        n_quant_node = quant_node.clone()

        n_data_prod.get_operator().attr.set_attr("constant",True)
        n_scale_prod.get_operator().attr.set_attr("constant",True)

        n_data_prod.add_child(n_quant_node,0,0)
        n_scale_prod.add_child(n_quant_node,0,1)
        n_graph = aidge_core.get_connected_graph_view(n_quant_node)
        aidge_core.constant_folding(n_graph)
        folded_prod = n_graph.get_nodes().pop()
        return folded_prod

    #-- Normal Conv export

    if Conv_op.input(2)[0] is None or not Conv_op.input(2)[0].get_operator().get_output(0).has_impl():
        # remove bias input if no bias
        node_inputs_name.pop() # In qop_regroup function, none inputs (bias) were moved to the last index
        has_bias = False

    has_pads = False

    conv_inner_op = Conv_op.get_operator()
    if "Padded" in Conv_type:#TODO change, this method is not enough
        #Treatment for a padded convolution, code identical to PaddedConv export
        conv_inner_micro_graph = Conv_op.get_operator().get_micro_graph()
        pad_inner_op = None
        for inner_node in conv_inner_micro_graph.get_nodes():
            if "Conv" in inner_node.type():
                conv_inner_op = inner_node.get_operator()
            elif "Pad" in inner_node.type():
                pad_inner_op = inner_node.get_operator()
            else:
                raise RuntimeError(f"Unsupported node type: {inner_node.type()} inside PaddedConv.")
        # Computing padding
        kernel_dims = conv_inner_op.attr.get_attr("kernel_dims")
        aidge_pads  = pad_inner_op.attr.get_attr("begin_end_borders")
        pads = [0] * 2*len(kernel_dims)
        for i in range(0, len(kernel_dims)):
            pads[i] = aidge_pads[2*i]
            pads[len(kernel_dims)+i] = aidge_pads[2*i+1]

        has_pads = True

    #-- QLinearConv export
    #QLinearConv inputs are as follows:
    #input X , x_scale , x_zero_point
    #input W , w_scale ,  w_zero_point
    #output y_scale, y_zero_point
    #input B (optional)

    prequant_dtype = aidge_onnx.dtype_converter.aidge_to_onnx(aidge_node.get_operator().get_input(1).dtype)
    quant_dtype = aidge_onnx.dtype_converter.aidge_to_onnx(aidge_node.get_operator().get_output(0).dtype)


    w_scale_value = aidge_node.get_parent(2).get_operator().get_output(0)
    y_scale_value = aidge_node.get_parent(3 + has_bias*2).get_operator().get_output(0)

    #Get input quantizer's scale value
    if not has_bias:
        #if bias is not present, the quantizer node needs to be found by exploring the graph
        current_parent = aidge_node.get_parent(0)
        while current_parent.type() not in ["Quantizer","QGemm","QLinearConv"]:
                #loop in case the quantizer is detached (usually shouldn't be the case)
                current_parent = current_parent.get_parent(0)
                if current_parent is None:
                    raise RuntimeError("Quantization node for input of QLinearConv could not be found")

        input_quant_idx = 1
        if current_parent.type() in ["QLinearConv", "QGemm"]:
            #TODO qlinearconv and qgemmm same index?
            current_parent_has_bias = len(current_parent.inputs()) >5
            input_quant_idx = 3 + current_parent_has_bias*2
        x_scale_value_invs = inverse_tensor(current_parent.get_parent(input_quant_idx).get_operator().get_output(0))
    else:
        #If bias is present the x_scale can be calculated
        b_scale_value = aidge_node.get_parent(4).get_operator().get_output(0)
        x_scale_value_invs = inverse_tensor(b_scale_value / w_scale_value)

    x_scale_node = make_constant_node(f"{Conv_op.name()}_x_scale", prequant_dtype,[],x_scale_value_invs)
    onnx_nodes.append(x_scale_node)

    x_zero_point = make_constant_node(f"{Conv_op.name()}_x_zeropoint",quant_dtype,[],[0])
    w_zero_point = make_constant_node(f"{Conv_op.name()}_w_zeropoint",quant_dtype,[],[0])
    y_zero_point = make_constant_node(f"{Conv_op.name()}_y_zeropoint",quant_dtype,[],[0])

    #Y zero point is "optional" but needed if the desired output dtype is int8 or uint8
    #if not provided the output dtype defaults to float32
    onnx_nodes.extend([x_zero_point,w_zero_point,y_zero_point])

    data_input_name = node_inputs_name[0]
    #in case the input is not quantized (shouldn't be the case, a quantizelinear is manually added)
    if aidge_node.get_operator().get_input(0).dtype != aidge_core.dtype.int8:
        x_nodes = make_quantizelinear(f"{Conv_op.name()}_x_ql",x_scale_value_invs,False,node_inputs_name[0])
        onnx_nodes.append(x_nodes)
        data_input_name = f"{Conv_op.name()}_x_ql_out"

    w_scale_value_invs = inverse_tensor(w_scale_value)
    w_nodes = make_quantizelinear(f"{Conv_op.name()}_w_ql",w_scale_value_invs,False,node_inputs_name[1])

    w_scale_node = make_constant_node(f"{Conv_op.name()}_w_scale", prequant_dtype,[],w_scale_value_invs)
    onnx_nodes.extend([w_scale_node,*w_nodes])


    if has_bias:
        bias_tensor = folding(aidge_node.get_parent(3),aidge_node.get_parent(4),aidge_node.get_operator().get_micro_graph().get_ordered_inputs()[3][0]).get_operator().get_output(0)
        b_quantized_node = make_constant_node(f"{Conv_op.name()}_b_ql",onnx.TensorProto.INT32,bias_tensor.dims,bias_tensor)
        onnx_nodes.append(b_quantized_node)

    #TODO change order to accomodate
    new_node_inputs_name = [data_input_name,
                            f"{Conv_op.name()}_x_scale_out",
                            f"{Conv_op.name()}_x_zeropoint_out",
                            f"{Conv_op.name()}_w_ql_out",
                            f"{Conv_op.name()}_w_scale_out",
                            f"{Conv_op.name()}_w_zeropoint_out"]

    y_scale_invs = inverse_tensor(y_scale_value)
    y_scale_node = make_constant_node(f"{Conv_op.name()}_y_scale", prequant_dtype,[],y_scale_invs)
    onnx_nodes.append(y_scale_node)
    new_node_inputs_name.extend([f"{Conv_op.name()}_y_scale_out",f"{Conv_op.name()}_y_zeropoint_out"])

    if has_bias:
        new_node_inputs_name.append(f"{Conv_op.name()}_b_ql_out")

    #See if dequantize linear is needed (onnx quantize-dequantize logic)
    #only the first output is looked at, it should be representative

    qlinearconv_output_names =  node_outputs_name
    dequant_need = False
    if aidge_node.get_ordered_children()[0] == [] or aidge_node.get_ordered_children()[0][0].type() not in ["Dequantizer","DequantizeLinear","QGemm","QLinearConv"]:
        #create dequantizelinear
        onnx_dq_scale_node = make_constant_node(aidge_node.name()+"_dq_scale",prequant_dtype,[],y_scale_invs)

        onnx_nodes.append(onnx_dq_scale_node)
        qlinearconv_output_names = [aidge_node.name()+"_out"]
        dequant_need = True

        dequantize_linear_node = helper.make_node(name = aidge_node.name()+"_Dequantize",
                                                  op_type = "DequantizeLinear",
                                                  inputs = [aidge_node.name()+"_out", aidge_node.name()+"_dq_scale_out"],
                                                  outputs = node_outputs_name)#output_dtype argument not used to remain compatible to earlier versions of onnx

    #onnx Qgemm node creation and attributes
    qlinearconv_node = helper.make_node(
        name = Conv_op.name(),
        op_type = "QLinearConv",
        inputs = new_node_inputs_name,
        outputs = qlinearconv_output_names
    )
    onnx_nodes.append(qlinearconv_node)

    qlinearconv_node.attribute.append(
        helper.make_attribute(
            "dilations",
            conv_inner_op.attr.get_attr("dilation_dims")
    ))
    qlinearconv_node.attribute.append(
        helper.make_attribute(
            "group",
            conv_inner_op.nb_channels() if "DepthWise" in aidge_node.type() else 1
    ))
    qlinearconv_node.attribute.append(
        helper.make_attribute(
            "kernel_shape",
            conv_inner_op.attr.get_attr("kernel_dims")
    ))
    qlinearconv_node.attribute.append(
        helper.make_attribute(
            "strides",
            conv_inner_op.attr.get_attr("stride_dims")
    ))

    if has_pads:
        qlinearconv_node.attribute.append(
        helper.make_attribute(
            "pads",
            pads
    ))

    if dequant_need: onnx_nodes.append(dequantize_linear_node)

    return onnx_nodes

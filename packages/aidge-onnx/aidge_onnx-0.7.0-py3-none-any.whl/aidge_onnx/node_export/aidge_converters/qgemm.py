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

@auto_register_export("QGemm")
def export_qgemm(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    onnx_nodes = []
    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()

    #getters of conv operator and scaling operator from the metaoperator
    FC_op = None
    for node in micro_graph.get_nodes():
        #conditions may change as operator types are currently being modified
        if node.type() == "FC":
            FC_op = node
            break
        elif node.type() not in ["Dequantizer","Quantizer","Producer","QuantizeLinear","Cast"]:
            raise RuntimeError(f"Unsupported node type: {node.type()} inside QGemm {aidge_node.name()}")

    #Get prequantization dtype and post quantization dtype; ex: float32 and int8 respectively
    #TODO Better getter for dtypes, more robust
    prequant_dtype = aidge_onnx.dtype_converter.aidge_to_onnx(aidge_node.get_operator().get_input(1).dtype())
    quant_dtype = aidge_onnx.dtype_converter.aidge_to_onnx(FC_op.get_parent(1).get_parent(0).get_operator().get_output(0).dtype())

    def inverse_tensor(tensor):
        temp_tensor = aidge_core.Tensor(1)
        temp_tensor.set_datatype(tensor.dtype())
        return temp_tensor/tensor

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

    #-- Normal FC export
    #If bias not set, remove bias as an input
    has_bias = True
    if FC_op.input(2)[0] is None or not FC_op.input(2)[0].get_operator().get_output(0).has_impl():
        # remove bias input if no bias
        node_inputs_name.pop() # In qop_regroup function, none inputs (bias) were moved to the last index
        has_bias = False

    # If input is not flatten, add a Flatten node
    if FC_op.get_operator().get_input(0) and len(FC_op.get_operator().get_input(0).dims()) != 2:
        flatten_name = f"{FC_op.name()}_flatten"
        flatten_out = f"{flatten_name}_out_0"

        onnx_node = helper.make_node(
            name=flatten_name,
            op_type="Flatten",
            inputs=[node_inputs_name[0]],
            outputs=[flatten_out],
        )
        onnx_node.attribute.append(helper.make_attribute("axis", 1))

        onnx_nodes.append(onnx_node)
        node_inputs_name[0] = flatten_out

    #Qgemm are as follows:
    #input A , a_scale , a_zero_point
    #input B , b_scale , b_zero_point
    #C (optional)
    #output y_scale(optional), y_zero_point(optional)

    #Considering this, a_scale needs to be calculated or found and zero points added
    #The rest is already easily accessible
    #All scaling values will be inversed to take into account the difference in operator (div vs mul)
    b_scale_value = aidge_node.get_parent(2).get_operator().get_output(0)
    y_scale_value = aidge_node.get_parent(5).get_operator().get_output(0)

    #Get input quantizer's scale value
    if not has_bias:
        #if bias is not present, the quantizer node needs to be found by exploring the graph
        current_parent = aidge_node.get_parent(0)
        while current_parent.type() not in ["Quantizer","QGemm","QLinearConv"]:
                #loop in case the quantizer is detached (shouldn't be the case)
                current_parent = current_parent.get_parent(0)
                if current_parent is None:
                    raise RuntimeError("Quantization node for input of QGemm could not be found")

        input_quant_idx = 1
        if current_parent.type() in ["QLinearConv", "QGemm"]:
            current_parent_has_bias = len(current_parent.inputs()) >5
            input_quant_idx = 3 + current_parent_has_bias*2
        a_scale_value_invs = inverse_tensor(current_parent.get_parent(input_quant_idx).get_operator().get_output(0))
    else:
        #If bias is present a_scale can be calculated (a_scale = c_scale / b_scale from b_scale = c_scale * a_scale)
        c_scale_value = aidge_node.get_parent(4).get_operator().get_output(0)
        a_scale_value_invs = inverse_tensor(c_scale_value / b_scale_value)

        # all quantized operators must have their bias folded
        # TODO folding should be moved to set_qop function
        bias_tensor = folding(aidge_node.get_parent(3),aidge_node.get_parent(4),aidge_node.get_operator().get_micro_graph().get_ordered_inputs()[3][0]).get_operator().get_output(0)
        c_quantized_node = make_constant_node(f"{FC_op.name()}_c_ql",onnx.TensorProto.INT32,bias_tensor.dims(),bias_tensor)
        onnx_nodes.append(c_quantized_node)

    a_scale_node = make_constant_node(f"{FC_op.name()}_a_scale", prequant_dtype,[],a_scale_value_invs)
    a_zero_point = make_constant_node(f"{FC_op.name()}_a_zeropoint",quant_dtype,[],[0])
    b_zero_point = make_constant_node(f"{FC_op.name()}_b_zeropoint",quant_dtype,[],[0])
    #Y zero point is "optional" but needed if the desired output dtype is int8 or uint8
    #for now all qops in aidge wil have their output quantized if possible
    y_zero_point = make_constant_node(f"{FC_op.name()}_y_zeropoint",quant_dtype,[],[0])

    b_scale_value_invs = inverse_tensor(b_scale_value)
    b_scale_node = make_constant_node(f"{FC_op.name()}_b_scale", prequant_dtype,[],b_scale_value_invs)

    y_scale_invs = inverse_tensor(y_scale_value)
    y_scale_node = make_constant_node(f"{FC_op.name()}_y_scale", prequant_dtype,[],y_scale_invs)

    onnx_nodes.extend([a_scale_node, a_zero_point, b_scale_node, b_zero_point,
                       y_scale_node,y_zero_point])

    # Input names derived from the producers created
    new_node_inputs_name = [node_inputs_name[0],
                            f"{FC_op.name()}_a_scale_out",
                            f"{FC_op.name()}_a_zeropoint_out",
                            node_inputs_name[1],# TODO Verify for all cases(aidge quant, onnx quant import etc)
                            f"{FC_op.name()}_b_scale_out",
                            f"{FC_op.name()}_b_zeropoint_out"]

    if has_bias:
        new_node_inputs_name.append(f"{FC_op.name()}_c_ql_out")

    new_node_inputs_name.extend([f"{FC_op.name()}_y_scale_out",f"{FC_op.name()}_y_zeropoint_out"])

    #Qgemm creation
    qgemm_node = helper.make_node(
        name = FC_op.name(),
        op_type = "QGemm",
        inputs = new_node_inputs_name,
        outputs = node_outputs_name,
        domain="com.microsoft"
    )
    onnx_nodes.append(qgemm_node)
    #qgemm does not have default values for its attributes so they must be especified
    qgemm_node.attribute.append(helper.make_attribute("alpha", 1.0))
    qgemm_node.attribute.append(helper.make_attribute("transA", 0))
    qgemm_node.attribute.append(helper.make_attribute("transB", 1))#transB at 1 as per aidge default

    return onnx_nodes

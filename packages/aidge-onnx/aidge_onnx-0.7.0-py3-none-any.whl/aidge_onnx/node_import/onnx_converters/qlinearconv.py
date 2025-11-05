"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional
import numpy as np

import aidge_core
import onnx
from onnx import NodeProto
from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log


@auto_register_import("qlinearconv")
def import_qlinearconv(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    #Qlinear Conv is the quantized convolution representation of ONNX, produced by quantization by Qop
    #Qlinear Conv uses quantized inputs, weights and bias, and returns a quantized output
    #The quantized inputs,weights and bias are firstly dequantized, passed by a normal convolution then quantized again
    #This operator can be described as a normal convolution with DequantizeLinear operators in its inputs(data, weight and bias)
    #and QuantizeLinear operators in its output
    #Inputs descriptions:
        #x: quantized input data (qlinearconv expects a quantified input)
        #x_scale: scaling factor used in the quantization of the input data (will be used to dequantify the input data)
        #x_zero_point: zero point used in the quantization of the input data (will be used to dequantify the input data)
        #w: quantized convolution weights (qlinearconv expects quantified weights)
        #w_scale: scaling factor used in the quantization of the weights (will be used to dequantify the weights)
        #w_zero_point: zero point used in the quantization of the weights (will be used to dequantify the weights)
        #y_scale: scaling factor that will be used in the quantization of the convolution output
        #y_zero_point: zero point that will be used in the quantization of the convolution output
        #b (optional): quantized convolution bias (qlinearconv expects a quantified bias)

    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    conv_attrs: dict = {}

    if 'kernel_shape' in onnx_attrs:
        kernel_dims = onnx_attrs['kernel_shape']
        del onnx_attrs['kernel_shape']
    else:
        # If not present, should be inferred from input W.
        if input_nodes[1] is None:
            Log.warning(f"Kernel dims cannot be inferred from W for qlinearconv node at import time. This node will be filled by a GenericOperator.")
            return None
        kernel_dims = input_nodes[1][0].get_operator().get_output(input_nodes[1][1]).dims[2:]
    kernel_lenght = len(kernel_dims)#to prevent reutilisation of len and kerneldims

    if 'strides' in onnx_attrs:
        conv_attrs['stride_dims'] = onnx_attrs['strides']
        del onnx_attrs['strides']
    else:
        # If not present, the stride defaults is 1 along each spatial axis.
        conv_attrs['stride_dims'] = [1] * kernel_lenght

    if 'dilations' in onnx_attrs:
        conv_attrs['dilation_dims'] = onnx_attrs['dilations']
        del onnx_attrs['dilations']
    else:
        # If not present, the stride defaults is 1 along each spatial axis.
        conv_attrs['dilation_dims'] = [1] * kernel_lenght

    #group is 1 by default
    group = 1
    if 'group' in onnx_attrs:
        group = onnx_attrs['group']
        del onnx_attrs['group']

    conv_attrs['padding_dims'] = [0] * 2*kernel_lenght
    if 'pads' in onnx_attrs:
        # `pads` format should be as follow [x1_begin, x2_begin...x1_end, x2_end,...]
        for i in range(0, kernel_lenght):
            conv_attrs['padding_dims'][2*i] = onnx_attrs['pads'][i]
            conv_attrs['padding_dims'][2*i+1] = onnx_attrs['pads'][kernel_lenght+i]
        del onnx_attrs['pads']

    if 'auto_pad' in onnx_attrs and onnx_attrs['auto_pad'] in (b'NOTSET', b'SAME_UPPER', b'SAME_LOWER', b'VALID'):
        if onnx_attrs['auto_pad'] != b'NOTSET' and np.count_nonzero(conv_attrs['padding_dims']) > 0:
            raise RuntimeError(f"Error: malformed ONNX: cannot have both non-zero 'pads' and 'auto_pad' different from 'NOTSET'.")

        for i,ele in enumerate(kernel_dims):
            padding = ele - conv_attrs['stride_dims'][i]
            floorHalfPadding = padding // 2

            if onnx_attrs['auto_pad'] == b'SAME_UPPER':
                conv_attrs['padding_dims'][2*i] = floorHalfPadding
                conv_attrs['padding_dims'][2*i+1] = padding - floorHalfPadding
            elif onnx_attrs['auto_pad'] == b'SAME_LOWER':
                conv_attrs['padding_dims'][2*i] = padding - floorHalfPadding
                conv_attrs['padding_dims'][2*i+1] = floorHalfPadding
        del onnx_attrs['auto_pad']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Conv' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    if group == 1:
        op_aidge_class_name = f"Conv{kernel_lenght}D"
        op_aidge_constr_name = f"Conv{kernel_lenght}DOp"
    else:
        #If group is different than one a depthwise convolution will be maade
        op_aidge_class_name = f"ConvDepthWise{kernel_lenght}D"
        op_aidge_constr_name = f"ConvDepthWise{kernel_lenght}DOp"

    if np.count_nonzero(conv_attrs['padding_dims']) > 0:
        #if padding_dims values are different from 0 then a padded convolution will be made
        op_aidge_class_name = "Padded" + op_aidge_class_name
        op_aidge_constr_name = "Padded" + op_aidge_constr_name
    else:
        del conv_attrs['padding_dims']

    if op_aidge_class_name in dir(aidge_core):
        aidge_op = aidge_core.__getattribute__(op_aidge_constr_name)(
            kernel_dims,
            **conv_attrs
        )
    else:
        Log.warn(f"Warning: {op_aidge_class_name} is not supported in Aidge. This node will be filled by a GenericOperator.")
        return None


    aidge_conv_node = aidge_core.Node(aidge_op, name = node_name)
    ### Quantization part import

    #get all the onnx initializers, will be used to know the dtypes used
    quantif_inputs = []
    for idx, inp in enumerate(input_nodes[1:]):
        prod_node = inp[0]
        if prod_node is None:
            Log.warning(f"Input {idx-1} is not available at import time for node qlinearconv, This node will be filled by a GenericOperator.")
            return None
        else:
            quantif_inputs.append(prod_node.get_operator().get_output(0))

    ##creation of a metaoperator equivalent to quantize linear
    #QuantizeLinear output type is dependent on zero_point dtype
    if len(quantif_inputs)<7:
        Log.warning(f"Need at least 7 inputs for qlinearconv node, got {len(quantif_inputs)} inputs. This node will be filled by a GenericOperator.")
        return None

    #getter of y_zero_point dtype
    output_zero_point_dtype = quantif_inputs[6].dtype

    #nodes creation: Div -> Round -> Cast -> Add
    output_quant_div = aidge_core.Div(node_name+"_quant_div_node")
    output_quant_round = aidge_core.Round(node_name+"_quant_round_node")
    output_quant_cast = aidge_core.Cast(output_zero_point_dtype,
                                        node_name+"_quant_cast_node")
    output_quant_add = aidge_core.Add(node_name+"_quant_add_node")

    #Nodes connection
    output_quant_div.add_child(output_quant_round,0,0)
    output_quant_round.add_child(output_quant_cast,0,0)
    output_quant_cast.add_child(output_quant_add,0,0)

    output_quantize_linear_graph = aidge_core.get_connected_graph_view(output_quant_add)

    #inputs of QuantizeLinear and y quantization attributes must be in the following order:
    #input data, scaling factor, zero_point
    output_quantize_linear_graph.set_ordered_inputs([[output_quant_div,0],#input
                                                     [output_quant_div,1],#scaling factor
                                                     [output_quant_add,1]])#zero point

    #creation of metaoperator
    output_metaop_quantize_linear = aidge_core.meta_operator("QuantizeLinear",
                             output_quantize_linear_graph,
                             name = node_name+"output_quantize")

    ##method for the creation of a metaoperator equivalent to dequantize linear
    def dequantize_linear(base_name,cast_data_type,descaling_factor = None,zero_point = None):
        #Nodes creation: Sub -> Cast -> Mul
        sub_node = aidge_core.Sub(base_name+"_sub")
        #output type is dependent on scaling factor dtype
        cast_node = aidge_core.Cast(cast_data_type,
                                    name = base_name+"_cast")
        mul_node = aidge_core.Mul(base_name+"_mul")

        #booleans to see if producers are needed for the node or if they are just ordinary inputs
        has_factor = descaling_factor is not None
        has_zero_point = zero_point is not None

        #producers creation
        if has_factor:
            producer_mul_node = aidge_core.Producer(descaling_factor,#scaling factor
                                                            base_name+"_producer_scaling_factor",
                                                            True)
            producer_mul_node.add_child(mul_node,0,1)

        if has_zero_point:
            producer_sub_node = aidge_core.Producer(zero_point,
                                                        base_name+"_producer_zero_point",
                                                        True)

            producer_sub_node.add_child(sub_node,0,1)

        #Nodes connection
        sub_node.add_child(cast_node,0,0)
        cast_node.add_child(mul_node,0,0)

        dequantize_graph = aidge_core.get_connected_graph_view(mul_node)

        #inputs of DequantizeLinear and y quantization attributes must be in the following order:
        #input data, descaling factor, zero_point
        ordered_inputs_list = [[sub_node,0]]
        if not has_factor:
            #if there is no scaling producer, append scaling factor input
            ordered_inputs_list.append([mul_node,1])
        if not has_zero_point:
            #if there is no zero point producer, append zero_point input
            ordered_inputs_list.append([sub_node,1])

        dequantize_graph.set_ordered_inputs(ordered_inputs_list)

        #Metaoperator creation
        dequant_metaop = aidge_core.meta_operator("DequantizeLinear",
                                                dequantize_graph,
                                                name = base_name)

        return dequant_metaop

    ##data input dequantize operator
    input_metaop_dequantize_linear = dequantize_linear(node_name+"_input_dequantize",
                                                       #input scaling factor dtype
                                                        quantif_inputs[0].dtype)

    ##convolution weight dequantize operator
    weight_metaop_dequantize_linear = dequantize_linear(node_name+"_weight_dequantize",
                                                        #weight scaling factor dtype
                                                        quantif_inputs[3].dtype)

    ##convolution bias dequantize operator
    #Dequantize operator attribute's values are not indicated in qlinear inputs but they are calculated or equal to:
    #bias scaling = input_scaling*weight_scaling
    #bias zero point = 0
    #source: https://onnx.ai/onnx/operators/onnx__QLinearConv.html#:~:text=using%20scale%20%3D%20x_scale%20*%20w_scale%20and%20zero_point%20%3D%200

    bias_scaling = np.multiply(np.asarray(quantif_inputs[0]),
                               np.asarray(quantif_inputs[3]))
    bias_scaling_tensor = aidge_core.Tensor(bias_scaling)

    bias_zero_point_tensor = aidge_core.Tensor(np.array(0))

    #metaoperator for bias dequantize
    bias_metaop_dequantize_linear = dequantize_linear(node_name+"_bias_dequantize",
                                                      bias_zero_point_tensor.dtype,
                                                      bias_scaling_tensor,
                                                      bias_zero_point_tensor)

    ## Dequantize metaop, Convolution and Quantize metaop operators connection
    input_metaop_dequantize_linear.add_child(aidge_conv_node,0,0)
    weight_metaop_dequantize_linear.add_child(aidge_conv_node,0,1)
    bias_metaop_dequantize_linear.add_child(aidge_conv_node,0,2)
    aidge_conv_node.add_child(output_metaop_quantize_linear,0,0)

    qlinear_conv_graph = aidge_core.get_connected_graph_view(output_metaop_quantize_linear)

    #QlinearConv inputs must be in the following order:
    qlinear_conv_graph.set_ordered_inputs([#convolution data input
                                           [input_metaop_dequantize_linear,0],
                                           #Input scaling factor
                                           [input_metaop_dequantize_linear,1],
                                           #Input zero point
                                           [input_metaop_dequantize_linear,2],
                                           #quantized weight input
                                           [weight_metaop_dequantize_linear,0],
                                           #Weight scaling factor
                                           [weight_metaop_dequantize_linear,1],
                                           #Weight zero point
                                           [weight_metaop_dequantize_linear,2],
                                           #output scaling factor
                                           [output_metaop_quantize_linear,1],
                                           #output scaling factor
                                           [output_metaop_quantize_linear,2],
                                           #quantized bias input
                                           [bias_metaop_dequantize_linear,0]])

    #QlinearConv metaop creation
    qlinear_conv_metaop = aidge_core.meta_operator("QLinearConv",
                             qlinear_conv_graph,
                             name = "qlinear_"+node_name)

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return qlinear_conv_metaop

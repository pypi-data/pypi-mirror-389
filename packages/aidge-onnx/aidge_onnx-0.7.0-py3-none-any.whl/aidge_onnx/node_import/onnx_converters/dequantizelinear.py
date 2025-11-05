"""
Copyright (c) 2023 CEA-List

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

from aidge_core import Log
from aidge_onnx.utils import warn_unsupported_attr

@auto_register_import("dequantizelinear")
def import_dequantizelinear(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    #DequantizeLinear is originally an Onnx operator used to dequantize a quantized tensor
    #dequantization uses the following formula : y = (x - x_zero_point) * x_scale
    #Inputs descriptions:
        #x: quantized input tensor
        #y_scale: scaling factor used in the dequantization
        #y_zero_point (optional): zero point used in the dequantization

    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)

    if opset >= 13:
        if 'axis' in onnx_attrs:
            if onnx_attrs['axis'] != 1:
                warn_unsupported_attr('axis','DequantizeLinear',opset,onnx_attrs['axis'])
                return None
            del onnx_attrs['axis']

    if opset >= 21:
        if 'block_size' in onnx_attrs:
            if onnx_attrs['block_size'] != 0:
                warn_unsupported_attr('block_size','DequantizeLinear',opset,onnx_attrs['block_size'])
                return None
            del onnx_attrs['block_size']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'DequantizeLinear' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    #get all the onnx initializers
    quantif_inputs = []
    for idx, inp in enumerate(input_nodes[1:]):
        prod_node = inp[0]
        if prod_node is None:
            Log.warning(f"Input {idx-1} is not available at import time for node dequantizelinear, This node will be filled by a GenericOperator.")
            return None
        quantif_inputs.append(prod_node.get_operator().get_output(0))

    #check if zero point is in the initializers
    has_zero_point = len(quantif_inputs) == 2

    #Nodes creation:
    #Sub(optional) -> Cast -> Mul
    #output dtype of dequantize operator is determined by the scaling factor dtype
    cast_node = aidge_core.Cast(quantif_inputs[0].dtype,
                                node_name+"_cast")
    mul_node = aidge_core.Mul(node_name+"_mul")

    #Nodes connections
    cast_node.add_child(mul_node,0,0)

    #DequantizeLinear inputs must use the following order:
    #input, scaling factor, zero point(optional)
    if has_zero_point:
        #if zero point is especified a sub node will be created
        sub_node = aidge_core.Sub(node_name+"_sub")
        sub_node.add_child(cast_node,0,0)
        ordered_inputs_list = [[sub_node,0],
                               [mul_node,1],
                               [sub_node,1]]
    else:
        #if zero point is not specified
        # its default value is 0 so a sub node is not necessary
        ordered_inputs_list = [[cast_node,0],
                               [mul_node,1]]

    dequantize_graph = aidge_core.get_connected_graph_view(mul_node)
    dequantize_graph.set_ordered_inputs(ordered_inputs_list)

    #metaoperator creation
    dequant_metaop = aidge_core.meta_operator("DequantizeLinear",
                                            dequantize_graph,
                                            name = node_name)

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return dequant_metaop

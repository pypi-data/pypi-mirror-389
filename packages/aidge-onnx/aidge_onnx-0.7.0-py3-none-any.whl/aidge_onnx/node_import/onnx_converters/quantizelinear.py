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
from aidge_onnx.utils import warn_unsupported_attr

from aidge_onnx.dtype_converter import onnx_to_aidge, aidge_to_onnx

@auto_register_import("quantizelinear")
def import_quantizelinear(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    #QuantizeLinear is originally an Onnx operator used to quantize a high precision tensor
    #quantization uses the following formula : y = round(x / y_scale) + y_zero_point
    #Inputs descriptions:
        #x: full precision input tensor
        #y_scale: scaling factor used in the quantization
        #y_zero_point (optional): zero point used in the quantization

    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    cast_output_dtype_onnx = None

    if opset >= 13:
        if 'axis' in onnx_attrs:
            if onnx_attrs['axis'] != 1:
                warn_unsupported_attr('axis','QuantizeLinear',opset,onnx_attrs['axis'])
                return None
            del onnx_attrs['axis']

    if opset >= 19:
        if 'saturate' in onnx_attrs:
            if onnx_attrs['saturate'] != 1:
                warn_unsupported_attr('saturate','QuantizeLinear',opset,onnx_attrs['saturate'])
                return None
            del onnx_attrs['saturate']

    if opset >= 21:
        if 'block_size' in onnx_attrs:
            if onnx_attrs['block_size'] != 0:
                warn_unsupported_attr('block_size','QuantizeLinear',opset,onnx_attrs['block_size'])
                return None
            del onnx_attrs['block_size']

        if 'output_dtype' in onnx_attrs:
            if onnx_attrs['output_dtype'] != 0:
                warn_unsupported_attr('output_dtype','QuantizeLinear',opset,onnx_attrs['output_dtype'])
                return None
            cast_output_dtype_onnx = onnx_attrs['output_dtype']
            del onnx_attrs['output_dtype']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'QuantizeLinear' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    #get all the onnx initializers
    quantif_inputs = []
    for idx, inp in enumerate(input_nodes[1:]):
        prod_node = inp[0]
        if prod_node is None:
            Log.warn(f"Input {idx-1} is not available at import time for node QuantizeLinear, This node will be filled by a GenericOperator.")
            return None
        quantif_inputs.append(prod_node.get_operator().get_output(0))

    #check if zero point is in the initializers
    has_zero_point = len(quantif_inputs) == 2
    zero_point = 0
    #output dtype is determined by zero_point dtype
    if has_zero_point:
        if cast_output_dtype_onnx is not None and onnx_to_aidge(cast_output_dtype_onnx) != quantif_inputs[1].dtype:
            Log.warn(f"Invalid ONNX node for operator QuantizeLinear {node_name}; outputdtype attribute is not equal to zero_point dtype, This node will be filled by a GenericOperator.")
            return None
        if cast_output_dtype_onnx is None:
            cast_output_dtype = quantif_inputs[1].dtype
            cast_output_dtype_onnx = aidge_to_onnx(quantif_inputs[1].dtype)

        if quantif_inputs[1][0] !=0:
            zero_point = quantif_inputs[1][0]
            # Log.warn(f"Zero point value for quantizers on Aidge must be 0 but {quantif_inputs[1]} was received for node {node_name} of type quantizelinear , This node will be filled by a GenericOperator.")
            # return None
    elif cast_output_dtype_onnx is None:
        #if zero point is no specified, default output dtype is uint8
        cast_output_dtype_onnx = onnx.TensorProto.UINT8
        cast_output_dtype = aidge_core.dtype.uint8

    #nodes creation
    clip_ranges = {
        2 : [0, 255],
        3 : [-128, 127],
        4 : [0, 65535],
        5 : [-32768, 32767],
        21 : [0, 15],
        22 : [-8, 7]
    }
    if cast_output_dtype_onnx not in clip_ranges:
        Log.warn(f"Unknown output dtype for node QuantizeLinear. This node will be filled by a GenericOperator.")
        return None
    scale_array = quantif_inputs[0]
    scale_value = scale_array[0]
    if not all([s == scale_value for s in scale_array]):
        Log.warn(f"Aidge currently only support layerwise scaling and not channelwise for QuantizeLinear node. This node will be filled by a GenericOperator.")
        return None

    quantizer_node = aidge_core.Quantizer(
        1/scale_value,
        name=node_name,
        zero_point=zero_point,
        round=True,
        clip_min=clip_ranges[cast_output_dtype_onnx][0],
        clip_max=clip_ranges[cast_output_dtype_onnx][1],
        to_type=cast_output_dtype
    )

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return quantizer_node

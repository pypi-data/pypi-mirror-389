"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional, Dict
import aidge_core
import onnx

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("resize")
def import_resize(onnx_node: onnx.NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """

    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    resize_attrs: Dict = {"axes" : [],
                          "coordinate_transformation_mode" : aidge_core.Interpolation.CoordinateTransformation.HALF_PIXEL,
                          "interpolation_mode" :aidge_core.Interpolation.Mode.ROUND_PREFER_FLOOR,
                          "cubic_coeff_a" : -.75,
                          "extrapolation_value" : 0.0,
                          "padding_mode" : aidge_core.PaddingMode.EDGE,
                          "aspect_ratio" : aidge_core.aspect_ratio.STRETCH ,
                          "antialias" : False,
                          "exclude_outside" : False}

    mode_dict: Dict[str, aidge_core.Interpolation.Mode] = {
        'cubic': aidge_core.Interpolation.Mode.CUBIC,
        'linear': aidge_core.Interpolation.Mode.LINEAR,
        'floor':  aidge_core.Interpolation.Mode.FLOOR,
        'ceil':  aidge_core.Interpolation.Mode.CEIL,
        'round_prefer_floor': aidge_core.Interpolation.Mode.ROUND_PREFER_FLOOR,
        'round_prefer_ceil': aidge_core.Interpolation.Mode.ROUND_PREFER_CEIL
    }

    coord_trans_dict = {
        "half_pixel": aidge_core.Interpolation.CoordinateTransformation.HALF_PIXEL,
        "asymmetric": aidge_core.Interpolation.CoordinateTransformation.ASYMMETRIC,
        "half_pixel_symmetric": aidge_core.Interpolation.CoordinateTransformation.HALF_PIXEL_SYMMETRIC,
        "pytorch_half_pixel": aidge_core.Interpolation.CoordinateTransformation.PYTORCH_HALF_PIXEL,
        "align_corners": aidge_core.Interpolation.CoordinateTransformation.ALIGN_CORNERS,
        "tf_half_pixel_for_nn": aidge_core.Interpolation.CoordinateTransformation.TF_HALF_PIXEL_FOR_NN,
        "tf_crop_and_resize": aidge_core.Interpolation.CoordinateTransformation.TF_CROP_AND_RESIZE
    }

    aspect_ratio_dict: Dict[str, aidge_core.aspect_ratio] = {
        'stretch': aidge_core.aspect_ratio.STRETCH,
        'not_larger': aidge_core.aspect_ratio.NOT_LARGER,
        'not_smaller':  aidge_core.aspect_ratio.NOT_SMALLER
    }

    if 'axes' in onnx_attrs:
        resize_attrs['axes'] = onnx_attrs['axes']
        del onnx_attrs['axes']
    if 'antialias' in onnx_attrs:
        if onnx_attrs['antialias']:
            resize_attrs['antialias'] = True
        del onnx_attrs['antialias']
    if 'cubic_coeff_a' in onnx_attrs:
        resize_attrs['cubic_coeff_a'] = onnx_attrs['cubic_coeff_a']
        del onnx_attrs['cubic_coeff_a']
    if 'extrapolation_value' in onnx_attrs:
        resize_attrs['extrapolation_value'] = onnx_attrs['extrapolation_value']
        del onnx_attrs['extrapolation_value']
    if 'exclude_outside' in onnx_attrs:
        if onnx_attrs['exclude_outside']:
            resize_attrs['exclude_outside'] = True
        del onnx_attrs['exclude_outside']
    if 'keep_aspect_ratio_policy' in onnx_attrs:
        resize_attrs['aspect_ratio'] = aspect_ratio_dict[onnx_attrs['keep_aspect_ratio_policy'].decode()]
        del onnx_attrs['keep_aspect_ratio_policy']

    if 'coordinate_transformation_mode' in onnx_attrs:
        resize_attrs['coordinate_transformation_mode'] = coord_trans_dict[onnx_attrs['coordinate_transformation_mode'].decode()]
        del onnx_attrs['coordinate_transformation_mode']
    if 'mode' in onnx_attrs:
        if onnx_attrs['mode'] == b'nearest':
            if 'nearest_mode' in onnx_attrs:
                resize_attrs['interpolation_mode'] = mode_dict[onnx_attrs['nearest_mode'].decode()]
                del onnx_attrs['nearest_mode']
            else:
                resize_attrs['interpolation_mode'] = mode_dict['floor']
        else:
            resize_attrs['interpolation_mode'] = mode_dict[onnx_attrs['mode'].decode()]
            if 'nearest_mode' in onnx_attrs:
                del onnx_attrs['nearest_mode']
        del onnx_attrs['mode']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator '{onnx_node.op_type}' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    aidge_op = aidge_core.ResizeOp(**resize_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(aidge_op, name = node_name)

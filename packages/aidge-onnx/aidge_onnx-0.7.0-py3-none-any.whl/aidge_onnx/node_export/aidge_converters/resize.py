"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, numpy_helper, TensorProto
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional
from numpy import array


@auto_register_export("Resize")
def export_resize(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs,
) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Resize",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    # Map Aidge attributes to ONNX attributes
    mode_dict_inv = {
        aidge_core.Interpolation.Mode.CUBIC: "cubic",
        aidge_core.Interpolation.Mode.LINEAR: "linear",
        aidge_core.Interpolation.Mode.FLOOR: "floor",
        aidge_core.Interpolation.Mode.CEIL: "ceil",
        aidge_core.Interpolation.Mode.ROUND_PREFER_FLOOR: "round_prefer_floor",
        aidge_core.Interpolation.Mode.ROUND_PREFER_CEIL: "round_prefer_ceil",
    }

    coord_trans_dict_inv = {
        aidge_core.Interpolation.CoordinateTransformation.HALF_PIXEL: "half_pixel",
        aidge_core.Interpolation.CoordinateTransformation.ASYMMETRIC: "asymmetric",
        aidge_core.Interpolation.CoordinateTransformation.HALF_PIXEL_SYMMETRIC: "half_pixel_symmetric",
        aidge_core.Interpolation.CoordinateTransformation.PYTORCH_HALF_PIXEL: "pytorch_half_pixel",
        aidge_core.Interpolation.CoordinateTransformation.ALIGN_CORNERS: "align_corners",
        aidge_core.Interpolation.CoordinateTransformation.TF_HALF_PIXEL_FOR_NN: "tf_half_pixel_for_nn",
        aidge_core.Interpolation.CoordinateTransformation.TF_CROP_AND_RESIZE: "tf_crop_and_resize"
    }

    aspect_ratio_dict_inv = {
        aidge_core.aspect_ratio.STRETCH: 'stretch',
        aidge_core.aspect_ratio.NOT_LARGER: 'not_larger',
        aidge_core.aspect_ratio.NOT_SMALLER: 'not_smaller'
    }

    onnx_attrs = {
        "axes": aidge_operator.attr.get_attr("axes"),
        "coordinate_transformation_mode": coord_trans_dict_inv[
            aidge_operator.attr.get_attr("coordinate_transformation_mode")
        ],
        "mode": "nearest",
        "cubic_coeff_a": aidge_operator.attr.get_attr("cubic_coeff_a"),
        "extrapolation_value": aidge_operator.attr.get_attr("extrapolation_value"),
        "keep_aspect_ratio_policy": aspect_ratio_dict_inv[aidge_operator.attr.get_attr("aspect_ratio")],
        "antialias": int(aidge_operator.attr.get_attr("antialias")),
        "exclude_outside": int(aidge_operator.attr.get_attr("exclude_outside")),
    }

    aidge_mode = aidge_operator.attr.get_attr("interpolation_mode")
    if aidge_mode in [aidge_core.Interpolation.Mode.CUBIC, aidge_core.Interpolation.Mode.LINEAR]:
        onnx_attrs["mode"] = mode_dict_inv[aidge_mode]
    else:
        onnx_attrs["mode"] = "nearest"
        onnx_attrs["nearest_mode"] = mode_dict_inv[aidge_mode]

    if not onnx_attrs["axes"]:
        del onnx_attrs["axes"]

    # # ROI
    # if aidge_node.get_parent(1) is None:
    #     if aidge_operator.get_input(1) is not None:
    #         roi_node_name: str = node_name + "_roi"

    #         roi_tensor = aidge_operator.get_input(1)
    #         roi_onnx_tensor = numpy_helper.from_array(array(roi_tensor), name=roi_node_name)
    #         node_inputs_name[1] = roi_node_name

    #         initializer_list.append(roi_onnx_tensor)

    # # Scales
    # if aidge_operator.get_input(2) is not None and aidge_node.get_parent(2) is None:
    #     scales_node_name: str = node_name + "_scales"

    #     scales_tensor = aidge_operator.get_input(2)
    #     scales_onnx_tensor = numpy_helper.from_array(array(scales_tensor), name=scales_node_name)
    #     node_inputs_name[2] = scales_node_name

    #     # initializer_list.append(scales_onnx_tensor)

    # # Size
    # if aidge_operator.get_input(3) is not None and aidge_node.get_parent(3) is None:
    #     size_node_name: str = node_name + "_size"

    #     size_tensor = aidge_operator.get_input(3)
    #     size_onnx_tensor = numpy_helper.from_array(array(size_tensor), name=size_node_name)
    #     node_inputs_name[3] = size_node_name

    #     initializer_list.append(size_onnx_tensor)


    # Create the ONNX node
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Resize",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
        **onnx_attrs,
    )

    aidge_core.Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")

    return [onnx_node]

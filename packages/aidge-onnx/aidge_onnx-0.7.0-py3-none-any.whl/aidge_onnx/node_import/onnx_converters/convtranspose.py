"""
Copyright (c) 2025 CEA-List

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

@auto_register_import("convtranspose")
def import_convtranspose(
    onnx_node: NodeProto,
    input_nodes: List[Tuple[aidge_core.Node, int]],
    opset: int,
) -> aidge_core.Node:
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
    onnx_default_attrs = {"auto_pad": "NOTSET", "group": 1, "output_padding": 0}
    convtranspose_attrs: dict = {}

    if "kernel_shape" in onnx_attrs:
        kernel_dims = onnx_attrs["kernel_shape"]
        del onnx_attrs["kernel_shape"]
    else:
        # If not present, should be inferred from input W.
        kernel_dims = (
            input_nodes[1][0].get_operator().get_output(input_nodes[1][1]).dims[2:]
        )
    kernel_lenght = len(kernel_dims)  # to prevent reutilisation of len and kerneldims

    ### Only the 2 following attributes differ between different opsets
    if opset is not None and opset >= 11:
        #### Attributes
        #  strides : list of ints (default is 1 along each spatial axis)
        #    Stride along each spatial axis.
        #  dilations : list of ints (default is 1 along each spatial axis)
        #    dilation value along each spatial axis of the filter.

        if "strides" in onnx_attrs:
            convtranspose_attrs["stride_dims"] = onnx_attrs["strides"]
            del onnx_attrs["strides"]
        else:
            # If not present, the stride defaults is 1 along each spatial axis.
            convtranspose_attrs["stride_dims"] = [1] * kernel_lenght

        if "dilations" in onnx_attrs:
            convtranspose_attrs["dilation_dims"] = onnx_attrs["dilations"]
            del onnx_attrs["dilations"]
        else:
            # If not present, the stride defaults is 1 along each spatial axis.
            convtranspose_attrs["dilation_dims"] = [1] * kernel_lenght
    else:
        #### Attributes
        #  strides : list of ints
        #    Stride along each spatial axis.
        #  dilations : list of ints
        #    dilation value along each spatial axis of the filter.
        if "strides" in onnx_attrs:
            convtranspose_attrs["stride_dims"] = onnx_attrs["strides"]
            del onnx_attrs["strides"]

        if "dilations" in onnx_attrs:
            convtranspose_attrs["dilation_dims"] = onnx_attrs["dilations"]
            del onnx_attrs["dilations"]

    #### Attributes
    #  auto_pad : string (default is NOTSET)
    #    auto_pad must be either NOTSET, SAME_UPPER, SAME_LOWER or VALID.
    #    Where default value is NOTSET, which means explicit padding is used.
    #    SAME_UPPER or SAME_LOWER mean pad the input so that `output_shape[i] = ceil(input_shape[i] / strides[i])`
    #    for each axis `i`. The padding is split between the two sides equally or almost equally
    #    (depending on whether it is even or odd). In case the padding is an odd number,
    #    the extra padding is added at the end for SAME_UPPER and at the beginning for SAME_LOWER.
    #  group : int (default is 1)
    #    number of groups input channels and output channels are divided into.
    #  kernel_shape : list of ints (default is inferred from input W)
    #    The shape of the convolution kernel.
    #  pads : list of ints (default is 0 along start and end of each spatial axis)
    #    Padding for the beginning and ending along each spatial axis, it can take any value greater than or equal to 0. The value represent the number of pixels added to the beginning and end part of the corresponding axis. `pads` format should be as follow [x1_begin, x2_begin...x1_end, x2_end,...], where xi_begin the number of pixels added at the beginning of axis `i` and xi_end, the number of pixels added at the end of axis `i`. This attribute cannot be used simultaneously with auto_pad attribute.
    #### Inputs (2 - 3)
    #  X (differentiable) : T
    #    Input data tensor from previous layer; has size (N x C x H x W), where N is the batch size, C is the number of channels, and H and W are the height and width. Note that this is for the 2D image. Otherwise the size is (N x C x D1 x D2 ... x Dn). Optionally, if dimension denotation is in effect, the operation expects input data tensor to arrive with the dimension denotation of [DATA_BATCH, DATA_CHANNEL, DATA_FEATURE, DATA_FEATURE ...].
    #  W (differentiable) : T
    #    The weight tensor that will be used in the convolutions;
    #    has size (M x C/group x kH x kW), where C is the number of channels,
    #    and kH and kW are the height and width of the kernel, and M is the number of feature maps.
    #    For more than 2 dimensions, the kernel shape will be (M x C/group x k1 x k2 x ... x kn),
    #    where (k1 x k2 x ... kn) is the dimension of the kernel. Optionally, if dimension denotation is in effect, the operation expects the weight tensor to arrive with the dimension denotation of [FILTER_OUT_CHANNEL, FILTER_IN_CHANNEL, FILTER_SPATIAL, FILTER_SPATIAL ...]. Assuming zero based indices for the shape array, X.shape[1] == (W.shape[1] * group) == C and W.shape[0] mod G == 0. Or in other words FILTER_IN_CHANNEL multiplied by the number of groups should be equal to DATA_CHANNEL and the number of feature maps M should be a multiple of the number of groups G.
    #  B (optional, differentiable) : T
    #    Optional 1D bias to be added to the convolution, has size of M.
    #### Outputs
    #  Y (differentiable) : T
    #    Output data tensor that contains the result of the convolution.
    #    The output dimensions are functions of the kernel size, stride size, and pad lengths.

    # group is 1 by default
    group = 1
    if "group" in onnx_attrs:
        group = onnx_attrs["group"]
        del onnx_attrs["group"]

    convtranspose_attrs["padding_dims"] = [0] * 2 * kernel_lenght
    if "pads" in onnx_attrs:
        # `pads` format should be as follow [x1_begin, x2_begin...x1_end, x2_end,...]
        for i in range(0, kernel_lenght):
            convtranspose_attrs["padding_dims"][2 * i] = onnx_attrs["pads"][i]
            convtranspose_attrs["padding_dims"][2 * i + 1] = onnx_attrs["pads"][
                kernel_lenght + i
            ]
        del onnx_attrs["pads"]

    auto_pad = onnx_attrs.get("auto_pad", onnx_default_attrs["auto_pad"])
    if auto_pad in (
        b"NOTSET",
        b"SAME_UPPER",
        b"SAME_LOWER",
        b"VALID",
    ):
        if (
            onnx_attrs["auto_pad"] != b"NOTSET"
            and np.count_nonzero(convtranspose_attrs["padding_dims"]) > 0
        ):
            raise RuntimeError(
                "Error: malformed ONNX: cannot have both non-zero 'pads' and 'auto_pad' different from 'NOTSET' for ConvTranspose operator."
            )

        nb_feature = len(kernel_dims)
        for i, ele in enumerate(kernel_dims):
            padding = ele - convtranspose_attrs["stride_dims"][i]
            nb_same_padding = padding // 2
            floor_half_hadding = padding % 2

            if onnx_attrs["auto_pad"] == b"SAME_UPPER":
                convtranspose_attrs["padding_dims"][i] = (
                    nb_same_padding + floor_half_hadding
                )
                convtranspose_attrs["padding_dims"][i + nb_feature] = nb_same_padding
            elif onnx_attrs["auto_pad"] == b"SAME_LOWER":
                convtranspose_attrs["padding_dims"][i] = nb_same_padding
                convtranspose_attrs["padding_dims"][i + nb_feature] = (
                    nb_same_padding + floor_half_hadding
                )
        del onnx_attrs["auto_pad"]

    if len(onnx_attrs) > 0:
        Log.warn(
            f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'ConvTranspose' with opset {opset}.\nThis node will be filled by a GenericOperator."
        )
        return None

    if group == 1:
        op_aidge_class_name = f"ConvTranspose{kernel_lenght}D"
        op_aidge_constr_name = f"ConvTranspose{kernel_lenght}DOp"
    else:
        raise RuntimeError("Error: ConvTranspose DepthWise is not supported yet.")

    if np.count_nonzero(convtranspose_attrs["padding_dims"]) > 0:
        # if padding_dims values are different from 0 then a padded convtranspose will be made
        op_aidge_class_name = "Padded" + op_aidge_class_name
        op_aidge_constr_name = "Padded" + op_aidge_constr_name
    else:
        del convtranspose_attrs["padding_dims"]

    if op_aidge_class_name in dir(aidge_core):
        aidge_op = aidge_core.__getattribute__(op_aidge_constr_name)(
            kernel_dims, **convtranspose_attrs
        )
    else:
        Log.warn(
            f"Warning: {op_aidge_class_name} is not supported in Aidge. This node will be filled by a GenericOperator."
        )
        return None

    Log.info(
        f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]"
    )
    return aidge_core.Node(aidge_op, name=node_name)

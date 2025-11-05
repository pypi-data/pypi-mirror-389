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


@auto_register_import("gridsample")
def import_gridsample(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    aidge_attrs: dict = {"name" : node_name}

    if "align_corners" in onnx_attrs:
        aidge_attrs["align_corners"] = bool(onnx_attrs["align_corners"])
        del onnx_attrs["align_corners"]
    else:
        aidge_attrs["align_corners"] = False

    if "mode" in onnx_attrs:
        onnx_attrs["mode"] = onnx_attrs["mode"].decode('utf-8')
        if onnx_attrs["mode"] == "linear":
            aidge_attrs["mode"] = "linear"
        elif onnx_attrs["mode"] == "nearest":
            aidge_attrs["mode"] = "nearest"
        elif onnx_attrs["mode"] == "cubic":
            aidge_attrs["mode"] = "cubic"
        elif onnx_attrs["mode"] == "bicubic":
            aidge_attrs["mode"] = "cubic" # Note: Bi-Cubic is just Cubic with 2D grid
        else:
            Log.warn(f"Warning: unsupported value: {onnx_attrs['mode']} for attribute mode of operator 'GridSample' with opset {opset}.\nThis node will be filled by a GenericOperator.")
            return None
        del onnx_attrs["mode"]
    else:
        if opset < 20:
            Log.warn(f"Warning: unsupported value: bilinear for attribute mode of operator 'GridSample' with opset {opset}.\nThis node will be filled by a GenericOperator.")
            return None
        # Default value is linear since opset 20 but was BiLinear when introduced in 16
        aidge_attrs["mode"] = "linear"

    if "padding_mode" in onnx_attrs:
        onnx_attrs["padding_mode"] = onnx_attrs["padding_mode"].decode('utf-8')
        if onnx_attrs["padding_mode"] == "zeros":
            aidge_attrs["padding_mode"] = "zeros"
        elif onnx_attrs["padding_mode"] == "border":
            aidge_attrs["padding_mode"] = "border"
        elif onnx_attrs["padding_mode"] == "reflection":
            aidge_attrs["padding_mode"] = "reflection"
        else:
            Log.warn(f"Warning: unsupported value: {onnx_attrs['padding_mode']} for attribute mode of operator 'GridSample' with opset {opset}.\nThis node will be filled by a GenericOperator.")
            return None
        del onnx_attrs["padding_mode"]
    else:
        # Default value is linear since opset 20 but was BiLinear when introduced in 16
        aidge_attrs["padding_mode"] = aidge_core.GridSample.padding_mode.Zeros

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'GridSample' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    aidge_node = aidge_core.GridSample(**aidge_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_node

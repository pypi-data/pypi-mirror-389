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
from aidge_core import PaddingMode

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log


@auto_register_import("pad")
def import_slice(
    onnx_node: NodeProto,
    input_nodes: List[Tuple[aidge_core.Node, int]],
    opset: int,
) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.output[0]
    mode_map = {
        b"constant": PaddingMode.CONSTANT,
        b"edge": PaddingMode.EDGE,
        b"reflect": PaddingMode.REFLECT,
        b"wrap": PaddingMode.WRAP,
    }
    onnx_attrs = get_node_attributes(onnx_node, opset)
    pad_attrs: dict = {"mode": PaddingMode.CONSTANT}

    if 'mode' in onnx_attrs and onnx_attrs["mode"] in mode_map:
        pad_attrs['mode'] = mode_map[onnx_attrs["mode"]]
        del onnx_attrs['mode']

    # Opset < 11
    if 'paddings' in onnx_attrs:
        pad_attrs['pads'] = onnx_attrs["paddings"]
        del onnx_attrs['paddings']

    # Opset < 11
    if 'value' in onnx_attrs:
        pad_attrs['constant_value'] = aidge_core.Tensor(onnx_attrs["value"])
        del onnx_attrs['value']

    if (len(onnx_attrs) > 0):
        Log.warn(f"Warning: Attribute {onnx_attrs.keys()} is not supported for operator Pad.")
        return None

    pad_node = aidge_core.Pad(**pad_attrs, name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return pad_node

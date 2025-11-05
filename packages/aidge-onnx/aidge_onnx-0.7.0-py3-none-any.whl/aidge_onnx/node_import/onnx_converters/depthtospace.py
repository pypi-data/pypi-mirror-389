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


@auto_register_import("depthtospace")
def import_dtp(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    aidge_attrs: dict = {"name" : node_name}

    if opset >= 11:
        if "mode" in onnx_attrs:
            onnx_attrs["mode"] = onnx_attrs["mode"].decode('utf-8')
            if onnx_attrs["mode"] == "DCR":
                aidge_attrs["mode"] = "DCR"
            elif onnx_attrs["mode"] == "CRD":
                aidge_attrs["mode"] = "CRD"
            else:
                Log.warn(f"Warning: unsupported value: {onnx_attrs['mode']} for attribute mode of operator 'DepthToSpace' with opset {opset}.\nThis node will be filled by a GenericOperator.")
                return None
            del onnx_attrs["mode"]
        else:
            # ONNX default value since opset 11 which introduce this attribute
            aidge_attrs["mode"] = "DRC"

    if "blocksize" in onnx_attrs:
        aidge_attrs["block_size"] = onnx_attrs["blocksize"]
        del onnx_attrs["blocksize"]
    else:
        Log.warn(f"Warning: attribute blocksize is mandatory for DepthToSpace with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Slice' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    aidge_node = aidge_core.DepthToSpace(**aidge_attrs)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_node

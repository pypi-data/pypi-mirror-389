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

@auto_register_import("gemm")
def import_gemm(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
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
    gemm_attrs: dict = {'alpha':1.0, 'beta':1.0, 'transA':0, 'transB':0}

    if "alpha" in onnx_attrs:
        gemm_attrs["alpha"] = onnx_attrs["alpha"]
        del onnx_attrs["alpha"]

    if "beta" in onnx_attrs:
        gemm_attrs["beta"] = onnx_attrs["beta"]
        del onnx_attrs["beta"]

    if "transA" in onnx_attrs:
        gemm_attrs["transA"] = onnx_attrs["transA"]
        del onnx_attrs["transA"]

    if "transB" in onnx_attrs:
        # Aidge expects W to be already transposed
        gemm_attrs["transB"] = 1 - onnx_attrs["transB"]
        del onnx_attrs["transB"]

    if opset < 7 and "broadcast" in onnx_attrs:
        warn_unsupported_attr("broadcast","Gemm",opset,onnx_attrs["broadcast"])
        return None

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Gemm' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    bias = None
    if len(input_nodes) >= 3 and input_nodes[2] is not None:
        bias = input_nodes[2][0].get_operator().get_output(0)
        bias_dims = bias.dims

    # In Aidge bias should be None or with 1 dims
    if bias is not None and len(bias_dims) !=1:
        if len(bias_dims) == 2 and bias_dims[0] == 1:
            # Case bias.dims = [1, N]
            bias.resize([bias_dims[1]])
        else:
            Log.warn(f"Warning: cannot import bias of dims: {bias_dims} for operator 'Gemm' with opset {opset}.\nThis node will be filled by a GenericOperator.")
            return None

    # Avoid metaop if only fc is needed
    if not gemm_attrs["transA"] and not gemm_attrs["transB"] and gemm_attrs["alpha"]==1.0 and gemm_attrs["beta"]==1.0:
        fc_node = aidge_core.Node(aidge_core.FCOp(), name=node_name)
        Log.notice(f"- {node_name} ({onnx_node.op_type})")
        return fc_node

    if "Gemm" not in dir(aidge_core):
        Log.warn(f"Cannot support gemm operator. This node will be filled by a GenericOperator.")
        return None
    fc_op = aidge_core.__getattribute__("GemmOp")(**gemm_attrs)
    fc_node = aidge_core.Node(fc_op, name=node_name)
    Log.notice(f"- {node_name} ({onnx_node.op_type})")
    return fc_node

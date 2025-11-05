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

@auto_register_import("lrn")
def import_lrn(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
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
    lrn_alpha = 0.0001
    lrn_beta = 0.75
    lrn_bias = 1.0
    lrn_size = 0

    if 'alpha' in onnx_attrs:
        lrn_alpha = onnx_attrs['alpha']
        del onnx_attrs['alpha']

    if 'beta' in onnx_attrs:
        lrn_beta = onnx_attrs['beta']
        del onnx_attrs['beta']

    if 'bias' in onnx_attrs:
        lrn_bias = onnx_attrs['bias']
        del onnx_attrs['bias']

    if 'size' in onnx_attrs:
        lrn_axis = onnx_attrs['size']
        del onnx_attrs['size']
    else:
        Log.warn(f"Could not find attribute size for operator LRN with opset {opset}")
        return None

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'LRN' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    my_op = aidge_core.LRNOp(lrn_size)
    my_op.attr.alpha = lrn_alpha
    my_op.attr.beta = lrn_beta
    my_op.attr.bias = lrn_bias
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(my_op, name = node_name)

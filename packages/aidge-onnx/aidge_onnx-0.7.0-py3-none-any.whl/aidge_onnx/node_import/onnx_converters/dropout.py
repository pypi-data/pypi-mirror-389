"""
Copyright (c) 2025 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional

import aidge_core
import numpy as np
import onnx
from onnx import NodeProto

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("dropout")
def import_dropout(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Optional opset version
    :type opset: int
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)

    dropout_attrs: dict = {'probability': 0.5}

    if opset > 11:
        if 'seed' in onnx_attrs:
            dropout_attrs['seed'] = onnx_attrs['seed']
            del onnx_attrs['seed']
        if 'training_mode' in onnx_attrs:
            dropout_attrs['training_mode'] = onnx_attrs['training_mode']
            del onnx_attrs['training_mode']

    if opset is None or opset < 11:
        if 'ratio' in onnx_attrs:
            dropout_attrs['probability'] = onnx_attrs['ratio']
            del onnx_attrs['ratio']
    else:
        if len(input_nodes) > 1 and input_nodes[1] is not None:
            prob_arr = np.array(input_nodes[1][0].get_operator().get_output(input_nodes[1][1]))
            if len(prob_arr) is not 1:
                Log.warning(f"Input#1 (probability) must be a scalar tensor, a {len(prob_arr)} elements tensor was given, This node will be filled by a GenericOperator.")
                return None 
            dropout_attrs['probability'] =  prob_arr.flat[0]

    if opset < 7:
        if 'is_test' in onnx_attrs:
            dropout_attrs['training_mode'] = int(not onnx_attrs['is_test'])
            del onnx_attrs['is_test']


    my_op = aidge_core.DropoutOp(**dropout_attrs)
    dropout_node = aidge_core.Node(my_op, name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    Log.info(f"- {node_name} ({onnx_node.op_type})")
    return dropout_node
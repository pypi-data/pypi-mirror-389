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
import numpy as np
from aidge_onnx.node_import import auto_register_import
from onnx import numpy_helper, NodeProto
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log

@auto_register_import("constant")
def import_constant(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
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

    prod = None

    if 'value' in onnx_attrs:
        prod = aidge_core.Producer(aidge_core.Tensor(numpy_helper.to_array(onnx_attrs['value'])), node_name, True)
        del onnx_attrs['value']
    elif 'value_int' in onnx_attrs:
        prod = aidge_core.Producer(aidge_core.Tensor(np.array(onnx_attrs['value_int'], dtype=np.int64)), node_name, True)
        del onnx_attrs['value_int']
    elif 'value_ints' in onnx_attrs:
        prod = aidge_core.Producer(aidge_core.Tensor(np.array(list(onnx_attrs['value_ints']), dtype=np.int64)), node_name, True)
        del onnx_attrs['value_ints']
    elif 'value_float' in onnx_attrs:
        prod = aidge_core.Producer(aidge_core.Tensor(np.array(onnx_attrs['value_float'], dtype=np.float32)), node_name, True)
        del onnx_attrs['value_float']
    elif 'value_floats' in onnx_attrs:
        prod = aidge_core.Producer(aidge_core.Tensor(np.array(list(onnx_attrs['value_floats']), dtype=np.float32)), node_name, True)
        del onnx_attrs['value_floats']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported or extra attribute(s): {onnx_attrs.keys()} for operator 'Constant' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return prod

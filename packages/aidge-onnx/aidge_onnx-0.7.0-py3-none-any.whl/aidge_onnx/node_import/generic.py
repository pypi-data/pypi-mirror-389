"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional

import onnx
import aidge_core
from aidge_core import Log
# Removed import of ConverterType to avoid circular dependency

def import_generic(onnx_node: onnx.NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int = 0) -> Optional[aidge_core.Node]:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of tuple of Aidge nodes with their output index, which constitute the input of the current node
    :type input_nodes: List[Tuple[aidge_core.Node, int]]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    generic_node = aidge_core.GenericOperator(onnx_node.op_type, len(input_nodes), len(onnx_node.input) - len(input_nodes), len(onnx_node.output), node_name)
    operator = generic_node.get_operator()

    for onnx_attribute in onnx_node.attribute:
        operator.attr.add_attr(onnx_attribute.name, onnx.helper.get_attribute_value(onnx_attribute))

    # TODO : Add verbose parameter somewhere to avoid those logs ...
    # TODO : Add a toString method to genericOperator
    message = f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m] as a GenericOperator.\n"
    for param_name in operator.attr.dict().keys():
        param_value = str(operator.attr.get_attr(param_name))
        param_value = (param_value[:75] + '...') if len(param_value) > 75 else param_value
        message += f"\t* {param_name} : {param_value}\n"
    Log.notice(message)
    return generic_node

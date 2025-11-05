"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional
from aidge_onnx import dtype_converter
import numpy as np
def fail_export(msg):
    aidge_core.Log.warn(msg)
    return None

@auto_register_export("LayerNorm")
def export_layernorm(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    if opset < 17:
        fail_export(f"LayerNorm has been introduced with opset 17, cannot export a network with LayerNorm in opset {opset}")
    epsilon = None
    axis = -1
    aidge_operator = aidge_node.get_operator()
    if not aidge_operator.attr.epsilon:
        fail_export("Missing LayerNorm mandatory attribute epsilon.")
    else:
        epsilon = aidge_operator.attr.epsilon
    if aidge_operator.attr.axis:
        axis = aidge_operator.attr.axis

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="LayerNormalization",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
        helper.make_attribute(
            "epsilon",
            epsilon
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "axis",
            axis
    ))

    return [onnx_node]

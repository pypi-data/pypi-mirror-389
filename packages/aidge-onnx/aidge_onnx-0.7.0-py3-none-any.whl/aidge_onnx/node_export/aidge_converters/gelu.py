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

def fail_export(msg):
    aidge_core.Log.warn(msg)
    return None

@auto_register_export("GeLU")
def export_gelu(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    approximate = "none"
    aidge_operator = aidge_node.get_operator()
    if aidge_operator.attr.has_attr("approximate"):
        approximate = aidge_operator.attr.get_attr("approximate")

    if len(node_inputs_name) != 1:
        return fail_export(f"Expected one input for GeLU, got {len(node_inputs_name)}.")

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Gelu",
        inputs=node_inputs_name, # Both inputs are the same
        outputs=node_outputs_name,
        approximate=approximate
    )

    return [onnx_node]

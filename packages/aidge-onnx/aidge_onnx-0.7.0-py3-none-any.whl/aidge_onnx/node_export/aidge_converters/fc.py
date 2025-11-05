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

@auto_register_export("FC")
def export_fc(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    onnx_nodes = []

    #If bias not set, remove bias as an input
    if aidge_node.input(2)[0] and not aidge_node.input(2)[0].get_operator().get_output(0).has_impl():
        node_inputs_name.remove(aidge_node.input(2)[0].name()+"_out0")

    # If input is not flatten, add a Flatten node
    if aidge_node.get_operator().get_input(0):
        if(len(aidge_node.get_operator().get_input(0).dims) != 2):
            flatten_name = f"{aidge_node.name()}_flatten"
            flatten_out = f"{flatten_name}_out_0"

            onnx_node = helper.make_node(
                name=flatten_name,
                op_type="Flatten",
                inputs=[node_inputs_name[0]],
                outputs=[flatten_out],
            )
            onnx_node.attribute.append(helper.make_attribute("axis", 1))

            onnx_nodes.append(onnx_node)
            node_inputs_name[0] = flatten_out

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Gemm",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(helper.make_attribute("transB", 1))

    onnx_nodes.append(onnx_node)
    return onnx_nodes

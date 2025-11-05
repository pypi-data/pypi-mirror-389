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

@auto_register_export("Gather")
def export_gather(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    aidge_operator = aidge_node.get_operator()
    onnx_nodes = []
    # Input 1 (Indices) is optional in aidge but mandatory in ONNX.
    if aidge_node.get_operator().get_input(1) is None:
        # No producer input for indices, create a constant node
        indices_node = helper.make_node(
            name=f"{node_inputs_name[1]}_constant",
            op_type="Constant",
            inputs=[],
            outputs=[node_inputs_name[1]],
        )
        nb_indices = len(aidge_operator.attr.indices)
        indices_node.attribute.append(
            helper.make_attribute(
                "value",
                helper.make_tensor(
                    f"{node_inputs_name[1]}_tensor",
                    TensorProto.INT64,
                    [nb_indices] if nb_indices!=1 else [], # Note: Allow a better netron representation
                    aidge_operator.attr.indices
            )
        ))

        onnx_nodes.append(indices_node)

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Gather",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )


    onnx_node.attribute.append(
        helper.make_attribute(
            "axis",
            aidge_operator.attr.get_attr("axis")
    ))
    onnx_nodes.append(onnx_node)
    return onnx_nodes

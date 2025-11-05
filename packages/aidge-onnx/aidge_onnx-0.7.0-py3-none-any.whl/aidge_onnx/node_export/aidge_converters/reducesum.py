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

@auto_register_export("ReduceSum")
def export_reducemean(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:
    aidge_operator = aidge_node.get_operator()
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="ReduceSum",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    onnx_node.attribute.append(
        helper.make_attribute(
            "axes",
            aidge_operator.attr.get_attr("axes")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "keepdims",
            aidge_operator.attr.get_attr("keep_dims")
    ))

    if opset > 17 :
        onnx_node.attribute.append(
            helper.make_attribute(
                "noop_with_empty_axes",
                aidge_operator.attr.get_attr("noop_with_empty_axes")
        ))
    return [onnx_node]

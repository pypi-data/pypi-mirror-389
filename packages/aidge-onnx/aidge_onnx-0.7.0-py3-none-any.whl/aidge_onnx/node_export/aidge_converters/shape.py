"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional

@auto_register_export("Shape")
def export_gather(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    aidge_operator = aidge_node.get_operator()
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Shape",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    if opset >= 15:
        onnx_node.attribute.append(
            helper.make_attribute(
                "start",
                aidge_operator.attr.get_attr("start")
        ))
        if aidge_operator.attr.get_attr("end") != -1:
            # Note: end -is the default value for Aidge:
            # With expected output
            # NCHW -> [N, C, H, W]
            # But ONNX will return
            # NCHW -> [N, C, H]
            # To have the expected output, we need to not
            # set end, which is the ONNX default value!
            onnx_node.attribute.append(
                helper.make_attribute(
                    "end",
                    aidge_operator.attr.get_attr("end")
            ))
    return [onnx_node]

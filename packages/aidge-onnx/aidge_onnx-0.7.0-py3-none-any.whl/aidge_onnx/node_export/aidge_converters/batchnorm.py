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

@auto_register_export("BatchNorm1D", "BatchNorm2D", "BatchNorm3D")
def export_batchnorm(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="BatchNormalization",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
        helper.make_attribute(
            "momentum",
            aidge_operator.attr.get_attr("momentum")
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "epsilon",
            aidge_operator.attr.get_attr("epsilon")
    ))
    if opset >= 14:
        onnx_node.attribute.append(
            helper.make_attribute(
                "training_mode",
                aidge_operator.attr.get_attr("training_mode")
        ))
    if opset < 9:
        onnx_node.attribute.append(
            helper.make_attribute(
                "spatial",
                1
        ))
    return [onnx_node]

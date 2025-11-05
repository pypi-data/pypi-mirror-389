"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Optional

from numpy import isnan
from onnx import helper
from onnx.onnx_pb import AttributeProto

import aidge_core
from aidge_onnx.node_export import auto_register_export
from aidge_onnx.dtype_converter import aidge_to_onnx

@auto_register_export("RandomNormalLike")
def export_random_normal_like(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="RandomNormalLike",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    onnx_node.attribute.append(
        helper.make_attribute(
            "mean",
            aidge_operator.attr.mean,
            attr_type=AttributeProto.FLOAT
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "scale",
            aidge_operator.attr.scale,
            attr_type=AttributeProto.FLOAT
    ))

    if (not isnan(aidge_operator.attr.seed)):
        onnx_node.attribute.append(
            helper.make_attribute(
                "seed",
                aidge_operator.attr.seed,
                attr_type=AttributeProto.FLOAT
        ))

    if (aidge_operator.attr.dtype != aidge_core.dtype.any):
        onnx_node.attribute.append(
            helper.make_attribute(
                "dtype",
                aidge_to_onnx(aidge_operator.attr.dtype),
                attr_type=AttributeProto.INT
        ))
    return [onnx_node]

"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Optional

import onnx
from onnx import helper, TensorProto

import aidge_core
from aidge_onnx.node_export import auto_register_export
from aidge_onnx import dtype_converter
import numpy as np

@auto_register_export("ConstantOfShape")
def export_constantofshape(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    aidge_operator = aidge_node.get_operator()
    aidge_value_attr: aidge_core.Tensor = aidge_operator.attr.value
    np_value_attr = np.array(aidge_value_attr)

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="ConstantOfShape",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    onnx_node.attribute.append(
        helper.make_attribute(
            "value",
            helper.make_tensor(
                name = f"{aidge_node.name()}_constant",
                data_type = dtype_converter.numpy_to_onnx(np_value_attr.dtype),
                dims = (1,), #np_value_attr.shape,
                vals = np_value_attr.flatten().tolist()
        )
    ))
    return [onnx_node]


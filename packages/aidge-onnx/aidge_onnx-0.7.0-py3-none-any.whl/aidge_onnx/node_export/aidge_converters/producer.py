"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
import numpy as np
from typing import List, Optional
from aidge_onnx.node_export import auto_register_export
from aidge_onnx import dtype_converter


@auto_register_export("Producer")
def export_producer(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:
    """
    Export a Constant producer node.

    :param aidge_node: The Aidge node representing a constant.
    :param node_inputs_name: List of input names.
    :param node_outputs_name: List of output names.
    :param opset: ONNX opset version (optional).
    :param kwargs: Additional arguments.
    :return: A list containing the ONNX Constant node.
    """
    aidge_operator = aidge_node.get_operator()

    # Non constant producer are handled by ONNX initializers which are created aprt in onnx_export.py
    if not aidge_operator.attr.get_attr("constant"):
        raise ValueError("Initializer operator has not been catched when creating Initializers.")

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Constant",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    np_value = np.array(aidge_operator.get_output(0))

    onnx_node.attribute.append(
        helper.make_attribute(
            "value",
            helper.make_tensor(
                f"{aidge_node.name()}_constant",
                dtype_converter.numpy_to_onnx(np_value.dtype),
                np_value.shape,
                np_value.flatten().tolist()
        )
    ))

    return [onnx_node]

"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper, TensorProto
import numpy as np
from aidge_onnx.node_export import auto_register_export
from aidge_onnx import dtype_converter
from typing import List, Optional

@auto_register_export("Pad")
def export_pad(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:

    pad_op = aidge_node.get_operator()

    mode =  pad_op.attr.mode.name.lower()

    node_list = []

    if len(node_inputs_name) < 4:
        node_inputs_name.extend([''] * (4 - len(node_inputs_name)))

    if aidge_node.get_parent(1) == None:
        pads_tensor = helper.make_tensor('pads', TensorProto.INT64, [len(pad_op.attr.pads)], pad_op.attr.pads)
        tensor_name = f"{aidge_node.name()}_pads_output_0"

        onnx_node_pads = helper.make_node(
            name=f"{aidge_node.name()}_pads",
            op_type="Constant",
            inputs=[],
            outputs=[tensor_name],
        )
        onnx_node_pads.attribute.append(
            helper.make_attribute(
                "value",
                pads_tensor
        ))

        node_inputs_name[1] = tensor_name
        node_list += [onnx_node_pads]

    if aidge_node.get_parent(2) == None and pad_op.attr.mode == aidge_core.PaddingMode.CONSTANT:
        tensor_name = f"{aidge_node.name()}_constant_value_output_0"
        onnx_node_constant = helper.make_node(
            name=f"{aidge_node.name()}_constant_value",
            op_type="Constant",
            inputs=[],
            outputs=[tensor_name],
        )

        np_value = np.array(pad_op.attr.constant_value)

        onnx_node_constant.attribute.append(
            helper.make_attribute(
                "value",
                helper.make_tensor(
                    f"{aidge_node.name()}_constant",
                    dtype_converter.numpy_to_onnx(np_value.dtype),
                    np_value.shape,
                    np_value.flatten().tolist()
            )
        ))

        node_inputs_name[2] = tensor_name
        node_list += [onnx_node_constant]

    if aidge_node.get_parent(3) == None and len(pad_op.attr.axes) > 0:
        axes_tensor = helper.make_tensor('axes', TensorProto.INT64, [len(pad_op.attr.axes)], pad_op.attr.axes)
        tensor_name = f"{aidge_node.name()}_axes_output_0"

        onnx_node_axes = helper.make_node(
            name=f"{aidge_node.name()}_axes",
            op_type="Constant",
            inputs=[],
            outputs=[tensor_name],
        )
        onnx_node_axes.attribute.append(
            helper.make_attribute(
                "value",
                axes_tensor
        ))

        node_inputs_name[3] = tensor_name
        node_list += [onnx_node_axes]

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Pad",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
    helper.make_attribute(
        "mode",
        mode
    ))

    node_list = [onnx_node] + node_list
    return node_list

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
import numpy as np
from aidge_onnx import dtype_converter


@auto_register_export("ReduceMean")
def export_reducemean(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:
    onnx_nodes  = []
    aidge_operator = aidge_node.get_operator()
    if opset > 17:
        axes_node_name = f"{aidge_node.name()}_axes"
        axes_node = helper.make_node(
                name=f"{axes_node_name}",
                op_type="Constant",
                inputs=[],
                outputs=[f"{axes_node_name}_0"],
            )
        np_value = np.array(aidge_operator.attr.axes)
        axes_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{axes_node_name}_tensor",
                        dtype_converter.numpy_to_onnx(np_value.dtype),
                        np_value.shape,
                        np_value.flatten().tolist()
                    )
                )
            )
        node_inputs_name.append(f"{axes_node_name}_0")
        onnx_nodes.append(axes_node)

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="ReduceMean",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    if opset < 18:
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
    onnx_nodes.append(onnx_node)
    return onnx_nodes

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

@auto_register_export("Squeeze")
def export_squeeze(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    """
    Export a Squeeze node.

    :param aidge_node: The Aidge node to export.
    :param node_inputs_name: List of input names.
    :param node_outputs_name: List of output names.
    :param opset: ONNX opset version (optional).
    :param kwargs: Additional arguments.
    :return: A list of ONNX NodeProto nodes.
    """
    aidge_operator = aidge_node.get_operator()
    onnx_nodes = []
    if opset is not None and opset < 13:
        if aidge_node.get_operator().get_input(1) is not None:
            # TODO: Implement the case where axes is a producer
            NotImplementedError("No support for Squeeze with axes as a producer for opset < 13")
        del node_inputs_name[1]

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Squeeze",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    if opset is not None and opset < 13:
        if aidge_operator.attr.axes != []:
            # Note: axes is optional in Squeeze
            onnx_node.attribute.append(
                helper.make_attribute(
                    "axes",
                    # Note: looks like this function only check attributes
                    # so may not work if axes is a producer.
                    aidge_operator.attr.axes
            ))
    else:
        # If axes is a producer, nothing to do
        # But if it is none we need to create a constant node
        # With the attribute value!
        if aidge_node.get_operator().get_input(1) is None:
            # No producer input for indices, create a constant node
            axes_node = helper.make_node(
                name=f"{node_inputs_name[1]}_constant",
                op_type="Constant",
                inputs=[],
                outputs=[node_inputs_name[1]],
            )
            nb_axes = len(aidge_operator.attr.axes)
            axes_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{node_inputs_name[1]}_tensor",
                        TensorProto.INT64,
                        [nb_axes] if nb_axes!=1 else [], # Note: Allow a better netron representation
                        aidge_operator.attr.axes
                )
            ))

        onnx_nodes.append(axes_node)
    onnx_nodes.append(onnx_node)
    return onnx_nodes



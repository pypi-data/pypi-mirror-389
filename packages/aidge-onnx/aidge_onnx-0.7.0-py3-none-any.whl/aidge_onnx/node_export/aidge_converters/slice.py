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

@auto_register_export("Slice")
def export_slice(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:
    """
    Export a Slice node.

    :param aidge_node: The Aidge node to export.
    :param node_inputs_name: List of input names.
    :param node_outputs_name: List of output names.
    :param opset: ONNX opset version (optional).
    :param kwargs: Additional arguments.
    :return: A list of ONNX NodeProto nodes.
    """
    aidge_operator = aidge_node.get_operator()
    onnx_nodes = []
    if opset is not None and opset < 10:
        if aidge_node.get_operator().get_input(3) is not None:
            # TODO: Implement the case where axes is a producer
            NotImplementedError("No support for Slice with axes as a producer for opset < 10")
        else:
            aidge_core.Log.debug(f"Removing {node_inputs_name[3]} input for Slice node {aidge_node.name()}")
            del node_inputs_name[3]
        if aidge_node.get_operator().get_input(4) is not None:
            # TODO: Implement the case where steps is a producer
            NotImplementedError("No support for Slice with steps as a producer for opset < 10")
        else:
            aidge_core.Log.debug(f"Removing {node_inputs_name[4]} input for Slice node {aidge_node.name()}")
            del node_inputs_name[4]

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Slice",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    if opset is not None and opset < 10:
        aidge_core.Log.debug("Setting axes and steps as attributes")
        onnx_node.attribute.append(
            helper.make_attribute(
                "axes",
                # Note: looks like this function only check attributes
                # so may not work if axes is a producer.
                aidge_operator.attr.axes
        ))
        onnx_node.attribute.append(
            helper.make_attribute(
                "steps",
                # Note: looks like this function only check attributes
                # so may not work if axes is a producer.
                aidge_operator.attr.steps
        ))
    else:
        # If axes and steps are producers, nothing to do
        # But if it is none we need to create a constant node
        # With the attribute value!
        if (
            aidge_operator.attr.axes
            and aidge_node.get_operator().get_input(3) is None
        ):
            aidge_core.Log.debug(f"Creating constant node for axes attribute in Slice node {aidge_node.name()}")
            # No producer input for indices, create a constant node
            axes_node = helper.make_node(
                name=f"{node_inputs_name[3]}_constant",
                op_type="Constant",
                inputs=[],
                outputs=[node_inputs_name[3]],
            )
            axes_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{node_inputs_name[3]}_tensor",
                        TensorProto.INT64,
                        [len(aidge_operator.attr.axes)],
                        aidge_operator.attr.axes
                )
            ))
            onnx_nodes.append(axes_node)

        if (
            aidge_operator.attr.steps
            and aidge_node.get_operator().get_input(4) is not None
        ):
            aidge_core.Log.debug(f"Creating constant node for steps attribute in Slice node {aidge_node.name()}")
            # No producer input for indices, create a constant node
            axes_node = helper.make_node(
                name=f"{node_inputs_name[4]}_constant",
                op_type="Constant",
                inputs=[],
                outputs=[node_inputs_name[4]],
            )
            axes_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{node_inputs_name[4]}_tensor",
                        TensorProto.INT64,
                        [len(aidge_operator.attr.steps)],
                        aidge_operator.attr.steps
                )
            ))
            onnx_nodes.append(axes_node)

    onnx_nodes.append(onnx_node)
    return onnx_nodes

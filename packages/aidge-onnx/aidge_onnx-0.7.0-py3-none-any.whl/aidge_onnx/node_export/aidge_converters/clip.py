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
from aidge_onnx import dtype_converter
from typing import List, Optional

def get_in_dtype(aidge_op):
    if aidge_op.get_input(0):
        return aidge_op.get_input(0).dtype
    else:
        raise ValueError("Clip node does not have an input cannot determine min and max type.")

@auto_register_export("Clip")
def export_clip(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    """
    Export the Clip operation from Aidge to ONNX.

    :param aidge_node: Aidge node to convert
    :type aidge_node: aidge_core.Node
    :param node_inputs_name: List of input names for the ONNX node
    :type node_inputs_name: List[str]
    :param node_outputs_name: List of output names for the ONNX node
    :type node_outputs_name: List[str]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    :param verbose: Whether to print detailed information, default=False
    :type verbose: bool, optional
    :return: List of ONNX nodes
    :rtype: List[helper.NodeProto]
    """


    aidge_operator = aidge_node.get_operator()

    MIN_MAX_AS_ATTRIBUTE =  opset is not None and opset < 11

    min = 0
    if aidge_operator.get_input(1) is not None: # operator associated
        min = aidge_operator.get_input(1)[0]
    else: # min is an attribute
        min = aidge_operator.min()

    max = 0
    if aidge_operator.get_input(2) is not None: # operator associated
        max = aidge_operator.get_input(2)[0]
    else: # min is an attribute
        max = aidge_operator.max()
        node_inputs_name[2] =f"{aidge_node.name()}_in_max"

    # max and min tensors but no node
    if aidge_node.get_parent(1) is None:
        node_inputs_name[1] =f"{aidge_node.name()}_in_min"
    if aidge_node.get_parent(2) is None:
        node_inputs_name[2] =f"{aidge_node.name()}_in_max"

    if MIN_MAX_AS_ATTRIBUTE:
        del node_inputs_name[1]
        del node_inputs_name[2]

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Clip",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_nodes = []

    if MIN_MAX_AS_ATTRIBUTE:
        onnx_node.attribute.append(
            helper.make_attribute(
                "min",
                min
        ))
        onnx_node.attribute.append(
            helper.make_attribute(
                "max",
                max
        ))
    else:
        # If min or max are a producer, nothing to do
        # But if they are none we need to create a constant node
        # With the attribute value!
        if aidge_node.get_parent(1) is None:

            # No producer input for indices, create a constant node
            min_node = helper.make_node(
                name=f"{node_inputs_name[1]}_constant",
                op_type="Constant",
                inputs=[],
                outputs=[node_inputs_name[1]],
            )

            min_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{node_inputs_name[1]}_tensor",
                        # TensorProto.FLOAT,
                        dtype_converter.aidge_to_onnx(get_in_dtype(aidge_operator)),
                        [], # Note: Allow a better netron representation
                        [min]
                    )
                )
            )
            onnx_nodes.append(min_node)

        if aidge_node.get_parent(2) is None:
            # No producer input for indices, create a constant node
            max_node = helper.make_node(
                name=f"{node_inputs_name[2]}_constant",
                op_type="Constant",
                inputs=[],
                outputs=[node_inputs_name[2]],
            )

            max_node.attribute.append(
                helper.make_attribute(
                    "value",
                    helper.make_tensor(
                        f"{node_inputs_name[2]}_tensor",
                        # TensorProto.FLOAT,
                        dtype_converter.aidge_to_onnx(get_in_dtype(aidge_operator)),
                        [], # Note: Allow a better netron representation
                        [max]
                    )
                )
            )
            onnx_nodes.append(max_node)
    onnx_nodes.append(onnx_node)
    return onnx_nodes

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

@auto_register_export("InstanceNorm")
def export_instance_norm(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:
    """
    Export Aidge InstanceNorm operator to ONNX InstanceNormalization operator.
    
    Instance Normalization normalizes the inputs across the spatial dimensions
    for each channel and each sample independently. This is particularly useful
    for style transfer and generative models where instance-specific statistics
    are more relevant than batch statistics.
    
    The computation follows:
    y = scale * (x - mean) / sqrt(variance + epsilon) + bias
    where mean and variance are computed per instance per channel.
    
    :param aidge_node: Aidge node to convert
    :type aidge_node: aidge_core.Node
    :param node_inputs_name: List of input names for the ONNX node
    :type node_inputs_name: List[str]
    :param node_outputs_name: List of output names for the ONNX node
    :type node_outputs_name: List[str]
    :param initializer_list: List of ONNX initializer tensors
    :type initializer_list: List[TensorProto]
    :param opset: ONNX opset version, optional  
    :type opset: Optional[int]
    :return: List of ONNX NodeProto objects
    :rtype: List[helper.NodeProto]
    """
    aidge_operator = aidge_node.get_operator()

    # Create the ONNX InstanceNormalization node
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="InstanceNormalization",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    
    # Add epsilon attribute
    onnx_node.attribute.append(
        helper.make_attribute(
            "epsilon",
            aidge_operator.attr.get_attr("epsilon")
        )
    )
    
    # Add consumed_inputs attribute for opset < 6 (legacy optimization attribute)
    if opset is not None and opset < 6:
        onnx_node.attribute.append(
            helper.make_attribute(
                "consumed_inputs",
                [0, 0, 0]  # Legacy optimization attribute, typically zeros
            )
        )
    
    return [onnx_node]

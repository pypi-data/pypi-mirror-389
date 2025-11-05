"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional

import aidge_core
import onnx
from onnx import NodeProto

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log
from aidge_onnx.utils import warn_unsupported_attr

@auto_register_import("instancenormalization", "instancenorm")
def import_instance_norm(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    Import ONNX InstanceNormalization operator to Aidge InstanceNorm operator.
    
    Instance Normalization normalizes the inputs across the spatial dimensions
    for each channel and each sample independently. This is particularly useful
    for style transfer and generative models where instance-specific statistics
    are more relevant than batch statistics.
    
    The computation follows:
    y = scale * (x - mean) / sqrt(variance + epsilon) + bias
    where mean and variance are computed per instance per channel.
    
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[Tuple[aidge_core.Node, int]]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    
    if len(input_nodes) != 3:
        Log.warn(f"Warning: InstanceNormalization expects exactly 3 inputs (input, scale, bias), got {len(input_nodes)}. This node will be filled by a GenericOperator.")
        return None
    
    instancenorm_attrs: dict = {"epsilon": 1e-05}
    
    if 'epsilon' in onnx_attrs:
        instancenorm_attrs["epsilon"] = onnx_attrs['epsilon']
        del onnx_attrs['epsilon']
    
    if opset < 6 and 'consumed_inputs' in onnx_attrs:
        del onnx_attrs['consumed_inputs']
    
    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'InstanceNormalization' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None
    
    try:
        scale_node, scale_output_idx = input_nodes[1]
        bias_node, bias_output_idx = input_nodes[2]
        if not scale_node or not bias_node:
            raise ValueError("Missing scale or bias input")
    except (IndexError, AttributeError, ValueError) as e:
        Log.warn(f"Warning: Invalid input configuration for InstanceNormalization: {e}. This node will be filled by a GenericOperator.")
        return None
    
    instance_norm_op = aidge_core.InstanceNormOp(instancenorm_attrs["epsilon"])
    instance_norm_node = aidge_core.Node(instance_norm_op, name=node_name)
        
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m] with epsilon={instancenorm_attrs['epsilon']}")
    return instance_norm_node
        


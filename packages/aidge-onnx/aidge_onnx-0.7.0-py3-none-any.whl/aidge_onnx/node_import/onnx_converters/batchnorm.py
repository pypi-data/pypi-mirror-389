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

@auto_register_import("batchnorm", "batchnormalization")
def import_batch_norm(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of Aidge nodes which constitute the input of the current node
    :type input_nodes: List[aidge_core.Node]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs = get_node_attributes(onnx_node, opset)
    batchnorm_attrs: dict = {"epsilon": 1e-05,"momentum":0.9, "training_mode": False}
    #epsilon and momentum are present in all opsets

    if 'epsilon' in onnx_attrs:
        batchnorm_attrs["epsilon"] = onnx_attrs['epsilon']
        del onnx_attrs['epsilon']

    if 'momentum' in onnx_attrs:
        batchnorm_attrs['momentum'] = onnx_attrs['momentum']
        del onnx_attrs['momentum']

    if opset >= 14:
        if 'training_mode' in onnx_attrs:
            batchnorm_attrs['training_mode'] = onnx_attrs['training_mode']
            del onnx_attrs['training_mode']

    if opset < 9:
        if 'spatial' in onnx_attrs:
            if onnx_attrs['spatial'] != 1:
                warn_unsupported_attr('spatial','BatchNorm',opset,onnx_attrs['spatial'])
                return None
            del onnx_attrs['spatial']

    if opset < 7:
        if 'is_test' in onnx_attrs:
            if onnx_attrs['is_test'] != 0:
                warn_unsupported_attr('is_test','BatchNorm',opset,onnx_attrs['is_test'])
                return None
            del onnx_attrs['is_test']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'BatchNorm' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    # Do not use BatchNorm2D helper here, because it requires nb_features argument
    # nb_features = input_nodes[1][0].get_operator().get_output(input_nodes[1][1]).dims[0]
    # nb_features can be obtained as shown above, but at the time of instanciation
    # of this operator, input_nodes[1] may still be None.
    # This may be the case if the input is not an ONNX initializer, but another
    # node (like Identity).
    batch_norm_node = aidge_core.Node(aidge_core.BatchNorm2DOp(**batchnorm_attrs), name=node_name)
    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return batch_norm_node

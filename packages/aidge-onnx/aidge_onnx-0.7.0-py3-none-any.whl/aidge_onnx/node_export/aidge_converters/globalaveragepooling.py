"""
Copyright (c) 2024 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import List, Optional
import aidge_core
from onnx import helper, TensorProto
from aidge_onnx.node_export import auto_register_export


@auto_register_export("GlobalAveragePooling")
def export_globalaveragepooling(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="GlobalAveragePool",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    return [onnx_node]

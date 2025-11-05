"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
from onnx import helper
from aidge_onnx.node_export import auto_register_export
from typing import List, Optional

@auto_register_export("Softplus")
def export_softplus(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    opset: Optional[int] = None,
    **kwargs) -> List[helper.NodeProto]:

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Softplus",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    return [onnx_node]

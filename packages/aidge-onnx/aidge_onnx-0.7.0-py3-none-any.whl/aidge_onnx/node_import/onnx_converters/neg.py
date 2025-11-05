"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from typing import Any, List, Mapping, Tuple

from onnx import NodeProto

from aidge_core import Log, Node, NegOp
from aidge_onnx.node_import import auto_register_import


@auto_register_import("neg")
def import_neg(
    onnx_node: NodeProto, input_nodes: List[Tuple[Node, int]], opset: int
) -> Node:
    """
    :param onnx_node: ONNX node to convert
    :type onnx_node: onnx.NodeProto
    :param input_nodes: List of pairs of Aidge Nodes which constitute the input
        of the current node and their associated output index linking to the
        current Node.
    :type input_nodes: List[aidge_core.Node, int]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    """
    node_name: str = onnx_node.name if onnx_node.name else onnx_node.output[0]
    onnx_attrs: Mapping[str, Any] = {attr.name: attr for attr in onnx_node.attribute}

    if opset < 6:
        #### Attributes
        #  consumed_inputs (Optional) : list of ints
        #    legacy optimization attribute.
        #### Inputs
        #  X : T
        #    Input tensor
        #### Outputs
        #  Y : T
        #    Output tensor
        if "consumed_inputs" in onnx_attrs:
            # legacy optimisation attribute, ignored
            del onnx_attrs["consumed_inputs"]

    if len(onnx_attrs) > 0:
        Log.warn(
            f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'Neg' with opset {opset}.\nThis node will be filled by a GenericOperator."
        )
        return None

    my_node: Node = Node(NegOp(), name=node_name)
    Log.info(
        f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]"
    )
    return my_node

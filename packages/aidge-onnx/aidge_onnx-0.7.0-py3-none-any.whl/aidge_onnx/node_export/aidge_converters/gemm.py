"""
Copyright (c) 2025 CEA-List

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


@auto_register_export("Gemm")
def export_gemm(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs
) -> List[helper.NodeProto]:


    aidge_operator = aidge_node.get_operator()
    micro_graph = aidge_operator.get_micro_graph()
    fc_op = None
    transA = 0
    transB = 0
    alpha = 1.0
    beta = 1.0
    for node in micro_graph.get_nodes():
        if node.type() == "FC":
            fc_op = node.get_operator()
            inputs = node.inputs()
            if inputs[0][0] is not None and inputs[0][0].type() == "Transpose":
                transA = 1
                transpose_node_inputs = inputs[0][0].inputs()
                if transpose_node_inputs[0][0] is not None and transpose_node_inputs[0][0].type() == "Mul":
                    prod = transpose_node_inputs[0][0].inputs()[1][0].get_operator()
                    prod_out_tensor = prod.get_output(0)
                    prod_out_tensor.to_backend("cpu")
                    if not prod.type() == "Producer" or prod_out_tensor.size != 1:
                        raise RuntimeError(f"Cannot retrieve alpha parameter for Gemm operator!")
                    alpha = np.array(prod_out_tensor).flatten()[0].astype(np.float32)
            if inputs[0][0] is not None and inputs[0][0].type() == "Mul":
                prod = inputs[0][0].inputs()[1][0].get_operator()
                prod_out_tensor = prod.get_output(0)
                prod_out_tensor.to_backend("cpu")
                if not prod.type() == "Producer" or prod_out_tensor.size != 1:
                    raise RuntimeError(f"Cannot retrieve alpha parameter for Gemm operator!")
                alpha = np.array(prod_out_tensor).flatten()[0].astype(np.float32)

            if inputs[1][0] is not None and inputs[1][0].type() == "Transpose":
                transB = 1
                transpose_node_inputs = inputs[1][0].inputs()
            if inputs[2][0] is not None and inputs[2][0].type() == "Mul":
                prod = inputs[2][0].inputs()[1][0].get_operator()
                prod_out_tensor = prod.get_output(0)
                prod_out_tensor.to_backend("cpu")
                if not prod.type() == "Producer" or prod_out_tensor.size != 1:
                    raise RuntimeError(f"Cannot retrieve beta parameter for Gemm operator!")
                beta = np.array(prod_out_tensor).flatten()[0].astype(np.float32)

        elif node.type() == "Transpose" or node.type() == "Mul" or node.type() == "Producer":
            pass
        else:
            raise RuntimeError(f"Unsupported node type: {node.type()} inside Gemm.")

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Gemm",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )
    onnx_node.attribute.append(
        helper.make_attribute(
            "alpha",
            alpha
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "beta",
            beta
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "transA",
            transA
    ))
    onnx_node.attribute.append(
        helper.make_attribute(
            "transB",
            1 - transB   # Aidge expects W to be transposed
    ))

    return [onnx_node]

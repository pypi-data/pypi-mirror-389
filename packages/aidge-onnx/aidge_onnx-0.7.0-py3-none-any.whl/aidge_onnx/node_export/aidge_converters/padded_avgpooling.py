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


# For some reasons, pybinds of paddedAveragePooling 1D & 3D are disabled
@auto_register_export("PaddedAvgPooling1D", "PaddedAvgPooling2D", "PaddedAvgPooling3D")
def export_padded_avg_pooling(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs,
) -> List[helper.NodeProto]:
    aidge_operator = aidge_node.get_operator()

    micro_graph = aidge_operator.get_micro_graph()
    avgpool_op, pad_op = None, None
    for node in micro_graph.get_nodes():
        if (
            node.type() == "AvgPooling1D"
            or node.type() == "AvgPooling2D"
            or node.type() == "AvgPooling3D"
        ):
            avgpool_op = node.get_operator()
        elif node.type() == "Pad":
            pad_op = node.get_operator()
        else:
            raise RuntimeError(
                f"Unsupported node type: {node.type()} inside PaddedAvgPooling."
            )

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="AveragePool",
        inputs=list(filter(None, node_inputs_name)),  # ignore Pad extra inputs
        outputs=node_outputs_name,
    )

    onnx_node.attribute.append(
        helper.make_attribute("strides", avgpool_op.attr.stride_dims)
    )
    onnx_node.attribute.append(
        helper.make_attribute("kernel_shape", avgpool_op.attr.kernel_dims)
    )

    onnx_node.attribute.append(helper.make_attribute("pads", pad_op.attr.pads))
    onnx_node.attribute.append(helper.make_attribute("auto_pad", "NOTSET"))

    if opset >= 7:
        ndims = int(len(avgpool_op.attr.ignore_pads) / 2)
        # Validate symmetry and equality to pad_op once
        include = 0
        for idx in range(ndims):
            val_start = avgpool_op.attr.ignore_pads[idx]
            val_end = avgpool_op.attr.ignore_pads[ndims + idx]
            if val_start != val_end:
                raise RuntimeError("Non-symmetric 'ignore_pads' in AveragePool.")
            if val_start > 0:
                if pad_op is None:
                    raise RuntimeError("ignore_pads>0 requires a preceding Pad.")
                if (val_start != pad_op.attr.pads[idx]) or (
                    val_end != pad_op.attr.pads[ndims + idx]
                ):
                    raise RuntimeError("'ignore_pads' must match 'pads'.")
                include = 1  # at least one dim requests including pad in the count

        # Append ONCE, after the loop
        onnx_node.attribute.append(helper.make_attribute("count_include_pad", include))

    if opset >= 10:
        onnx_node.attribute.append(
            helper.make_attribute("ceil_mode", int(avgpool_op.attr.ceil_mode))
        )

    if opset >= 19:
        onnx_node.attribute.append(
            helper.make_attribute("dilations", avgpool_op.attr.dilations)
        )

    return [onnx_node]

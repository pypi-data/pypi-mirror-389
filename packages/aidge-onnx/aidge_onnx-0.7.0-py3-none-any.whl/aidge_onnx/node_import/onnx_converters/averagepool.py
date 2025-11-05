"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List, Tuple, Optional
import numpy as np

import aidge_core
import onnx
from onnx import NodeProto

from aidge_onnx.node_import import auto_register_import
from aidge_onnx.utils import get_node_attributes

from aidge_core import Log
from aidge_onnx.utils import warn_unsupported_attr

@auto_register_import("averagepool")
def import_avg_pooling(onnx_node: NodeProto, input_nodes: List[Tuple[aidge_core.Node, int]], opset: int) -> aidge_core.Node:
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
    avg_pool_attrs: dict = {}
    #attributes common to every opset of avgpool: auto_pad, kernel_shape, pads, strides

    if 'kernel_shape' in onnx_attrs:
        kernel_dims = onnx_attrs['kernel_shape']
        del onnx_attrs['kernel_shape']
        dimensions = len(kernel_dims)
    else:
        Log.warn("Warning: Operator 'AvgPool' must have 'kernel_shape' attribute. This node will be filled by a GenericOperator.")
        return None

    if 'strides' in onnx_attrs:
        avg_pool_attrs['stride_dims'] = onnx_attrs['strides']
        del onnx_attrs['strides']
    else:
        # If not present, the stride defaults is 1 along each spatial axis.
        avg_pool_attrs['stride_dims'] = [1] * dimensions

    avg_pool_attrs['padding_dims'] = [0] * 2*dimensions
    if 'pads' in onnx_attrs:
        avg_pool_attrs['padding_dims'] = onnx_attrs['pads']
        del onnx_attrs['pads']

    if 'auto_pad' in onnx_attrs and onnx_attrs['auto_pad'] in (b'NOTSET', b'SAME_UPPER', b'SAME_LOWER', b'VALID'):
        if onnx_attrs['auto_pad'] != b'NOTSET' and np.count_nonzero(avg_pool_attrs['padding_dims']) > 0:
            raise RuntimeError("Error: malformed ONNX: cannot have both non-zero 'pads' and 'auto_pad' different from 'NOTSET'.")

        nb_feature = len(kernel_dims)
        for i,ele in enumerate(kernel_dims):
            padding = ele - avg_pool_attrs['stride_dims'][i]
            nb_same_padding = padding // 2
            floor_half_hadding = padding % 2

            if onnx_attrs['auto_pad'] == b'SAME_UPPER':
                avg_pool_attrs['padding_dims'][i] = nb_same_padding + floor_half_hadding
                avg_pool_attrs['padding_dims'][i+nb_feature] = nb_same_padding
            elif onnx_attrs['auto_pad'] == b'SAME_LOWER':
                avg_pool_attrs['padding_dims'][i] = nb_same_padding
                avg_pool_attrs['padding_dims'][i+nb_feature] = nb_same_padding + floor_half_hadding
        del onnx_attrs['auto_pad']

    #attributes dependent on the operator's opset
    if opset >= 19:
        if 'dilations' in onnx_attrs:
            avg_pool_attrs['dilations'] = onnx_attrs['dilations']
            del onnx_attrs['dilations']

    if opset >= 10:
        if 'ceil_mode' in onnx_attrs:
            avg_pool_attrs['ceil_mode'] = onnx_attrs['ceil_mode']
            del onnx_attrs['ceil_mode']

    count_include_pad = True
    if opset >= 7:
        if 'count_include_pad' in onnx_attrs:
            count_include_pad = onnx_attrs['count_include_pad']
            del onnx_attrs['count_include_pad']

    if len(onnx_attrs) > 0:
        Log.warn(f"Warning: unsupported attribute(s): {onnx_attrs.keys()} for operator 'AveragePool' with opset {opset}.\nThis node will be filled by a GenericOperator.")
        return None

    #Usage of AvgPoolingOpxD or PaddedAvgPoolingOpxD
    op_aidge_class_name = f"AvgPooling{dimensions}D"
    op_aidge_constr_name = f"AvgPooling{dimensions}DOp"
    if np.count_nonzero(avg_pool_attrs['padding_dims']) > 0:
        op_aidge_class_name = "Padded" + op_aidge_class_name
        op_aidge_constr_name = "Padded" + op_aidge_constr_name
    else:
        del avg_pool_attrs['padding_dims']

    if op_aidge_class_name in dir(aidge_core):
        avg_pooling_op = aidge_core.__getattribute__(op_aidge_constr_name)(
            kernel_dims,
            **avg_pool_attrs)

        if 'padding_dims' in avg_pool_attrs and count_include_pad:
            avg_pooling_op.attr.ignore_pads = avg_pool_attrs['padding_dims']
    else:
        Log.warn(f"Warning: operator {op_aidge_class_name} is not supported in Aidge. This node will be filled by a GenericOperator.")
        return None

    Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")
    return aidge_core.Node(avg_pooling_op, name = node_name)

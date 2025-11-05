"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from typing import List

import onnx
from onnx import helper
import aidge_core
from aidge_onnx.utils import _AIDGE_DOMAIN


def generic_export(
        aidge_node: aidge_core.Node,
        node_inputs_name,
        node_outputs_name,
        opset: int = None,
        enable_custom_op: bool = False) -> None:
    """Function to export a :py:class:`aidge_core.GenericOperator` to an ONNX node

    :param aidge_node: Aidge node containing a :py:class:`aidge_core.GenericOperator`
    :type aidge_node: aidge_core.Node
    :param node_inputs_name: list of names of inputs node
    :type node_inputs_name: list[str]
    :param node_outputs_name: list of names of outputs node
    :type node_outputs_name: list[str]
    :param opset: opset to use for the export, defaults to None
    :type opset: int, optional
    :param enable_custom_op: If True, the export will not fait if the type associated to the :py:class:`aidge_core.GenericOperator` is not , defaults to False
    :type enable_custom_op: bool, optional
    """
    aidge_core.Log.debug(
        f"Exporting GenericOperator {aidge_node.name()}[{aidge_node.type()}] to ONNX")
    aidge_operator = aidge_node.get_operator()
    if not issubclass(type(aidge_operator), aidge_core.GenericOperatorOp):
        raise RuntimeError(
            f"No support for onnx export of Aidge operator : {aidge_node.type()}")

    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type=aidge_node.type(),
        inputs=node_inputs_name,
        outputs=node_outputs_name,
    )

    if hasattr(aidge_operator, "attr"):
        for key, val in aidge_operator.attr.dict().items():
            aidge_core.Log.info(f"\t{key}: {val}")
            onnx_node.attribute.append(helper.make_attribute(key, val))
    else:
        aidge_core.Log.debug(f"Operator {aidge_node.name()}[{aidge_node.type()}] has no attribute")
    # Check if operator is supported by ONNX
    if not onnx.defs.has(aidge_node.type()):
        if enable_custom_op:
            onnx_node.domain = _AIDGE_DOMAIN
            onnx.defs.OpSchema(
                name=aidge_node.type(),
                domain=_AIDGE_DOMAIN,
                since_version=1,
            )
        else:
            raise RuntimeError(
                f"GenericOperator {aidge_node.name()}[{aidge_node.type()}] is not compatible with ONNX domain and enable_custom_op is False.")

    return [onnx_node]

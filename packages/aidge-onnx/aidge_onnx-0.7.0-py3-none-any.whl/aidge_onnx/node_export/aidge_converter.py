"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from collections import defaultdict
from typing import List, Mapping, Callable, Optional

import onnx

import aidge_core
from .generic_export import generic_export


AIDGE_NODE_CONVERTER_: Mapping[str, Callable[[aidge_core.Node, List[str], List[str], Optional[int]], onnx.NodeProto]] = defaultdict(lambda: generic_export)
"""This ``defaultdict`` maps the Aidge type to a function which can convert an Aidge Node into an ONNX Node.  If the function fails to convert the operator, it must return ``None``.
This means that if a key is missing from :py:data:`aidge_onnx.node_export.AIDGE_NODE_CONVERTER_`, it will return the function
:py:func:`aidge_onnx.node_export.generic_export.generic_export` which imports the Aidge node as an ONNX generic operator.
It is possible to add keys to this dictionnary using :py:func:`aidge_onnx.node_export.register_export` or :py:func:`aidge_onnx.node_export.auto_register_export`
"""

def auto_register_export(*args) -> Callable:
    """Decorator used to register a converter to the :py:data:`aidge_onnx.node_export.AIDGE_NODE_CONVERTER_`

    Example:

    .. code-block:: python

        @auto_register_export("myOp")
        def my_op_converter(aidge_node, node_inputs_name, node_outputs_name, verbose):
            ...

    :param args: Set of keys (str) which should correspond to the operator type defined by Aidge.
    """

    key_list = [arg for arg in args]

    def decorator(decorated_function) -> Callable:
        def wrapper(*args, **kwargs) -> Callable:
            """Transparent wrapper.
            """
            return decorated_function(*args, **kwargs)

        for key in key_list:
            register_export(key, decorated_function)

        return wrapper
    return decorator

def supported_operators() -> List[str]:
    """Return a list of operators supported by the ONNX export.

    :return: List of string representing the operators supported by the ONNX import.
    :rtype: List[str]
    """
    return list(AIDGE_NODE_CONVERTER_.keys())

def register_export(key, parser_function) -> None:
    """Add a new conversion function to the :py:data:`aidge_onnx.node_export.AIDGE_NODE_CONVERTER_` dictionnary.
    A conversion function must have the following signature : ``(aidge_core.Node, List[str], List[str], int, bool) -> onnx.NodeProto``

    :param key: This chain of characters must correspond to the Aidge type.
    :type key: str
    :param converter_function: Function which take as an input an Aidge node, list of inputs name, outputs name and a boolean to handle verbosity level.
    :type converter_function: Callable[[aidge_core.Node, List[str], List[str], Optional[int]], onnx.NodeProto]
    """
    AIDGE_NODE_CONVERTER_[key] = parser_function


def remove_export_converter(key: str) -> None:
    """Remove the support for the operator provided"""
    del AIDGE_NODE_CONVERTER_[key]

def clear_export_converter() -> None:
    """Remove the support for all operators"""
    AIDGE_NODE_CONVERTER_.clear()

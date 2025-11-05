"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Callable, Optional, Protocol

import onnx

import aidge_core
from .generic import import_generic

# Protocol for ONNX node converter functions
class ConverterType(Protocol):
    def __call__(
        self,
        onnx_node: onnx.NodeProto,
        input_nodes: List[Tuple[aidge_core.Node, int]],
        opset: int,
    ) -> Optional[aidge_core.Node]:
        ...


ONNX_NODE_CONVERTER_: Dict[str, ConverterType] = defaultdict(lambda: import_generic)
"""This ``defaultdict`` maps the ONNX type to a function which can convert an ONNX Node into an Aidge Node.  If the function fails to convert the operator, it must return ``None``.
This means that if a key is missing from :py:data:`aidge_onnx.node_import.ONNX_NODE_CONVERTER_`, it will return the function
:py:func:`aidge_onnx.node_import.generic.import_generic` which imports the ONNX node as an Aidge generic operator.
It is possible to add keys to this dictionnary using :py:func:`aidge_onnx.node_import.register_import` or :py:func:`aidge_onnx.node_import.auto_register_import`
"""


def auto_register_import(*args) -> Callable[[ConverterType], ConverterType]:
    """Decorator used to register a converter to the :py:data:`aidge_onnx.node_import.ONNX_NODE_CONVERTER_`

    Example:

    .. code-block:: python

        @auto_register_import("myOp")
        def my_op_onverter(onnx_node, input_nodes, opset):
            ...

    :param args: Set of keys (str) which should correspond to the operator type defined by ONNX (https://github.com/onnx/onnx/blob/main/docs/Operators.md).
    """

    key_list = [arg for arg in args]

    def decorator(decorated_function: ConverterType) -> ConverterType:
        """Replace the function by the wrapper and add the ``decorated_function`` to the :py:data:`aidge_onnx.node_import.ONNX_NODE_CONVERTER_`."""

        def wrapper(*args, **kwargs) -> Optional[aidge_core.Node]:
            """Transparent wrapper."""
            return decorated_function(*args, **kwargs)

        for key in key_list:
            register_import(key, decorated_function)

        return wrapper

    return decorator


def supported_operators() -> List[str]:
    """Return a list of operators supported by the ONNX import.

    :return: List of string representing the operators supported by the ONNX import.
    :rtype: List[str]
    """
    return list(ONNX_NODE_CONVERTER_.keys())


def register_import(key: str, converter_function: ConverterType) -> None:
    """Add a new conversion function to the :py:data:`aidge_onnx.node_import.ONNX_NODE_CONVERTER_` dictionnary.
    A conversion function must have the following signature : ``(onnx.NodeProto, List[aidge_core.Node], int) -> aidge_core.Node``

    :param key: This chain of characters must correspond to the ONNX type (https://github.com/onnx/onnx/blob/main/docs/Operators.md) of the operator (in lowercase).
    :type key: str
    :param converter_function: Function which take as an input the ONNX node and a list of aidge nodes and output the corresponding Aidge node. This function must not connect the node. If the function fails to convert the operator, it must return ``None``.
    :type converter_function: Callable[[onnx.NodeProto, List[Tuple[:py:class:`aidge_core.Node`], int], int], :py:class:`aidge_core.Node`]
    """
    ONNX_NODE_CONVERTER_[key] = converter_function


def remove_import_converter(key: str) -> None:
    """Remove the support for the operator provided"""
    del ONNX_NODE_CONVERTER_[key]


def clear_import_converter() -> None:
    """Remove the support for all operators"""
    ONNX_NODE_CONVERTER_.clear()

"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
from .onnx_converter import ONNX_NODE_CONVERTER_, auto_register_import, supported_operators, register_import, clear_import_converter, remove_import_converter
from .onnx_converters import *

import onnx

from onnx import helper, TensorProto
import aidge_core
from aidge_onnx.node_export import auto_register_export
import aidge_onnx.dtype_converter
from aidge_core import dtype as ai_dtype
from typing import List, Optional


@auto_register_export("Cast")
def export_cast(
    aidge_node: aidge_core.Node,
    node_inputs_name: List[str],
    node_outputs_name: List[str],
    initializer_list: List[TensorProto],
    opset: Optional[int] = None,
    **kwargs,
) -> List[helper.NodeProto]:
    """
    Export the Cast operation from Aidge to ONNX.

    :param aidge_node: Aidge node to convert
    :type aidge_node: aidge_core.Node
    :param node_inputs_name: List of input names for the ONNX node
    :type node_inputs_name: List[str]
    :param node_outputs_name: List of output names for the ONNX node
    :type node_outputs_name: List[str]
    :param opset: Indicate opset version of the ONNX model, default=None
    :type opset: int, optional
    :param verbose: Whether to print detailed information, default=False
    :type verbose: bool, optional
    :return: List of ONNX nodes
    :rtype: List[helper.NodeProto]
    """

    # Extract the cast attributes from the Aidge node
    aidge_operator = aidge_node.get_operator()
    # Convert Aidge data type to ONNX data type
    try:
        onnx_target_type = aidge_onnx.dtype_converter.aidge_to_onnx(
            aidge_operator.attr.get_attr("target_type")
        )
    except ValueError as e:
        aidge_core.Log.warn(f"Warning: {e} for Cast operation in node {aidge_node.name()}")
        return None

    # Create the ONNX node
    onnx_node = helper.make_node(
        name=aidge_node.name(),
        op_type="Cast",
        inputs=node_inputs_name,
        outputs=node_outputs_name,
        to=onnx_target_type,
    )
    node_name = onnx_node.name if onnx_node.name else onnx_node.output[0]

    aidge_core.Log.info(f"Loaded node [\033[1m\033[3m{node_name}\033[0m] of type [\033[1m\033[3m{onnx_node.op_type}\033[0m]")

    return [onnx_node]

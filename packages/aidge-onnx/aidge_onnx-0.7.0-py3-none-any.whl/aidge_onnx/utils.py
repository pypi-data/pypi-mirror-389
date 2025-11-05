import onnx

from aidge_core import Log
from typing import Dict, Any
from importlib.metadata import version

_AIDGE_DOMAIN = "ai.onnx.converters.aidge"

def show_version():
    version_aidge_onnx = version("aidge_onnx")
    version_onnx = version("onnx")
    version_protobuf = version("protobuf")
    print(f"Aidge ONNX: {version_aidge_onnx}")
    print(f"ONNX version: {version_onnx}")
    print(f"Protobuf: {version_protobuf}")

def get_project_version()->str:
    return version("aidge_onnx")

def onnx_to_aidge_model_names(model: onnx.ModelProto) -> onnx.ModelProto:
    """
    Change the name of each node of the model from onnx convention to aidge's one
    args :
        model : to modify
    return :
        model : modified
    """
    for i in model.graph.initializer:
        i.name = onnx_to_aidge_name(i.name)

    for n in model.graph.node:
        if len(n.name) > 0:
            new_name = onnx_to_aidge_name(n.name)
            if n.name[0].isdigit():
                new_name = "layer_" + new_name
            n.name = new_name
        for index, i in enumerate(n.input):
            n.input[index] = onnx_to_aidge_name(i)
        for index, o in enumerate(n.output):
            n.output[index] = onnx_to_aidge_name(o)

    for i in model.graph.input:
        i.name = onnx_to_aidge_name(i.name)

    for o in model.graph.output:
        o.name = onnx_to_aidge_name(o.name)

    return model


def onnx_to_aidge_name(name: str) -> str:
    """
    Translates onnx node naming convention to aidge naming convention
    """
    name = name.replace("/", "_").replace(".", "_").replace(":", "_")
    if len(name) > 0 and name[0] == "_":
        name = name[1:]
    name = name if (len(name) == 0 or not name[0].isdigit()) else "data_" + name
    return name


def get_node_attributes(
    onnx_node: onnx.NodeProto, op_set: int = None, domain: str = ""
) -> Dict[str, Any]:
    """Given an ONNX node, return a dictionary with all attributes set to the
    provided value if any or the default value.
    """
    op_type = onnx_node.op_type
    schema = onnx.defs.get_schema(op_type, op_set, domain)
    result_attrs = {}

    provided_attrs = (
        {
            attr.name: onnx.helper.get_attribute_value(attr)
            for attr in onnx_node.attribute
        }
        if onnx_node.attribute
        else {}
    )

    for attr_name, attr in schema.attributes.items():
        if attr_name in provided_attrs:
            result_attrs[attr_name] = provided_attrs[attr_name]
            del provided_attrs[attr_name]
        elif attr.required:
            raise ValueError(f"Required attribute '{attr_name}' is missing.")
        elif attr.default_value.type != onnx.AttributeProto.AttributeType.UNDEFINED:
            # Add default attributes
            if attr.default_value.type == onnx.AttributeProto.INT:
                result_attrs[attr_name] = attr.default_value.i
            elif attr.default_value.type == onnx.AttributeProto.FLOAT:
                result_attrs[attr_name] = attr.default_value.f
            elif attr.default_value.type == onnx.AttributeProto.STRING:
                result_attrs[attr_name] = attr.default_value.s
            elif attr.default_value.type == onnx.AttributeProto.TENSOR:
                result_attrs[attr_name] = onnx.numpy_helper.to_array(
                    attr.default_value.t
                )
            elif attr.default_value.type == onnx.AttributeProto.INTS:
                result_attrs[attr_name] = list(attr.default_value.ints)
            elif attr.default_value.type == onnx.AttributeProto.FLOATS:
                result_attrs[attr_name] = list(attr.default_value.floats)
            elif attr.default_value.type == onnx.AttributeProto.STRINGS:
                result_attrs[attr_name] = list(attr.default_value.strings)
    if len(provided_attrs) > 0:
        raise ValueError(
            f"Warning: unsupported attribute(s): {provided_attrs.keys()} "
            f"for operator '{onnx_node.op_type}' with opset {op_set}."
        )
    return result_attrs

def warn_unsupported_attr(
    attr: str, operator: str, opset: int, value: Any = None
) -> None:
    """Function used to standardize warning messages for operators import

    :param attr: Name of the attribute not supported
    :type attr: str
    :param operator: name of the type of operator
    :type operator: str
    :param opset: opset of the operator used
    :type opset: int
    :param value: Value of the attribute if it has one
    :type value: Any
    """
    if value is not None:
        Log.warn(
            f"Warning: Unsupported attribute '{attr}' with value {value} for operator '{operator}' with opset {opset}. This node will be filled by a GenericOperator."
        )
    else:
        Log.warn(
            f"Warning: Unsupported attribute '{attr}' for operator '{operator}' with opset {opset}. This node will be filled by a GenericOperator."
        )

def get_inputs(onnx_model: onnx.ModelProto) -> list[dict]:
    """Return the ONNX inputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list of dicts with input names and dimensions
    :rtype: list[dict]
    """
    #the inputs have names in the onnx files (e.g.: 'input', 'X', etc.)
    #nb_inputs = len(onnx_model.graph.input)
    #initialize the return
    onnx_input_nodes = []
    #sometimes, the inputs include producers, so they must be excluded
    onnx_producer_nodes_names = [node.name for node in onnx_model.graph.initializer]
    #read each input and add name and dimensions to a list
    for input_node in onnx_model.graph.input:
        if not input_node.name in onnx_producer_nodes_names:
            onnx_input_nodes.append({"name":input_node.name, "dims": [dim.dim_value if (dim.dim_value != 0) else 1 for dim in input_node.type.tensor_type.shape.dim]})
    #print("inputs:", onnx_input_nodes)
    return onnx_input_nodes

def get_outputs(onnx_model: onnx.ModelProto) -> list[dict]:
    """Return the ONNX outputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list of dicts with output names and dimensions
    :rtype: list[dict]
    """
    #the outputs have names in the onnx files (e.g.: 'ouput', 'Y', etc.)
    #nb_outputs = len(onnx_model.graph.output)
    onnx_output_nodes = []
    #read each output and add name and dimensions to a list
    for output_node in onnx_model.graph.output:
        onnx_output_nodes.append({"name":output_node.name, "dims": [dim.dim_value if (dim.dim_value != 0) else 1 for dim in output_node.type.tensor_type.shape.dim]})
    #print("outputs:", onnx_output_nodes)
    return onnx_output_nodes


def get_input_dims(onnx_model: onnx.ModelProto) -> list[list]:
    """Return the dimensions of all ONNX inputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list of lists with the shapes of the onnx inputs
    :rtype: list[list]
    """
    #sometimes, the inputs include producers, so they must be excluded
    onnx_producer_nodes_names = [node.name for node in onnx_model.graph.initializer]
    return [[dim.dim_value if (dim.dim_value != 0) else 1 for dim in node.type.tensor_type.shape.dim] for node in onnx_model.graph.input if not node.name in onnx_producer_nodes_names]

def get_output_dims(onnx_model: onnx.ModelProto) -> list[list]:
    """Return the dimensions of all ONNX outputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list of lists with the shapes of the onnx outputs
    :rtype: list[list]
    """
    return [[dim.dim_value if (dim.dim_value != 0) else 1 for dim in node.type.tensor_type.shape.dim] for node in onnx_model.graph.output]


def get_input_names(onnx_model: onnx.ModelProto) -> list[str]:
    """Return the names of all ONNX inputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list with the names of the onnx inputs
    :rtype: list[str]
    """
    #sometimes, the inputs include producers, so they must be excluded
    onnx_producer_nodes_names = [node.name for node in onnx_model.graph.initializer]
    return [node.name for node in onnx_model.graph.input if not node.name in onnx_producer_nodes_names]

def get_output_names(onnx_model: onnx.ModelProto) -> list[str]:
    """Return the names of all ONNX outputs.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    :return: a list with the names of the onnx outputs
    :rtype: list[str]
    """
    return [node.name for node in onnx_model.graph.output]

def set_every_out_as_graph_out(model: onnx.ModelProto):
    """Set every node output as a graph output.
    Constant nodes are ignored.
    This allow to retrieve intermediate outputs when using ONNX Runtime.

    :param onnx_model: the onnx model
    :type onnx_model: onnx.ModelProto
    """
    # Create a set of Constant node to ignore them
    constant_nodes_name = set(output for node in model.graph.node if node.op_type == "Constant" for output in node.output)
    shape_info = onnx.shape_inference.infer_shapes(model)
    for node in shape_info.graph.value_info:
        if node.name not in constant_nodes_name:
            model.graph.output.append(node)
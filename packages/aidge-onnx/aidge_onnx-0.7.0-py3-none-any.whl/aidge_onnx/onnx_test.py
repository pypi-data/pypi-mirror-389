import onnx
from aidge_core import Log
from typing import Union

def check_onnx_validity(onnx_model: Union[str, onnx.ModelProto]) -> bool:
    """
    Check if an ONNX model or file path is valid according to the ONNX standard.

    :param model: Either a path to an ONNX file (str) or a loaded ONNX model (onnx.ModelProto).
    :type model: Union[str, onnx.ModelProto]
    :return: True if the model is valid, False otherwise.
    :rtype: bool
    """

    if isinstance(onnx_model, str):
        try:
            # Load the ONNX model
            model = onnx.load(onnx_model)
        except Exception as e:
            Log.notice(f"An error occurred while loading the ONNX file:\n{e}")
            return False
    elif isinstance(onnx_model, onnx.ModelProto):
        model = onnx_model
    else:
        raise TypeError("Input must be a file path (str) or an onnx.ModelProto instance.")

    try:
        # Check the model for errors
        onnx.checker.check_model(model)
    except onnx.onnx_cpp2py_export.checker.ValidationError as e:
        Log.notice(f"The ONNX file is invalid:\n{e}")
        return False
    except Exception as e:
        Log.notice(f"An error occurred while checking the ONNX file: {e}")
        return False
    Log.notice("The ONNX file is valid.")
    return True

def _compare_onnx_attributes(attr_list_1, attr_list_2):
    if len(attr_list_1) != len(attr_list_2):
        return False

    attr_map_1 = {attr.name : attr for attr in attr_list_1}
    attr_map_2 = {attr.name : attr for attr in attr_list_2}

    for attr_name, attr1 in attr_map_1.items():
        if attr_name not in attr_map_2:
            return False
        attr2 = attr_map_2[attr_name]
        if attr1.type !=attr2.type:
            return False
        values_are_equal = False

        if attr1.type == onnx.AttributeProto.FLOAT:
            values_are_equal = attr1.f == attr2.f
        elif attr1.type == onnx.AttributeProto.INT:
            values_are_equal = attr1.i == attr2.i
        elif attr1.type == onnx.AttributeProto.STRING:
            values_are_equal = attr1.s == attr2.s
        elif attr1.type == onnx.AttributeProto.FLOATS:
            return attr1.floats == attr2.floats
        elif attr1.type == onnx.AttributeProto.INTS:
            return attr1.ints == attr2.ints
        elif attr1.type == onnx.AttributeProto.STRINGS:
            return attr1.strings == attr2.strings

        if not values_are_equal:
            return False
    return True

def check_isomorphism(file_path1, file_path2):
    """If both onnx file are isomorphic return True.
    This check account for possible branch permutations.
    """
    model1 = onnx.load(file_path1)
    model2 = onnx.load(file_path2)

    nodes1 = model1.graph.node
    nodes2 = model2.graph.node

    # Easy check on number of nodes.
    if len(nodes1) != len(nodes2):
        Log.notice(f"Graph are not isomorphic, number of nodes differs ({len(nodes1)} != {len(nodes2)})")
        return False

    # Set of index of nodes from graph2 which has been matched in graph1
    matched_nodes = set()

    for node1 in nodes1:
        node_not_found = True
        for i, node2 in enumerate(nodes2):
            if i not in matched_nodes and\
                  node1.op_type == node2.op_type and\
                      _compare_onnx_attributes(node1.attribute, node2.attribute):
                matched_nodes.add(i)
                node_not_found = False
        if node_not_found:
            Log.notice(f"Cannot find equivalent of node: {node1.name} in {file_path2}")
            return False
    return True

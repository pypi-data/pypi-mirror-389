"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""
import aidge_core
import numpy as np
import sys
from typing import List, Dict, Tuple
from collections import defaultdict


from importlib.metadata import version
import onnx
from onnx import helper
from onnx import numpy_helper
from onnx import TensorProto
from aidge_onnx.utils import _AIDGE_DOMAIN

from .node_export.aidge_converter import AIDGE_NODE_CONVERTER_
from aidge_onnx import dtype_converter, has_native_coverage


def make_edge_names_unique(graph_view: aidge_core.GraphView)->None:
    """
    Ensures all edge names in the graph are unique and consistent between connected nodes.

    For each node in the graph, this function checks the names of its inputs:

    - If the input is connected to a parent node, the input name must match the parent's output name.
    - If the input name is already used by a different connection, it will be renamed with a unique suffix (e.g., ``_0``, ``_1``, etc.).
    - The corresponding parent's output name is also updated to match the new unique name.

    This guarantees that each edge (connection between output and input) has a globally unique name in the graph.

    :param graph_view: The graph view to process.
    :type graph_view: aidge_core.GraphView

    :raises RuntimeError: If a node's input name does not match the output name of its connected parent node.
    """
    nodes: List[aidge_core.Node] = graph_view.get_nodes()

    # Dictionary with key: edge name and value a pair parent name and parent outID
    # If a node is graph input then the value is None
    edge_name: Dict[str, Tuple[aidge_core.Node, int]] = {}

    # Lambda function to test if an edge name is unique
    # An edge is unique if it hasn't been seen or if it is connected to the same edge
    name_is_unique = lambda _name, _parent_outID: _name not in edge_name or _parent_outID == edge_name[_name]

    for node in nodes:
        for in_id in range(node.get_nb_inputs()):
            input_name = node.input_name(in_id)
            # Optional data/param are named "" when not connected
            if input_name == "": continue
            parent_outID: Tuple[aidge_core.Node, int] = node.input(in_id)
            parent = parent_outID[0]
            out_id = parent_outID[1]
            if parent and input_name != parent.output_name(out_id):
                raise RuntimeError(
                    f"Graph is corrupted: {parent.name()}({parent.type()})#{out_id} -> "
                    f"{node.name()}({node.type()})#{in_id}\n"
                    f"Output name is {parent.output_name(out_id)} != input name {input_name}"
                )

            if not name_is_unique(input_name, parent_outID):
                cpt = 0
                new_name = f"{input_name}_{cpt}"
                while(not name_is_unique(new_name, parent_outID)):
                    cpt += 1
                    new_name = f"{input_name}_{cpt}"
                node.input_name(in_id, new_name)
                if parent: parent.output_name(out_id, new_name)
                edge_name[new_name] = parent_outID if parent else None
            else:
                edge_name[input_name] = parent_outID if parent else None


def remove_duplicate_names(graph_view: aidge_core.GraphView):
    """Given a :py:class:`aidge_core.GraphView` rename every nodes with duplicate names.
    Nodes are browsed in no particular order so renaming may seems random.
    If same names are encountered the old name is suffixed by ``_{idx}``.
    Where idx in range(nb_duplicate).
    This function is called recursively as long as there are duplicates.

    :param graph_view: GraphView to parse
    :type graph_view: :py:class:`aidge_core.GraphView`
    """
    # Boolean used to get out of recursion
    name_updated = False
    # Dictionary which map a name to the nodes which have this name
    # Use of defaultdict to ease the syntax
    name_map = defaultdict(list)
    for aidge_node in graph_view.get_nodes():
        name_map[aidge_node.name()].append(aidge_node)

    for name, node_list in name_map.items():
        if len(node_list) > 1:
            # We need another recursive call to check current modifications doesn't invalidate the graph
            name_updated = True
            for idx, node in enumerate(node_list):
                node.set_name(name + f"_{idx}")

    # Recursion call !
    if name_updated:
        remove_duplicate_names(graph_view)

def export_onnx(graph_view: aidge_core.GraphView,
                path_to_save: str,
                inputs_dims: Dict[str, List[List[int]]] = None,
                outputs_dims: Dict[str, List[List[int]]] = None,
                enable_custom_op: bool = False,
                opset: int = None,
                ir_version: int =None):
    """Export a :py:class:`aidge_core.GraphView` to an ONNX file.

    :param graph_view: :py:class:`aidge_core.GraphView` to convert.
    :type graph_view: :py:class:`aidge_core.GraphView`
    :param path_to_save: Path where to save the ONNX file, example ``test.onnx``
    :type path_to_save: str
    :param inputs_dims: input dimensions of the network, if provided, ``outputs_dims`` must also be filled, this argument is a map, where the key is the name of the input node and the value is a list of dimensions ordered by the input index, defaults to None
    :type inputs_dims: Mapping[str, List[List[int]]], optional
    :param outputs_dims: output dimensions of the network, if provided, ``inputs_dims`` must also be filled, this argument is a map, where the key is the name of the output node and the value is a list of dimensions ordered by the output index, defaults to None
    :type outputs_dims: Mapping[str, List[List[int]]], optional
    :param enable_custom_op: If True, export will not fail for :py:class:`aidge_core.GenericOperator` and will add the operator schema to a custom aidge domain, defaults to False
    :type enable_custom_op: bool, optional
    :param opset: The version of the ONNX opset generated, defaults to None
    :type opset: int, optional
    :param ir_version: The version of the ONNX intermediate representation, if None the version will be decided by `onnx.helper.make_model`, defaults to None
    :type ir_version: int, optional
    """
    model: onnx.ModelProto = convert_aidge_to_onnx(graph_view,
                                                   path_to_save,
                                                   inputs_dims,
                                                   outputs_dims,
                                                   enable_custom_op,
                                                   opset,
                                                   ir_version)
    onnx.save(model, path_to_save)


def convert_aidge_to_onnx(graph_view: aidge_core.GraphView,
                model_name: str,
                inputs_dims: Dict[str, List[List[int]]] = None,
                outputs_dims: Dict[str, List[List[int]]] = None,
                enable_custom_op: bool = False,
                opset: int = None,
                ir_version: int =None) -> onnx.ModelProto:
    """Export a :py:class:`aidge_core.GraphView` to an ONNX file.

    :param graph_view: :py:class:`aidge_core.GraphView` to convert.
    :type graph_view: :py:class:`aidge_core.GraphView`
    :param model_name: how to name the ONNX model, example ``test``
    :type model_name: str
    :param inputs_dims: input dimensions of the network, if provided, ``outputs_dims`` must also be filled, this argument is a map, where the key is the name of the input node and the value is a list of dimensions ordered by the input index, defaults to None
    :type inputs_dims: Mapping[str, List[List[int]]], optional
    :param outputs_dims: output dimensions of the network, if provided, ``inputs_dims`` must also be filled, this argument is a map, where the key is the name of the output node and the value is a list of dimensions ordered by the output index, defaults to None
    :type outputs_dims: Mapping[str, List[List[int]]], optional
    :param enable_custom_op: If True, export will not fail for :py:class:`aidge_core.GenericOperator` and will add the operator schema to a custom aidge domain, defaults to False
    :type enable_custom_op: bool, optional
    :param opset: The version of the ONNX opset generated, defaults to None
    :type opset: int, optional
    :param ir_version: The version of the ONNX intermediate representation, if None the version will be decided by `onnx.helper.make_model`, defaults to None
    :type ir_version: int, optional
    :return: an ONNX model equivalent Aidge model.
    :rtype: onnx.ModelProto
    """
    major, minor = onnx.__version__.split(".")[:2]
    if enable_custom_op and (int(major)*100 + int(minor) < 114):
        ("Warning: Cannot enable custom operator with onnx < 1.14, update onnx library with:"
              "\n\t> pip install --upgrade onnx\nDefaulting to enable_custom_op = False")
        enable_custom_op = False
    if opset is None:
        opset = onnx.defs.onnx_opset_version()

    # Map old inputs names to nodes to keep track of node name after potential renaming
    # This is used to make inputs_dims and outputs_dims works.
    old_io_names = {}
    old_io_names.update({node: node.name()
                        for node in graph_view.get_input_nodes()})
    old_io_names.update({node: node.name()
                        for node in graph_view.get_output_nodes()})

    remove_duplicate_names(graph_view)
    make_edge_names_unique(graph_view)

    # Initializing variables necessary for ONNX creation
    onnx_inputs = []  # List of ONNX tensor representing graph inputs
    onnx_outputs = []  # List of ONNX tensor representing graph outputs
    onnx_initializers = []  # List of ONNX initializers in no particular order
    onnx_nodes = []  # List of ONNX nodes, must follow the topological order of the graph
    # Variable used to help in the creation of the ONNX
    open_nodes = []  # Queue of Aidge nodes to explore, guarantee a topological exploration of the graph
    closed_nodes = []  # List of Aidge nodes already explored

    if inputs_dims is not None:
        if outputs_dims is None:
            if has_native_coverage(graph_view):
                in_dims = [dim for dims in inputs_dims.values() for dim in dims]
                if len(in_dims) != 1:
                    raise NotImplementedError("ONNX export only support forward dims with one dimensions.")
                graph_view.forward_dims(dims=in_dims[0])
            else:
                raise RuntimeError("Both input_dims and output_dims must be defined.")

    # Boolean to check if every tensor is defined (i.e. possess a dim)
    all_tensor_def = all([all([not o.is_undefined() for o in node.get_operator().get_outputs()]) for node in graph_view.get_nodes()])

    forward_dims_required = (inputs_dims is None) and (not all_tensor_def)
    if forward_dims_required:
        for input_node, in_idx in graph_view.get_ordered_inputs():
            if input_node.get_operator().is_optional_input(in_idx): continue
            parent_node, _ = input_node.input(in_idx)
            if parent_node is None:
                raise RuntimeError(
                    f"One of the input of the GraphView is not set. Check inputs {input_node.name()}[{input_node.type()}][{in_idx}].")
        graph_view.forward_dims()

    open_nodes = list(graph_view.get_input_nodes())
    if not open_nodes:
        open_nodes = [graph_view.root_node()]

    graph_inputs_name = [node.name() for node in graph_view.get_input_nodes()]
    graph_outputs_name = [node.name()
                          for node in graph_view.get_output_nodes()]

    # Creating initializer list
    for aidge_node in graph_view.get_nodes():
        aidge_operator = aidge_node.get_operator()
        # Check if operator is an initializer
        if isinstance(aidge_operator, aidge_core.ProducerOp):
            if aidge_operator.get_output(0).impl :
                # if not aidge_operator.attr.constant:
                aidge_core.Log.info(f"Creating initializer: {aidge_node.name()}")
                onnx_initializers.append(
                    numpy_helper.from_array(
                        np.array(aidge_operator.get_output(0)),
                        f"{aidge_node.name()}_out0")
                )
                # Node converted, adding to close list
                closed_nodes.append(aidge_node)
                # Not supposed to be in open_nodes list since it is a Producer,
                # except if it is the root node
                if aidge_node in open_nodes:
                    # In this case, open_nodes only contain this node and we
                    # must add its childs to allow to start topological exploration!
                    open_nodes += list(aidge_node.get_children())
                # endif not aidge_operator.attr.constant:
            else:
                raise RuntimeError(f"The producer {aidge_node.name()} does not have an implementation, make sure it is initialized !")
    # Topological exploration of the graph !
    while open_nodes:
        aidge_node = open_nodes.pop(0)
        if aidge_node in closed_nodes:
            continue  # Node already converted, moving on ...
        parents_not_converted = False
        # Check all parents have been converted
        for parent in aidge_node.get_parents():
            if parent is not None and \
                    parent not in closed_nodes:
                # If parents have not been converted, push back current node
                if not parents_not_converted:
                    open_nodes.insert(0, aidge_node)
                    parents_not_converted = True
                # Add to the stack the not converted parent as next node to convert
                open_nodes.insert(0, parent)
        if parents_not_converted:
            continue
        # Next nodes to treat are children of current node
        open_nodes += list(aidge_node.get_children())
        aidge_core.Log.info(aidge_node.name() + "[" + aidge_node.type() + "]" + "\n" +
                  "="*(len(aidge_node.name()) + 2 + len(aidge_node.type())))

        aidge_operator = aidge_node.get_operator()

        # Set input and output names
        # /!\ IMPORTANT /!\
        # Convention:
        # - names of output is "{current_node_name}_out_{out_idx}"
        # - names of input refer to the output name set by the parent node
        node_inputs_name = []
        node_outputs_name = []
        for input_idx in range(len(aidge_node.inputs())):
            node_inputs_name.append(aidge_node.input_name(input_idx))

        # We create all expected output to keep correct order
        for out_idx in range(len(aidge_node.outputs())):
            node_outputs_name.append(aidge_node.output_name(out_idx))

        # Check if node is at the Output of the graph
        if aidge_node.name() in graph_outputs_name:
            # If it is the case, we create ONNX tensor for each one of the node outputs
            for i in range(aidge_node.get_nb_outputs()):
                # Check if node output are connected or not connected to an output of the graph
                if aidge_node.output(i) == [] or all([(tuple_node_idx[0] not in graph_view.get_nodes()) for tuple_node_idx in aidge_node.output(i)]):
                    output_name = aidge_node.output_name(i)
                    output_dims = None
                    out_dtype = None
                    if outputs_dims is not None:
                        dim_name = output_name
                        if old_io_names[aidge_node] in outputs_dims:
                            dim_name = old_io_names[aidge_node]

                        if dim_name not in outputs_dims:
                            continue
                            raise RuntimeError(
                                f"Graph output: {old_io_names[aidge_node]} has no dims specified in outputs_dims parameter.")
                        output_dims = outputs_dims[dim_name][i]
                        if aidge_node.get_operator().get_output(i) is None:
                            # If no output default to float32
                            aidge_core.Log.warn(f"Output {aidge_node.name()}[{i}] has no dtype specified, defaulting to float32.")
                            aidge_dtype = aidge_core.dtype.float32
                        else:
                            aidge_dtype = aidge_node.get_operator().get_output(i).dtype
                        out_dtype = dtype_converter.aidge_to_onnx(aidge_dtype)
                    else:
                        output_tensor = aidge_operator.get_output(i)
                        output_dims = output_tensor.dims
                        out_dtype = dtype_converter.aidge_to_onnx(output_tensor.dtype)
                    onnx_outputs.append(
                        helper.make_tensor_value_info(
                            output_name,
                            out_dtype,
                            output_dims
                        )
                    )
        # Check if node is at the Input
        if aidge_node.name() in graph_inputs_name:
            # If it is the case, we create ONNX tensor for each one of the node inputs
            for i in range(aidge_node.get_nb_inputs()):
                if aidge_node.input_category(i) not in [aidge_core.InputCategory.Data, aidge_core.InputCategory.OptionalData]:
                    continue
                if aidge_node.input(i)[0] in graph_view.get_nodes():
                    continue  # This node input is not an input graph
                input_name = aidge_node.input_name(i)
                input_dims = None
                in_dtype = None

                if inputs_dims is not None:
                    # dim_name = input_name
                    node_name = aidge_node.name()
                    if old_io_names[aidge_node] in inputs_dims:
                        node_name = old_io_names[aidge_node]
                    if node_name not in inputs_dims:
                        if aidge_node.input_category(i) == aidge_core.InputCategory.OptionalData:
                            aidge_core.Log.notice(f"Optional input {aidge_node.name()}[{i}] not in inputs_dims, skipping.")
                            continue
                        raise RuntimeError(
                            f"Graph input: {node_name} has no dims specified in inputs_dims parameter.")
                    if i >= len(inputs_dims[node_name]):
                        if aidge_node.input_category(i) != aidge_core.InputCategory.OptionalData:
                            raise RuntimeError(
                                f"Graph input: {node_name} has been described with {len(inputs_dims[node_name])} inputs but it has an input #{i+1} that is mandatory.")
                        else: continue # Optional data is not described

                    input_dims = inputs_dims[node_name][i]
                    aidge_dtype = None
                    if aidge_node.get_operator().get_input(i) is None:
                        # If no input default to float32
                        aidge_dtype = aidge_core.dtype.float32
                    else:
                        aidge_dtype = aidge_node.get_operator().get_input(i).dtype
                    in_dtype = dtype_converter.aidge_to_onnx(aidge_dtype)
                else:
                    input_tensor = aidge_operator.get_input(i)
                    if not input_tensor:
                        if aidge_node.input_category(i) == aidge_core.InputCategory.OptionalData:
                            continue
                        raise RuntimeError(f"Undefined graph input {aidge_node.name()}({aidge_node.type()}#{i})")
                    # add a name to the node to create a valid input
                    if not aidge_node.name():
                        aidge_node.set_name(aidge_node.create_unique_name(f"{aidge_operator.type()}_{aidge_node.id()}"))
                    input_dims = input_tensor.dims
                    in_dtype = dtype_converter.aidge_to_onnx(input_tensor.dtype)
                onnx_inputs.append(
                    helper.make_tensor_value_info(
                        input_name,
                        in_dtype,
                        input_dims
                    )
                )

        aidge_core.Log.info(f"\tInputs: {node_inputs_name}")
        aidge_core.Log.info(f"\tOutputs: {node_outputs_name}")
        new_nodes = AIDGE_NODE_CONVERTER_[aidge_node.type()](
            aidge_node=aidge_node,
            node_inputs_name=node_inputs_name,
            node_outputs_name=node_outputs_name,
            initializer_list=onnx_initializers,
            opset=opset,
            enable_custom_op=enable_custom_op
        )
        # Add to list of onnx nodes
        onnx_nodes += new_nodes
        # Node converted, adding to close list
        closed_nodes.append(aidge_node)

    # Create the graph (GraphProto)
    # For IR versions < 4, ONNX requires that all initializers also appear in graph inputs.
    if ir_version is not None and ir_version < 4:
        existing_input_names = {value_info.name for value_info in onnx_inputs}
        for initializer in onnx_initializers:
            if initializer.name not in existing_input_names:
                onnx_inputs.append(
                    helper.make_tensor_value_info(
                        initializer.name,
                        initializer.data_type,
                        list(initializer.dims)
                    )
                )
    onnx_graph = onnx.helper.make_graph(
        nodes=onnx_nodes,
        initializer=onnx_initializers,
        name=model_name,
        inputs=onnx_inputs,
        outputs=onnx_outputs,
    )
    opset_import = []
    if enable_custom_op:
        opset_import.append(helper.make_opsetid(_AIDGE_DOMAIN, 1))
    if opset:
        opset_import.append(onnx.helper.make_opsetid("", opset))

    # Create the model (ModelProto)
    proto_model: onnx.ModelProto = onnx.helper.make_model(
        onnx_graph,
        producer_name=vars(sys.modules[__name__])['__package__'],
        producer_version=str(version("aidge_onnx")),
        opset_imports=opset_import
    )
    if ir_version:
        proto_model.ir_version = ir_version
    return proto_model

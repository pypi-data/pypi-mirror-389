"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import aidge_core
import numpy as np
from collections import defaultdict
from types import SimpleNamespace as NS
import colorama
from typing import List, Dict, Optional, Tuple
from typing_extensions import TypeAlias, deprecated

from onnx import numpy_helper
import onnx
from .node_import import ONNX_NODE_CONVERTER_, generic
from .utils import onnx_to_aidge_model_names
from . import dtype_converter
from aidge_core import Log

def load_onnx(filename: str, verbose: bool = False):
    """Load an ONNX file and convert it into a :py:class:`aidge_core.GraphView`.

    :param filename: Path to the ONNX file to load
    :type filename: str
    :param verbose: If ``True``, display information on the terminal, default=False
    :type verbose: bool, optional
    :returns: Aidge :py:class:`aidge_core.GraphView` corresponding to the ONNX model described by the onnx file  ``filename``
    :rtype: :py:class:`aidge_core.GraphView`
    """
    aidge_core.Log.info(f"Loading ONNX {filename}")

    # Load the ONNX model
    model = onnx.load(filename)
    return convert_onnx_to_aidge(model, verbose)


def has_native_coverage(graph: aidge_core.GraphView):
    """Check if a graph view is supported with only native Aidge operators
    (meaning no GenericOperator)

    :param graph: Graph view
    :type graph: aidge_core.GraphView
    :returns: True if there is no GenericOperator in the graph
    :rtype: bool
    """
    for node in graph.get_nodes():
        if isinstance(node.get_operator(), aidge_core.GenericOperatorOp):
            return False
    return True


def native_coverage_report(graph: aidge_core.GraphView):
    """Report Aidge native operators support for a graph view

    :param graph: Graph view
    :type graph: aidge_core.GraphView
    """
    if len(graph.get_nodes()) == 0:
        Log.warn("GraphView is empty, could not get a native coverage report!")
        return

    native_node_types = defaultdict(int)
    generic_node_types = defaultdict(int)

    for node in graph.get_nodes():
        if isinstance(node.get_operator(), aidge_core.GenericOperatorOp):
            generic_node_types[node.type()] += 1
        else:
            native_node_types[node.type()] += 1

    nb_native_nodes = sum(native_node_types.values())
    nb_generic_nodes = sum(generic_node_types.values())

    print(f"Native operators: {nb_native_nodes} ({len(native_node_types)} types)")
    for op, nb in sorted(native_node_types.items()):
        print(f"- {op}: {nb}")
    print(f"Generic operators: {nb_generic_nodes} ({len(generic_node_types)} types)")
    for op, nb in sorted(generic_node_types.items()):
        print(f"- {op}: {nb}")
    print(
        f"Native types coverage: {100 * len(native_node_types) / (len(native_node_types) + len(generic_node_types)):.1f}% ({len(native_node_types)}/{len(native_node_types) + len(generic_node_types)})"
    )
    print(
        f"Native operators coverage: {100 * nb_native_nodes / (nb_native_nodes + nb_generic_nodes):.1f}% ({nb_native_nodes}/{nb_native_nodes + nb_generic_nodes})"
    )

    return (native_node_types, generic_node_types)


def _get_dataflow_graph(model: onnx.ModelProto) -> NS:
    """From the given ONNX model, returns the dataflow graph over node ids

    An ONNX model graph is actually a scheduled data dependency graph, where
    the node order is expected to be a topological order of operators w.r.t.
    output value name -> input value name edges. There is no constraint on the
    uniqueness of value names, hence allowing reuse of output value names.
    Normally a data dependence graph should not have exposed uses, though
    we allow it in order to accept cyclic graphs. Any exposed use is resolved
    to the first forward definition.
    The resulting data flow graph is a set of nodes with static single
    definitions identified by the a def loc tuple (node id, output index) and uses
    identified by a use loc tuple (node id, input index). Every node definition
    or use it connected in the returned graph to either another computation node
    or one of the root nodes (intializers, inputs, undefined) or one of the sink
    nodes (outputs, ignored).
    Note that initializers take priority over inputs of the same name.
    We return the:
    - node_inputs: mapping a node id to it's ordered list of inputs (defs locs)
    - node_outputs: mapping a node id to it's ordered list of outputs (use locs lists)
    - initializers, inputs, ops, outputs, undefined, ignored: maps of nodes, a node_id
      is in exactly one of these maps

    :param graph: ONNX Model
    :type graph: onnx.ModelProto
    :returns: the data flow graph
    :rtype: A namespace containing the described information
    """
    UDLoc: TypeAlias = Tuple[str, int]
    UseLoc: TypeAlias = UDLoc
    DefLoc: TypeAlias = UDLoc
    NodeId: TypeAlias = str
    ValName: TypeAlias = str

    last_def: Dict[ValName, DefLoc] = {}
    exposed_uses: Dict[ValName, List[UseLoc]] = defaultdict(list)
    ignored_uses: List[UseLoc] = []
    use_def: Dict[UseLoc, DefLoc] = {}
    initializers: Dict[NodeId, onnx.TensorProto] = {}
    inputs: Dict[NodeId, onnx.ValueInfoProto] = {}
    ops: Dict[NodeId, onnx.NodeProto] = {}
    outputs: Dict[NodeId, onnx.ValueInfoProto] = {}
    undefined: Dict[NodeId, None] = {}
    ignored: Dict[NodeId, None] = {}
    op_defs_uses: Dict[NodeId, Tuple[List[DefLoc], List[UseLoc]]] = {}

    for inp_idx, inp in enumerate(model.graph.input):
        ident = f"inp#{inp_idx}"
        single_def = (ident, 0)
        op_defs_uses[ident] = ([single_def], [])
        inputs[ident] = inp
        if inp.name != "":
            last_def[inp.name] = single_def

    for ini_idx, ini in enumerate(model.graph.initializer):
        ident = f"ini#{ini_idx}"
        single_def = (ident, 0)
        op_defs_uses[ident] = ([single_def], [])
        initializers[ident] = ini
        if ini.name != "":
            last_def[ini.name] = single_def

    for op_idx, onnx_op in enumerate(model.graph.node):
        ident = f"nod#{op_idx}"
        ops[ident] = onnx_op
        # Update use -> def map: (input node id, input_idx) -> (output node id, output idx)
        # or mark as ignored (empty name) or exposed (forward reference)
        op_uses = []
        for input_idx, input_name in enumerate(onnx_op.input):
            use = (ident, input_idx)
            op_uses.append(use)
            if input_name == "":
                ignored_uses.append(use)
            elif input_name in last_def:
                use_def[use] = last_def[input_name]
            else:
                exposed_uses[input_name].append(use)

        # Update name -> def map: output name -> (output node id, output idx)
        # unless name is empty
        op_defs = []
        for output_idx, output_name in enumerate(onnx_op.output):
            single_def = (ident, output_idx)
            op_defs.append(single_def)
            if output_name != "":
                if output_name in exposed_uses:
                    for input_ref in exposed_uses[output_name]:
                        use_def[input_ref] = single_def
                    del exposed_uses[output_name]
                last_def[output_name] = single_def
        op_defs_uses[ident] = (op_defs, op_uses)

    for out_idx, out in enumerate(model.graph.output):
        ident = f"out#{out_idx}"
        use = (ident, 0)
        op_defs_uses[ident] = ([], [use])
        outputs[ident] = out
        if out.name == "":
            ignored_uses.append(use)
        elif out.name in last_def:
            use_def[use] = last_def[out.name]
        else:
            exposed_uses[out.name].append(use)

    for exposed_idx, uses in enumerate(exposed_uses.values()):
        ident = f"und#{exposed_idx}"
        single_def = (ident, 0)
        op_defs_uses[ident] = ([single_def], [])
        undefined[ident] = None
        for use in uses:
            use_def[use] = single_def

    for ignored_idx, use in enumerate(ignored_uses):
        ident = f"ign#{ignored_idx}"
        single_def = (ident, 0)
        op_defs_uses[ident] = ([single_def], [])
        ignored[ident] = None
        use_def[use] = single_def

    def_uses: Dict[DefLoc, List[UseLoc]] = {
        single_def: [] for defs, _ in op_defs_uses.values() for single_def in defs
    }
    for use, single_def in use_def.items():
        def_uses[single_def].append(use)

    node_inputs: Dict[NodeId, List[DefLoc]] = {}
    node_outputs: Dict[NodeId, List[List[UseLoc]]] = {}
    for node_id, (defs, uses) in op_defs_uses.items():
        node_inputs[node_id] = [use_def[use] for use in uses]
        node_outputs[node_id] = [def_uses[single_def] for single_def in defs]

    return NS(
        initializers=initializers,
        inputs=inputs,
        outputs=outputs,
        ops=ops,
        undefined=undefined,
        ignored=ignored,
        node_inputs=node_inputs,
        node_outputs=node_outputs,
    )

def _remove_unused_initializers(dfg):
    dfg.initializers = {
        init: v for (init, v) in dfg.initializers.items()
        if len(dfg.node_outputs[init][0]) > 0
    }

def _remove_unused_producers(graph: aidge_core.GraphView) -> None:
    """Remove unused producers from the GraphView.
    This can happen if an Aidge Node doesn't use an initializer.
    """
    for node in graph.get_nodes():
        if node.type() == "Producer" and not node.get_children():
            graph.remove(node)

@deprecated("Use 'convert_onnx_to_aidge' function instead")
def _load_onnx2graphview(model: onnx.ModelProto,
                         verbose: bool = False,
                         remove_unused_init:bool = True):
    return convert_onnx_to_aidge(model, verbose, remove_unused_init)

def convert_onnx_to_aidge(model: onnx.ModelProto,
                         verbose: bool = False,
                         remove_unused_init:bool = True):
    """Transform an ONNX graph to an Aidge GraphView

    :param model: ONNX graph
    :type model: onnx.ModelProto
    :param verbose: If ``True``, display information on the terminal, default=False
    :type verbose: bool, optional
    :param remove_unused_init: If ``True``, Aidge GraphView will not contains unused Initializers, default=True.
    :type remove_unused_init: bool, optional
    :returns: Aidge :py:class:`aidge_core.GraphView` corresponding to the ONNX model described by the onnx ``model``
    :rtype: :py:class:`aidge_core.GraphView`
    """
    if hasattr(model, "opset_import"):
        domains = {domain.domain: domain.version for domain in model.opset_import}
    else:
        raise RuntimeError("Cannot retrieve opset version from ONNX model.")
    aidge_core.Log.info(
            f"ONNX metadata:"
            f"\n\t- Producer name: {model.producer_name}"
            f"\n\t- Producer version: {model.producer_version}"
            f"\n\t- Opset max version: {max(domains.values())}"
        )
    model_nodes = {}  # Key : node id, Value : aidge node object
    graph: aidge_core.GraphView = aidge_core.GraphView()

    # Clean model if some issues in the model
    # might affect Aidge in the next steps
    model = onnx_to_aidge_model_names(model)

    aidge_core.Log.info("Constructing DFG...")
    dfg = _get_dataflow_graph(model)

    # Clean dataflow graph
    if remove_unused_init:
        _remove_unused_initializers(dfg)

    aidge_core.Log.info("Processing Initializers...")
    for node_id, onnx_init in dfg.initializers.items():
        values = numpy_helper.to_array(onnx_init)
        data = (
            aidge_core.Tensor(values)
            if values.shape != ()
            else aidge_core.Tensor(np.array([values.item()]))
        )
        data.set_datatype(dtype_converter.onnx_to_aidge(onnx_init.data_type))
        aidge_node = aidge_core.Producer(
            data,
            onnx_init.name,
        )
        model_nodes[node_id] = aidge_node
        if verbose:
            print(f"- Initializer: '{onnx_init.name}': {list(values.shape)}")

    aidge_core.Log.info("Processing Nodes...")
    # Get the nodes
    # Associate the ONNX nodes with Aidge Node if possible
    for node_id, onnx_node in dfg.ops.items():
        # There can be multiple opsets in a given model, each ones attached to a given domain
        # Each nodes are attached to a given opset via a domain name.
        # more on how opset work here : http://onnx.ai/sklearn-onnx/auto_tutorial/plot_cbegin_opset.html
        if onnx_node.domain in domains:
            node_opset = domains[onnx_node.domain]
        elif onnx_node.domain == "" and "ai.onnx" in domains:
            node_opset = domains["ai.onnx"] # default

        # Adding only producers to the list of inputs
        node_inputs: List[Optional[Tuple[aidge_core.Node, int]]] = []
        for out_node_id, out_idx in dfg.node_inputs[node_id]:
            if out_node_id in dfg.initializers:
                node_inputs.append((model_nodes[out_node_id], out_idx))
            else:
                node_inputs.append(None)

        try:
            aidge_node = ONNX_NODE_CONVERTER_[onnx_node.op_type.lower()](
                onnx_node, node_inputs, node_opset
            )
        except Exception as e:
            Log.warn(
                f"Trying to load node named [\033[1m\033[3m{onnx_node.name}\033[0m] of type "
                f"[\033[1m\033[3m{onnx_node.op_type}\033[0m].\n"
                "Loading node using a [\033[1m\033[3mGenericOperator\033[0m].\n"
                "Please report this issue at "
                "https://gitlab.eclipse.org/eclipse/aidge/aidge_onnx by "
                "providing your ONNX model and the following error:\n"
                f"\"ONNX_NODE_CONVERTER_ returned: {e}\""
            )
            aidge_node = None

        # If None, the node type exists but could not be converted (for instance because unsupported attribute) => fall back to generic
        if aidge_node is None:
            aidge_node = generic.import_generic(onnx_node, node_inputs, node_opset)
        assert (
            aidge_node is not None
        ), f"failed to convert node '{onnx_node.name}' of type {onnx_node.op_type} to generic."

        model_nodes[node_id] = aidge_node

    # Allow the generated Aidge nodes to ignore some trailing inputs of the original ONNX node
    for node_id in dfg.ops:
        node, inputs = model_nodes[node_id], dfg.node_inputs[node_id]
        while len(inputs) > node.get_nb_inputs():
            input_node_id, output_idx = inputs.pop()
            dfg.node_outputs[input_node_id][output_idx].remove((node_id, len(inputs)))

    aidge_core.Log.info("Connecting Nodes...")
    # Generate ordered input and add identity nodes only when necessary
    aidge_inputs = []
    for node_id, onnx_input in dfg.inputs.items():
        outputs = dfg.node_outputs[node_id][0]
        is_graph_output = bool(sum([out[0] in dfg.outputs for out in outputs]))
        if is_graph_output or len(outputs) > 1:
            input_node, input_idx = aidge_core.Identity(onnx_input.name), 0
            model_nodes[node_id] = input_node
        elif len(outputs) == 1:
            input_node_id, input_idx = outputs[0]
            input_node = model_nodes[input_node_id]
        else:
            input_node, input_idx = None, 0  # input unused
        if input_node:
            input_node.input_name(input_idx, onnx_input.name)
            # Generating Input tensors to have access to input dtype once the model is loaded
            # If input type is not Undefined
            if onnx_input.type.tensor_type.elem_type != onnx.TensorProto.UNDEFINED:
                in_tensor = aidge_core.Tensor()
                in_tensor.to_dtype(dtype_converter.onnx_to_aidge(onnx_input.type.tensor_type.elem_type))
                in_tensor.to_dformat(aidge_core.dformat.nchw)
                input_node.get_operator().set_input(
                    input_idx,
                    in_tensor
                )
        aidge_inputs.append((input_node, input_idx))
        if verbose:
            if input_node is not None:
                aidge_core.Log.debug(f"Input: '{onnx_input.name}': {input_node.name()}#{input_idx}")
            else:
                aidge_core.Log.debug(f"Input: '{onnx_input.name}': ignored")

    # Generate ordered outputs
    aidge_outputs = []
    for node_id, onnx_output in dfg.outputs.items():
        input_node_id, output_idx = dfg.node_inputs[node_id][0]
        if input_node_id not in dfg.undefined and input_node_id not in dfg.ignored:
            output_node = model_nodes[input_node_id]
        else:
            output_node, output_idx = None, 0  # output ignored or undefined
        if output_node:
            output_node.output_name(output_idx, onnx_output.name)
            if onnx_output.type.tensor_type.elem_type:
                output_node.get_operator().get_output(output_idx).to_dtype(dtype_converter.onnx_to_aidge(onnx_output.type.tensor_type.elem_type))
        aidge_outputs.append((output_node, output_idx))
        if verbose:
            if output_node is not None:
                aidge_core.Log.debug(f"Output: '{onnx_output.name}': {output_node.name()}#{output_idx}")
            else:
                aidge_core.Log.debug(f"Output: '{onnx_output.name}': ignored")

    # Link every inputs
    for node_id, inputs in dfg.node_inputs.items():
        node = model_nodes.get(node_id)
        for input_idx, (input_node_id, output_idx) in enumerate(inputs):
            input_node = model_nodes.get(input_node_id)
            if input_node is not None:
                if node is not None:
                    input_node.add_child(node, output_idx, input_idx)
                    aidge_core.Log.debug(
                            f"edge {input_node.name()}#{output_idx} -> {node.name()}#{input_idx} added"
                        )
                # Add node to the graph after updating connections
                graph.add(input_node)
            else:
                pass  # No node associated, it's a graph input
        if node is not None:
            graph.add(node)
            aidge_core.Log.debug(f"node {node.name()} added")

    if remove_unused_init:
        _remove_unused_producers(graph)

    # The final output list may differ from the onnx output list as undefined/ignored outputs are filtered
    graph.set_ordered_outputs(
        [output_ref for output_ref in aidge_outputs if output_ref[0] is not None],
        ignore_missing=True
    )

    # The final input list may differ from the onnx input list as ignored/unused inputs are filtered
    graph.set_ordered_inputs(
        [input_ref for input_ref in aidge_inputs if input_ref[0] is not None]
    )

    # ONNX only supports NCHW, by design:
    # see https://github.com/onnx/onnx/issues/369
    graph.set_dataformat(aidge_core.dformat.nchw)
    return graph

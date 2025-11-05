from . import recipe
import aidge_core
import numpy as np
from math import prod

def _epsilon(node):
    if node.type() != "Producer": return False
    tensor = node.get_operator().get_output(0)
    if tensor.size != 1: return False
    if not node.attributes().has_attr("epsilon"):
        node.attributes().add_attr("epsilon", tensor[0])
    return True

def _bias(node):
    if node.type() != "Producer": return False
    tensor = node.get_operator().get_output(0)
    if not node.attributes().has_attr("bias"):
        node.attributes().add_attr("bias", tensor)
    return True

def _scale(node):
    if node.type() != "Producer": return False
    tensor = node.get_operator().get_output(0)
    if not node.attributes().has_attr("scale"):
        node.attributes().add_attr("scale", tensor)
    return True

def _axis(node):
    axis = None
    if node.type() == "GlobalAveragePooling":
        # Keras replace ReduceMean axis=-1 in the case 3D (B,C,H)
        # with a GlobalAvgPool
        axis = -1
    if node.type() == "ReduceMean":
        # Number of dimensions
        nb_dims = len(node.get_operator().get_input(0).dims)
        # Retrieve the raw axes from the ReduceMean
        # It is a list of all axes on which to compute the mean
        # ONNX LayerNorm ask to specify the first normalization dimension
        np_axes = np.array(node.get_operator().attr.axes)
        # Set the dimension to positive integers for better comparisons
        positive_axes = [(a + nb_dims) if a < 0 else a for a in np_axes]
        # The expected axis is the lowest in the list of dims
        axis = np_axes[np.argmin(np_axes)]
        # If the ReduceMean is LayerNorm compatible then the list of dimensions
        # should contains every dimensions starting from dims to the number of dims.
        expected_axes = list(range(axis, nb_dims))
        # Axes list may be shuffled
        # For example if the dimensions were negative
        # [-1,-2] (nb_dims=4) => [3, 2] instead of [2, 3]
        positive_axes.sort()
        if not positive_axes == expected_axes:
            aidge_core.Log.debug(f"Matching reduce mean doesn't have axis compatible with ONNX def, with axis={np_axes}, expected={expected_axes} .")
            return False
    if axis is not None:
        if not node.attributes().has_attr("axis"):
            node.attributes().add_attr("axis", axis)
            node.attributes().add_attr("in_dims", node.get_operator().get_input(0).dims)
        return True
    return False

def fuse_layernorm(graph: aidge_core.GraphView, query: str) -> int:
    nb_replaced: int = 0

    spgm = aidge_core.SinglePassGraphMatching(graph)
    spgm.add_node_lambda("epsilon", _epsilon)
    spgm.add_node_lambda("bias", _bias)
    spgm.add_node_lambda("scale", _scale)
    spgm.add_node_lambda("axis", _axis)


    matches = spgm.match(query)
    for match in matches:
        try:
            # VALUE RETRIEVAL
            # Create clone so that if the recipe fail we do not alter the original graph
            matched_graph = match.graph.clone()
            mop_backend = matched_graph.root_node().get_operator().backend()
            matched_nodes = matched_graph.get_nodes()

            ### CREATE IDENTITY INPUT ###
            # Add an identity input so that LayerNormalization has only one input
            identity_node = aidge_core.Identity(name="Layernorm_in")
            if len(matched_graph.get_ordered_inputs()) != 1:
                raise ValueError("LayerNormalization match should have only one input.")
            input_node = matched_graph.get_ordered_inputs()[0][0]

            # Search for the output of the input node that is connected to our LayerNormalization.
            good_out_idx = None
            for out_idx, input_node_output in enumerate(input_node.outputs()):
                if all([input_node_child in matched_nodes for input_node_child, _ in input_node_output]):
                    if good_out_idx is not None:
                        raise RuntimeError("Two valid output when parsing the LayerNormalization parent outputs, something went wrong.")
                    good_out_idx = out_idx

            if good_out_idx is None: raise RuntimeError("Fail to find the output idx of LayerNormalization parent node.")

            for n, i in input_node.outputs()[good_out_idx]:
                matched_graph.insert_parent(n, identity_node, i, 0, 0)

            matched_graph.add(identity_node)
            input_node.remove_child(identity_node, good_out_idx)
            matched_graph.remove(input_node)

            ### RETRIEVE ATTRIBUTES ###
            epsilon = None
            axis = None
            in_dims = None
            scale_val = None
            bias_val = None
            for n in matched_graph.get_nodes():
                if n.attributes().has_attr("scale"):
                    scale_val = n.attributes().get_attr("scale")
                if n.attributes().has_attr("bias"):
                    bias_val = n.attributes().get_attr("bias")
                if n.attributes().has_attr("epsilon"):
                    epsilon = n.attributes().get_attr("epsilon")
                if n.attributes().has_attr("axis"):
                    in_dims = n.attributes().get_attr("in_dims")
                    axis = n.attributes().get_attr("axis")
            if epsilon is None:
                raise RuntimeError("Failed to retrieve epsilon value.")
            if axis is None:
                raise RuntimeError("Failed to retrieve axis value.")

            nb_feature = prod(in_dims[axis:])
            layernorm_node = aidge_core.LayerNorm(
                nb_features=nb_feature,
                axis=axis,
                epsilon=epsilon
            )

            # Bias and scale are not mandatory and are not initialized
            # with the factory function. So we add a default value
            if scale_val is None:
                scale_val = aidge_core.Tensor(dims=[nb_feature])
                scale_val.set_backend(mop_backend if mop_backend else "cpu")
                aidge_core.constant_filler(scale_val, 1.0)
            if bias_val is None:
                bias_val = aidge_core.Tensor(dims=[nb_feature])
                bias_val.set_backend(mop_backend if mop_backend else "cpu")
                aidge_core.constant_filler(bias_val, 0.0)

            # Update LayerNorm scale and bias val
            layernorm_node.get_parent(1).get_operator().set_output(0, scale_val)
            layernorm_node.get_parent(2).get_operator().set_output(0, bias_val)

            if mop_backend != "":
                layernorm_node.get_operator().set_backend(mop_backend)

            mop_graph = aidge_core.GraphView()
            mop_graph.add(layernorm_node)

            ### REPLACEMENT STEP ###
            # Remove input from the matched graph, but not from the graph we are working on
            match.graph.remove(match.graph.get_ordered_inputs()[0][0], False)
            if (not aidge_core.GraphView.replace(match.graph, mop_graph)):
                aidge_core.Log.notice("Could not replace sub-graph with meta operator")
            else:
                nb_replaced += 1

        except RuntimeError as e:
            aidge_core.Log.notice(f"Fail to fuse a LayerNorm because of:\n{e}")
    return nb_replaced


class FuseLayerNorm(recipe):
    brief = "Fuse operator to form a LayerNormalization operation."

    @staticmethod
    def is_compatible_opset(opset:int)->bool:
        # LayerNorm was introduced by opset 17
        return opset >= 17

    @staticmethod
    def apply(graph_view):

        # LayerNormalization from Torch ONNX
        fuse_layernorm(graph_view,
                    ".#0~*>ReduceMean#1~*>Sub#2~*>Pow#3->ReduceMean#4[axis]~*>Add#5->Sqrt#6~*>Div#6;"
                        ".#0~*>Sub#2~*>Div#6;"
                        "Pow#3<*~Producer;"
                        "Add#5<*~Producer[epsilon];"
                        "Div#6~*>(Mul#7~*>Add#8)?;"
                        "(Mul#7<*~Producer[scale])?;"
                        "(Add#8<*~Producer[bias])?;",
        )

        # LayerNormalization from Keras ONNX
        fuse_layernorm(graph_view,
                    ".#0~*>Sub#1~*>Mul#2->(ReduceMean#3[axis]|GlobalAveragePooling#3[axis])~*>Add#4->Sqrt#5->Reciprocal#6;"
                        ".#0~*>Mul#11~*>Add#10;"
                        ".#0~*>(ReduceMean#12|GlobalAveragePooling#12)~*>Neg#13~*>Mul#8;"
                        "(ReduceMean#12|GlobalAveragePooling#12)~*>Sub#1;"
                        "Reciprocal#6~*>(Mul#7)?;"
                        "(Reciprocal#6|(Mul#7)?)~*>Mul#8;"
                        "(Reciprocal#6|(Mul#7)?)~*>Mul#11;"
                        "Mul#8~*>(Add#9)?~*>Add#10;"
                        "(Mul#7<*~Producer[scale])?;"
                        "(Add#9<*~Producer[bias])?;"
                        "Add#4<*~Producer[epsilon];",
        )

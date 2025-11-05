import aidge_core
from . import recipe

def fuse_gelu(graph: aidge_core.GraphView, query: str, approximate: str="none") -> int:
    nb_replaced: int = 0
    spgm = aidge_core.SinglePassGraphMatching(graph)
    matches = spgm.match(query)

    for match in matches:
        try:
            # VALUE RETRIEVAL
            # Create clone so that if the recipe fail we do not alter the original graph
            matched_graph = match.graph.clone()
            mop_backend = matched_graph.root_node().get_operator().backend()
            matched_nodes = matched_graph.get_nodes()

            ### CREATE IDENTITY INPUT ###
            # Add an identity input so that GeLU has only one input
            id_node = aidge_core.Identity(name="GeLU_in")
            if len(matched_graph.get_ordered_inputs()) != 1:
                raise ValueError("GeLU should have only one input.")
            input_node = matched_graph.get_ordered_inputs()[0][0]

            # Search for the output of the input node that is connected to our GeLU.
            good_out_idx = None
            for out_idx, input_node_output in enumerate(input_node.outputs()):
                if all([input_node_child in matched_nodes for input_node_child, _ in input_node_output]):
                    if good_out_idx is not None:
                        raise RuntimeError("Two valid output hen parsing the GeLU parent outputs, something went wrong.")
                    good_out_idx = out_idx

            if good_out_idx is None: raise RuntimeError("Fail to find the output idx of GeLU parent node.")

            for n, i in input_node.outputs()[good_out_idx]:
                matched_graph.insert_parent(n, id_node, i, 0, 0)

            ### CREATE MICRO-GRAPH ###

            matched_graph.add(id_node)
            input_node.remove_child(id_node, good_out_idx)
            matched_graph.remove(input_node)

            mop = aidge_core.meta_operator("GeLU", matched_graph)
            mop.get_operator().attr.add_attr("approximate", approximate)

            if mop_backend != "":
                mop.get_operator().set_backend(mop_backend)

            mop_graph = aidge_core.GraphView()
            mop_graph.add(mop)


            # REPLACEMENT STEP
            # Remove input from the matched graph, but not from the graph we are working on
            match.graph.remove(match.graph.get_ordered_inputs()[0][0], False)
            if (not aidge_core.GraphView.replace(match.graph, mop_graph)):
                aidge_core.Log.notice("Could not replace sub-graph with meta operator")
            else:
                nb_replaced += 1

        except RuntimeError as e:
            aidge_core.Log.notice(f"Fail to fuse a GeLU because of:\n{e}")
    return nb_replaced

class FuseGeLU(recipe):
    brief = "Fuse operators to form a GeLU operation."

    @staticmethod
    def is_compatible_opset(opset:int)->bool:
        # Gelu was introduced by opset 20
        return opset >= 20

    @staticmethod
    def apply(graph_view):
        # GeLU from Torch ONNX
        fuse_gelu(graph_view,
                    ".#0~*>Div#1->Erf->Add#1-0-1>Mul#1->Mul#2;"
                        ".#0~>Mul#1;"
                        "Div#1<1~Producer;"
                        "Add#1<*~Producer;"
                        "Mul#2<*~Producer",
                    approximate = "none"
        )
        fuse_gelu(graph_view,
                    ".#0~*>Mul#1~*>Mul#2~*>Mul#3~*>Add#4~*>Mul#5->Tanh~*>Add#6~*>Mul#7~*>Mul#8;"
                        ".#0~*>Mul#2;"
                        ".#0~*>Add#4;"
                        ".#0~*>Mul#7;"
                        "Mul#3<*~Producer;"
                        "Mul#5<*~Producer;"
                        "Add#6<*~Producer;"
                        "Mul#8<*~Producer",
                    approximate = "tanh"
        )
        # GeLU from Keras ONNX
        fuse_gelu(graph_view,
            ".#0;"
                ".#0~0-1>Mul#1->Mul#4;"
                ".#0~0-0>Mul#2-0-0>Erf#6-0-1>Add#7-0-1>Mul#4;"
                "Mul#1<0-0-Producer#3;"
                "Mul#1-0-0>Mul#4;"
                "Mul#2<1-0-Producer#5;"
                "Add#7<0-0-Producer#8",
            approximate = "none"
        )
        fuse_gelu(graph_view,
                ".#0~*>Pow#0~*>Mul#0~*>Add#1~*>Mul#2~*>Tanh~*>Add#3~*>Mul#4;"
                ".#0~*>Add#1;"
                ".#0~*>Mul#5;"
                "Mul#5<*~Producer;"
                "Mul#0<*~Producer;"
                "Mul#2<*~Producer;"
                "Add#3<*~Producer;"
                "Pow#0<*~Producer;",
            approximate = "tanh"
        )



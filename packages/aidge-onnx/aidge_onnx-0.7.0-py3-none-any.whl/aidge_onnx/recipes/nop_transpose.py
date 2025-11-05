from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopTranspose(recipe):
    brief = "Remove Transpose if transposition order is not modified."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node:  node.get_operator().attr.output_dims_order == list(range(len(node.get_operator().get_input(0).dims))))
        matches = gm.match("Transpose[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

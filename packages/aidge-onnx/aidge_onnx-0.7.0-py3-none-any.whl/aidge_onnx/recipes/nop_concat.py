from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopConcat(recipe):
    brief = "Remove Concat with only one input."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: node.get_operator().nb_inputs() == 1)
        matches = gm.match("Concat[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

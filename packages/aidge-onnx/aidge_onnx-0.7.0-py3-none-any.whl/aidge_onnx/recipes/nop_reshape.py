from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopReshape(recipe):
    brief = "Remove Reshape if input shape is already the same as shape argument."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: node.get_operator().attr.shape == node.get_operator().get_input(0).dims)
        matches = gm.match("Reshape[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

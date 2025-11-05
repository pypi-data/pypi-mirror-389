from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopFlatten(recipe):
    brief = "Remove Flatten if input is already flatten."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: node.get_operator().axis() + 1 == len(node.get_operator().get_input(0).dims))
        matches = gm.match("Flatten[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopCast(recipe):
    brief = "Remove Cast with 'to' attribute that is already the input type."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: node.get_operator().target_type() == node.get_operator().get_input(0).dtype)
        matches = gm.match("Cast[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

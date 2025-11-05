from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopPad(recipe):
    brief = "Remove Pad if no Pad is added (Padding size is 0)."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: all(p_size == 0 for p_size in node.get_operator().attr.pads))
        matches = gm.match("Pad[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

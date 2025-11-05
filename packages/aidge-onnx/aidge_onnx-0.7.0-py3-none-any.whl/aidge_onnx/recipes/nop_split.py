from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class NopSplit(recipe):
    brief = "Remove Split if it does not split the input."

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)

        gm.add_node_lambda("nop", lambda node: len(node.outputs()) == 1)
        matches = gm.match("Split[nop]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

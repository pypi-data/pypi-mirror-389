from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class RemoveDropOut(recipe):
    brief = "Remove Dropout nodes that are used only for learning (training unsafe)."
    training_safe=False

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)
        matches = gm.match("Dropout")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

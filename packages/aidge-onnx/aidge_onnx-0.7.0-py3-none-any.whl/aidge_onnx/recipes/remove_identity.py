from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

class RemoveIdentity(recipe):
    brief = "Remove identity nodes from graph, except if it is a graph input with two nodes connected to it."

    @staticmethod
    def apply(graph_view):
        input_nodes = graph_view.get_input_nodes()
        gm = SinglePassGraphMatching(graph_view)
        gm.add_node_lambda("that_will_not_create_multiple_inputs", lambda node: (node not in input_nodes or len(node.get_children()) < 2))
        matches = gm.match("Identity[that_will_not_create_multiple_inputs]")
        for match in matches:
            GraphView.replace(match.graph.get_nodes(), set())

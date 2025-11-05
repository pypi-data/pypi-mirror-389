from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

def nopAddOr(graph_view):
    gm = SinglePassGraphMatching(graph_view)
    gm.add_node_lambda("nop", lambda node: all(val == 0 for val in node.get_operator().get_output(0)))
    matches = gm.match("Producer[nop]-*>(Add|Or)")
    for match in matches:
        GraphView.replace(match.graph.get_nodes(), set())

def nopMulAnd(graph_view):
    gm = SinglePassGraphMatching(graph_view)
    gm.add_node_lambda("nop", lambda node: all(val == 1 for val in node.get_operator().get_output(0)))
    matches = gm.match("Producer[nop]-*>(Mul|And)")
    for match in matches:
        GraphView.replace(match.graph.get_nodes(), set())

def nopSub(graph_view):
    gm = SinglePassGraphMatching(graph_view)
    gm.add_node_lambda("nop", lambda node: all(val == 0 for val in node.get_operator().get_output(0)))
    matches = gm.match("Producer[nop]-0-1>Sub")
    for match in matches:
        GraphView.replace(match.graph.get_nodes(), set())

def nopDivPow(graph_view):
    gm = SinglePassGraphMatching(graph_view)
    gm.add_node_lambda("nop", lambda node: all(val == 1 for val in node.get_operator().get_output(0)))
    matches = gm.match("Producer[nop]-0-1>(Div|Pow)")
    for match in matches:
        GraphView.replace(match.graph.get_nodes(), set())

class NopElemWise(recipe):
    brief = "Remove elementwise operators (Add, Sub, Mul, Div, Pow, And, Or) that act as no-ops because of their identity behavior with respect to the input tensor."

    @staticmethod
    def apply(graph_view):
        nopAddOr(graph_view)
        nopMulAnd(graph_view)
        nopSub(graph_view)
        nopDivPow(graph_view)


from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe

IDEMPOTENT_NODES = ["ReLU", "Reshape", "Ceil", "Floor", "Round"]

class RemoveIdempotent(recipe):
    brief = f"Remove idempotent nodes that follow each other. Idempotent nodes are: {', '.join(IDEMPOTENT_NODES)}"

    @staticmethod
    def apply(graph_view):
        gm = SinglePassGraphMatching(graph_view)
        for node_type in IDEMPOTENT_NODES:
            # Note: Reshape as a 'shape' input that we need to match in order
            # to remove it, this is why we match an optional Producer on input 1
            # of the first idempotent node.
            # We match but do not capture the second idempotent node as we want to
            # remove only the first one.
            matches = gm.match(f"{node_type}#0->^{node_type}#1; {node_type}#0<1-0-Producer?")
            for match in matches:
                if not GraphView.replace(match.graph.get_nodes(), set()):
                    raise RuntimeError(f"Failed to replace idempotent operator {node_type}")

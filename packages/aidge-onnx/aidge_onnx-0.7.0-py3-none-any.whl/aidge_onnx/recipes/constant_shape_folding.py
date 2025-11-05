from aidge_core import constant_shape_folding
from . import recipe

class ConstantShapeFolding(recipe):
    brief = "Fold constant and shape node."

    @staticmethod
    def apply(graph_view):
        constant_shape_folding(graph_view)
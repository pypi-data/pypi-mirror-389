from aidge_core import matmul_to_fc
from . import recipe

class FuseMatMulAddToFC(recipe):
    brief = "Fuse MatMul and Add in a Gemm operator."

    @staticmethod
    def apply(graph_view):
        matmul_to_fc(graph_view)
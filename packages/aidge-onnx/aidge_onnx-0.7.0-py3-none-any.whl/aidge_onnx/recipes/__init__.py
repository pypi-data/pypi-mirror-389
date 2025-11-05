from aidge_core import GraphView
from abc import ABC, abstractmethod

class recipe(ABC):
    brief: str = ""
    accuracy_safe=True
    training_safe=True

    @staticmethod
    @abstractmethod
    def apply(graph_view: GraphView)->None:
        """Recipe function that transform the graph.
        """
        pass

    @staticmethod
    def is_compatible_opset(opset:int)->bool:
        """Method to override if the recipe is compatible
        with only certain opset versions.
        """
        return True
from .constant_shape_folding import ConstantShapeFolding
from .fuse_batchnorm import FuseBatchNorm
from .fuse_duplicate_producers import FuseDuplicateProducers
from .fuse_gelu import FuseGeLU
from .fuse_layernorm import FuseLayerNorm
from .fuse_matmul_to_gemm import FuseMatMulAddToFC
from .fuse_pad_with_conv import FusePadWithConv
from .nop_cast import NopCast
from .nop_concat import NopConcat
from .nop_elemwise import NopElemWise
from .nop_flatten import NopFlatten
from .nop_pad import NopPad
from .nop_reshape import NopReshape
from .nop_split import NopSplit
from .nop_transpose import NopTranspose
from .remove_dropout import RemoveDropOut
from .remove_identity import RemoveIdentity
from .remove_idempotent import RemoveIdempotent

RECIPES: list[type[recipe]]  = [
    ConstantShapeFolding,
    # Fuse
    FuseBatchNorm,
    FuseGeLU,
    FuseLayerNorm,
    FuseMatMulAddToFC,
    FusePadWithConv,
    # Nop
    NopCast,
    NopConcat,
    NopElemWise,
    NopFlatten,
    NopPad,
    NopReshape,
    NopSplit,
    NopTranspose,
    # Remove
    RemoveDropOut,
    RemoveIdempotent,
    # Finalize
    RemoveIdentity,
    FuseDuplicateProducers
]

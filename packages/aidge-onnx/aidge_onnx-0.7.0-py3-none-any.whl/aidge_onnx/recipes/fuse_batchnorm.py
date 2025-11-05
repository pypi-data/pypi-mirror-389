from aidge_core import fuse_batchnorm
from . import recipe

class FuseBatchNorm(recipe):
    brief = "Fuse BatchNormalization layer with previous Conv or FC layer."
    training_safe=False

    @staticmethod
    def apply(graph_view):
        fuse_batchnorm(graph_view)
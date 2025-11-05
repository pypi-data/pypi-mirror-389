from aidge_core import fuse_to_metaops
from . import recipe

class FusePadWithConv(recipe):
    brief = "Remove Pad layer before Conv (or ConvDepthWise) layer and update the Conv Padding attribute."

    @staticmethod
    def apply(graph_view):
        for x in range(4):
            fuse_to_metaops(
                graph_view,
                f"Pad->(Conv{x}D)",
                f"PaddedConv{x}D",
                lambda g : g.set_optional_data_last()
            )
            fuse_to_metaops(
                graph_view,
                f"Pad->(ConvDepthWise{x}D)",
                f"PaddedConvDepthWise{x}D",
                lambda g : g.set_optional_data_last()
            )

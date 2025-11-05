from aidge_core import GraphView, SinglePassGraphMatching
from . import recipe
import numpy as np
import hashlib
from collections import defaultdict

class FuseDuplicateProducers(recipe):
    brief = "Fuse producers node with the same values."
    training_safe=False

    @staticmethod
    def apply(graph_view):

        producers = [n for n in graph_view.get_nodes() if n.type() == "Producer"]
        map = defaultdict(list)

        for i, producer in enumerate(producers):
            np_tensor = np.array(producer.get_operator().get_output(0))

            # In order to compare float with a tolerance, we round values.
            if not np.issubdtype(np_tensor.dtype, np.integer):
                # Tolerance is 10^-6
                np_tensor = np.round(np_tensor, 6)

            key = (
                np_tensor.dtype,
                np_tensor.shape,
                hashlib.sha256(np_tensor.tobytes()).hexdigest()
            )

            map[key].append(i)

        for idx_list in map.values():
            if len(idx_list) > 1:
                for i in idx_list[1:]:
                    # Note: Producer have only one output this simplify
                    # the code as we don't need to loop on output idx.
                    for child, child_in_idx in producers[i].outputs()[0]:
                        producers[i].remove_child(child)
                        producers[0].add_child(child, 0, child_in_idx)
                    graph_view.remove(producers[i])
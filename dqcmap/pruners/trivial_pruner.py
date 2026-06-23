import copy
import logging
import random

from qiskit.transpiler.coupling import CouplingMap

from dqcmap.basepruner import BasePruner
from dqcmap.exceptions import DqcMapException

logger = logging.getLogger(__name__)


class TrivialPruner(BasePruner):
    """Randomly prune inter-subgraph edges of the coupling map.

    A fraction ``prob`` of the directed edges that cross controller boundaries
    is removed at random. Several seeds are tried until a pruning is found that
    both keeps the coupling map connected and retains every physical qubit
    (see :meth:`BasePruner._retains_all_nodes`); otherwise a
    :class:`DqcMapException` is raised.
    """

    def __init__(self, sg_nodes_lst, coupling_map, prob: float = 0.5, seed: int = 1900):
        super().__init__(sg_nodes_lst, coupling_map)

        if not (prob >= 0 and prob < 1):
            raise ValueError("Pruning probability should be in [0, 1)")
        self._prob = prob
        self._base_seed = seed

    def run(self):
        """
        Just randomly remove some connections between different subgraphs,
        note that we should keep the coupling map connected
        """
        num_pruned = int(len(self._edges) * self._prob)

        if num_pruned == 0:
            logger.warning(
                "No edges to prune, consider increasing the pruning probability"
            )

        for i in range(10):
            random.seed(self._base_seed + i)
            random.shuffle(self._edges)
            pruned_edges = self._edges[:num_pruned]

            # deepcopy is used to avoid modifying original coupling_map
            cm_lst = copy.deepcopy(self._cm)

            for e in pruned_edges:
                cm_lst.remove(e)

            # return if coupling map is still connected and no node was dropped
            cm = CouplingMap(cm_lst)

            if cm.is_connected() and self._retains_all_nodes(cm_lst):
                return cm_lst

        raise DqcMapException(
            f"{self.__class__} failed to generate a valid prunning pattern to keep the original coupling map connected"
        )

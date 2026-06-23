from abc import ABC, abstractmethod
from typing import Any, List


class BasePruner(ABC):
    def __init__(self, sg_nodes_lst, coupling_map: List[List[int]]):
        """Initialization of a pruner

        Args:
            sg_nodes_lst: List of subgraph node lists, a subgraph means physical qubits
                within this subgraph are controlled by the same controller.
            coupling_map: coupling map in couplinglist format.
        """
        self._cm = coupling_map

        # mapping between physical qubit index and subgraph index
        self._pq2sg = None

        # edges between different subgraphs
        self._edges = self._get_edges_inter_sg(sg_nodes_lst, coupling_map)

        # All physical qubits present in the original coupling map. Pruning must
        # not drop any of them: removing every edge incident to a node would
        # silently shrink the device (the node disappears from the resulting
        # CouplingMap), which `is_connected()` alone does not catch.
        self._all_nodes = {pq for e in coupling_map for pq in e}

    def _get_edges_inter_sg(self, sg_nodes_lst, coupling_map):
        """Analyze the connections between different subgraphs"""
        pq2sg = {}
        edges = []
        for sg_id, sg_nodes in enumerate(sg_nodes_lst):
            for pq in sg_nodes:
                pq2sg[pq] = sg_id

        for e in coupling_map:
            assert len(e) == 2
            sg_0, sg_1 = pq2sg[e[0]], pq2sg[e[1]]
            if sg_0 != sg_1:
                edges.append(e)

        self._pq2sg = pq2sg

        return edges

    def _retains_all_nodes(self, cm_lst: List[List[int]]) -> bool:
        """Return True iff every physical qubit in the original coupling map
        still appears in the pruned coupling list ``cm_lst``.

        Used to reject pruning candidates that drop a node by removing all of
        its incident edges.
        """
        remaining = {pq for e in cm_lst for pq in e}
        return remaining >= self._all_nodes

    @abstractmethod
    def run(self) -> Any:
        """Prune the edges between subgraphs and return the couplinglist after pruning"""

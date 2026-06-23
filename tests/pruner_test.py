from qiskit.transpiler.coupling import CouplingMap

from dqcmap.pruners import TrivialPruner, TrivialPrunerV2
from dqcmap.pruners.mapping_aware import MappingAwarePruner

"""
Consider following coupling map

0--1--2
|  |  |
3--4--5

Subgraphs are

0   1   2
|   |   |
3 , 4,  5

"""

CM = [
    [0, 1],
    [1, 0],
    [1, 2],
    [2, 1],
    [0, 3],
    [3, 0],
    [3, 4],
    [4, 3],
    [1, 4],
    [4, 1],
    [4, 5],
    [5, 4],
    [2, 5],
    [5, 2],
]
SG_NODES_LIST = [[0, 3], [1, 4], [2, 5]]

MAPPING = [1, 3, 5, 4, 2, 0]

MULTI_OP_LIST = [[5, 0], [0, 4]]


class TestPruners:
    pruner = TrivialPruner(SG_NODES_LIST, CM)
    pruner_v2 = TrivialPrunerV2(SG_NODES_LIST, CM)
    mapaware_pruner = MappingAwarePruner(
        SG_NODES_LIST, CM, prob=0.4, mapping=MAPPING, multi_op_list=MULTI_OP_LIST
    )

    def test_edges_inter_sg(self):
        expected_edges = [
            [0, 1],
            [1, 0],
            [3, 4],
            [4, 3],
            [1, 2],
            [2, 1],
            [4, 5],
            [5, 4],
        ]

        for e in expected_edges:
            assert e in self.pruner._edges

    def test_pq2sg(self):
        """Test if the subgraph to physical qubit mapping is as expected"""
        assert self.pruner._pq2sg is not None
        assert self.pruner._pq2sg[0] == 0
        assert self.pruner._pq2sg[3] == 0
        assert self.pruner._pq2sg[1] == 1
        assert self.pruner._pq2sg[4] == 1
        assert self.pruner._pq2sg[2] == 2
        assert self.pruner._pq2sg[5] == 2

    def test_pruner_run(self):
        cm = self.pruner.run()
        assert len(cm) < len(self.pruner._cm)

    def test_pruner_v2_run(self):
        cm = self.pruner_v2.run()
        assert len(cm) < len(self.pruner_v2._cm)

        pruned_set = set()
        original_set = set()

        for e in self.pruner_v2._cm:
            original_set.add(tuple(e))
        for e in cm:
            pruned_set.add(tuple(e))

        for e in original_set - pruned_set:
            reverse = (e[1], e[0])
            assert reverse not in pruned_set

    def test_mapaware_pruner_score(self):
        scores = self.mapaware_pruner._score_edges(MAPPING, MULTI_OP_LIST)

        expected_scores = [
            ([0, 1], 1),
            ([1, 0], 1),
            ([3, 4], 0),
            ([4, 3], 0),
            ([1, 2], 1),
            ([2, 1], 1),
            ([4, 5], 0),
            ([5, 4], 0),
        ]

        for s in scores:
            assert s in expected_scores

    def test_mapaware_pruner_run(self):
        cm = self.mapaware_pruner.run()

        expected_remaining_edges = [[0, 1], [1, 0], [1, 2], [2, 1]]

        expected_pruned_edges = [[3, 4], [4, 3], [4, 5], [5, 4]]

        for e in expected_remaining_edges:
            assert e in cm or e.reverse() in cm

        flag = False
        for e in expected_pruned_edges:
            if e not in cm and e.reverse() not in cm:
                flag = True

        assert flag

    def test_retains_all_nodes_helper(self):
        """The retention check accepts a full coupling list and rejects one
        that has dropped a physical qubit (node)."""
        assert self.pruner._retains_all_nodes(CM)

        # Drop every edge incident to node 5 -> node 5 no longer appears.
        cm_missing_node = [e for e in CM if 5 not in e]
        assert not self.pruner._retains_all_nodes(cm_missing_node)


# A coupling map where node 4 forms a singleton subgraph and connects to the
# rest *only* through inter-subgraph edges, while subgraphs A and B are joined
# by two redundant edges (0-2 and 1-2). Pruning the single 3-4 edge would
# disconnect node 4 from the graph yet leave {0,1,2,3} connected -- the exact
# situation the old pruners failed to reject.
SINGLETON_CM = [
    [0, 1],
    [1, 0],
    [0, 2],
    [2, 0],
    [1, 2],
    [2, 1],
    [2, 3],
    [3, 2],
    [3, 4],
    [4, 3],
]
SINGLETON_SG = [[0, 1], [2, 3], [4]]


class TestPrunerNodeRetention:
    def test_pruner_retains_all_nodes(self):
        pruner = TrivialPruner(SINGLETON_SG, SINGLETON_CM, prob=0.5)
        pruned = pruner.run()

        nodes = {pq for e in pruned for pq in e}
        assert nodes == {0, 1, 2, 3, 4}  # node 4 must not be dropped
        assert CouplingMap(pruned).is_connected()

    def test_pruner_v2_retains_all_nodes(self):
        pruner = TrivialPrunerV2(SINGLETON_SG, SINGLETON_CM, prob=0.5)
        pruned = pruner.run()

        nodes = {pq for e in pruned for pq in e}
        assert nodes == {0, 1, 2, 3, 4}
        assert CouplingMap(pruned).is_connected()

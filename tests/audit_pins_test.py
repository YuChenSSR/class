"""Regression pins added by the Phase-3 correctness audit (quantum-repo-to-paper).

Each test freezes a value or property that was verified by at least two
independent methods (analytic anchor, oracle simulation, or brute-force
recount). See docs/health-check-report.md section 3 for the audit table.

Notes on determinism: the KL mapper uses a wall-clock time budget
(iter_KL_mapper.py, time_limit = 4.0 s) and qiskit's default SabreLayout
trial count depends on CPU count, so end-to-end transpilation outputs are
only guaranteed reproducible on a fixed machine configuration. Pins below
therefore assert either machine-independent arithmetic, semantic
equivalence, or inequalities that encode the paper's claim, not exact
transpiler outputs.
"""

from math import isclose

import pytest
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.providers.fake_provider import Fake5QV1
from qiskit_aer import AerSimulator

from dqcmap.circuit_prop import CircProperty
from dqcmap.compilers.multi_ctrl_compiler import MultiCtrlCompiler
from dqcmap.controller import ControllerConfig, MapStratety
from dqcmap.evaluator import EvalV2
from dqcmap.mappers.iter_KL_mapper import KLMapper
from dqcmap.utils import get_cif_qubit_pairs


def _teleportation_circuit() -> QuantumCircuit:
    """Standard teleportation of |1> from q0 to q2 with c_if corrections.

    Analytic anchor: the final measurement of q2 must always yield 1.
    """
    qr = QuantumRegister(3, "q")
    cr = ClassicalRegister(3, "c")
    qc = QuantumCircuit(qr, cr)
    qc.x(0)  # state to teleport: |1>
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(1, 1)
    qc.x(2).c_if(cr[1], 1)
    qc.z(2).c_if(cr[0], 1)
    qc.measure(2, 2)
    return qc


def _cross_ctrl_pair_count(tqc: QuantumCircuit, pq2c) -> int:
    """Independent brute-force recount of cross-controller cif pairs.

    Re-implements the counting semantics without using dqcmap.evaluator,
    to serve as an oracle for EvalV2.calc_ctrl_latency bookkeeping.
    """
    pairs = get_cif_qubit_pairs(tqc)
    count = 0
    for targ, cond in pairs:
        if pq2c[targ._index] != pq2c[cond._index]:
            count += 1
    return count


class TestEvalV2Anchors:
    """B1 analytic anchor: hand-computed latency arithmetic for EvalV2."""

    def test_gate_latency_hand_computed(self):
        # 2 one-qubit ops (2 x 20 ns) + 1 two-qubit op (40 ns) = 80 ns.
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.h(1)
        qc.cx(0, 1)
        qc.measure(0, 0)  # measures must not be counted
        conf = ControllerConfig(127, 10)
        ev = EvalV2(conf)
        assert isclose(ev.calc_orig_latency(qc, backend=None), 8e-8)

    def test_ctrl_latency_hand_computed(self):
        # Trivial partition of 127 qubits over 10 controllers puts
        # 13 qubits per controller in the first groups: pair [1, 0] is
        # intra-controller (50 ns), pair [3, 15] is inter (500 ns).
        conf = ControllerConfig(127, 10)
        ev = EvalV2(conf)
        latency = ev.calc_ctrl_latency([[1, 0], [3, 15]])
        assert isclose(latency, 5e-8 + 5e-7)
        assert ev.num_cif_pairs == 1  # only the inter-controller pair

    def test_creg_condition_pairs_hand_derived(self):
        # ClassicalRegister-wide condition must pair the conditioned qubit
        # with every qubit measured into that register so far.
        qc = QuantumCircuit(3, 2)
        qc.measure(0, 0)
        qc.measure(1, 1)
        qc.h(2).c_if(qc.cregs[0], 3)
        pairs = get_cif_qubit_pairs(qc)
        idx_pairs = sorted([q0._index, q1._index] for q0, q1 in pairs)
        assert idx_pairs == [[2, 0], [2, 1]]


class TestCompilerSemanticEquivalence:
    """B2/D1 oracle: CLASS-transpiled dynamic circuit must preserve the
    teleportation outcome distribution (ideal Aer simulation)."""

    @pytest.fixture(scope="class")
    def compiled(self):
        dev = Fake5QV1()
        cm = dev.configuration().coupling_map
        conf = ControllerConfig(5, 2, strategy=MapStratety.CONNECT, cm=cm)
        compiler = MultiCtrlCompiler(conf)
        qc = _teleportation_circuit()
        tqc = compiler.run(
            qc,
            backend=dev,
            routing_method="dqcswap",
            seed_transpiler=1900,
            opt_level=6,
            heuristic="dqcmap",
            swap_trials=5,
        )
        return conf, qc, tqc

    def test_teleportation_outcome_preserved(self, compiled):
        _, qc, tqc = compiled
        shots = 4096
        sim = AerSimulator(seed_simulator=7)
        for circ in (qc, tqc):
            counts = sim.run(circ, shots=shots).result().get_counts()
            # clbit c2 (leftmost in the little-endian counts string) must
            # always read 1: teleported state is |1>.
            for bitstring, n in counts.items():
                assert bitstring[0] == "1", (
                    f"teleportation broken: outcome {bitstring} x{n}"
                )

    def test_num_cif_pairs_matches_bruteforce(self, compiled):
        conf, _, tqc = compiled
        ev = EvalV2(conf)
        ev(tqc, backend=None)
        assert ev.num_cif_pairs == _cross_ctrl_pair_count(tqc, conf.pq_to_ctrl)


class TestKLMapperInvariants:
    """B3/D3 property checks for the KL-partition mapper."""

    def _make_inputs(self):
        qc = QuantumCircuit(6, 6)
        for q in range(5):
            qc.measure(q, q)
            qc.h(q + 1).c_if(q, 1)
        cm = [[i, i + 1] for i in range(11)] + [[11, 0]]
        conf = ControllerConfig(12, 3, strategy=MapStratety.CONNECT, cm=cm)
        return conf, CircProperty(qc)

    def test_mapping_is_valid_injection(self):
        conf, prop = self._make_inputs()
        mapper = KLMapper(conf, prop)
        mapping = mapper.run()
        assert len(mapping) == prop.num_qubits
        assert len(set(mapping)) == len(mapping)  # injective
        all_pqs = {pq for pqs in conf.ctrl_to_pq.values() for pq in pqs}
        assert set(mapping) <= all_pqs

    def test_evaluate_mapping_matches_bruteforce(self):
        conf, prop = self._make_inputs()
        mapper = KLMapper(conf, prop)
        mapping = mapper.run()
        # independent recount of the objective
        pq2c = conf.pq_to_ctrl
        expected = sum(
            1 for q1, q2 in prop.cif_pairs if pq2c[mapping[q1]] != pq2c[mapping[q2]]
        )
        assert mapper.evaluate_mapping(mapping) == expected


class TestBenchRegressionPins:
    """Claim-level pin: on pe_20 with 4 controllers, CLASS (opt 6, dqcswap)
    must produce strictly fewer cross-controller feedback pairs than the
    Qiskit SABRE baseline. This is the headline Table-II relationship;
    exact values are machine-configuration-sensitive (KL wall-clock budget,
    CPU-count-dependent SabreLayout trials) and are not pinned.
    """

    def test_pe20_class_beats_baseline(self):
        import os

        from qiskit.providers.fake_provider import Fake127QPulseV1

        from dqcmap.compilers import QiskitDefaultCompiler

        qasm = "benchmarks/veriq-benchmark/dynamic/pe/dqc_pe_20.qasm"
        assert os.path.exists(qasm)
        qc = QuantumCircuit.from_qasm_file(qasm)

        dev = Fake127QPulseV1()
        cm = dev.configuration().coupling_map
        conf = ControllerConfig(127, 4, strategy=MapStratety.CONNECT, cm=cm)
        ev = EvalV2(conf)

        base = QiskitDefaultCompiler(conf).run(
            qc, backend=dev, layout_method="sabre", routing_method="sabre",
            seed_transpiler=1900,
        )
        ev(base, backend=None)
        baseline_pairs = ev.num_cif_pairs

        tqc = MultiCtrlCompiler(conf).run(
            qc, backend=dev, routing_method="dqcswap", seed_transpiler=1900,
            opt_level=6, heuristic="dqcmap", swap_trials=5,
        )
        ev(tqc, backend=None)
        class_pairs = ev.num_cif_pairs

        assert class_pairs < baseline_pairs, (
            f"CLASS ({class_pairs}) not better than baseline ({baseline_pairs})"
        )

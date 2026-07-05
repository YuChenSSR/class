"""Pins for the opt-in improvement hooks added in the Phase-4/5 pass
(quantum-repo-to-paper, improvement engagement).

Everything here guards two properties:
  1. the new switches actually do what they claim, and
  2. leaving them at their defaults reproduces the historical behavior
     bit-for-bit (the published numbers must not silently change).
"""

from math import isclose

import pytest
from qiskit import QuantumCircuit

from dqcmap.circuit_prop import CircProperty
from dqcmap.controller import ControllerConfig, MapStratety
from dqcmap.evaluator import EvalV2
from dqcmap.mappers.iter_KL_mapper import KLMapper


def _two_h_one_cx() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.h(1)
    qc.cx(0, 1)
    qc.measure(0, 0)
    return qc


class TestEvalV2GateTimeParams:
    def test_default_times_unchanged(self):
        # 2 x 20 ns + 40 ns = 80 ns; identical to the pre-change constant path
        conf = ControllerConfig(127, 10)
        ev = EvalV2(conf)
        assert isclose(ev.calc_orig_latency(_two_h_one_cx(), backend=None), 8e-8)

    def test_custom_2q_time_scales(self):
        # t_2q = 40 ns * 0.2 = 8 ns -> total 2 x 20 + 8 = 48 ns
        conf = ControllerConfig(127, 10)
        ev = EvalV2(conf, t_2q=EvalV2.DEFAULT_T_2Q * 0.2)
        assert isclose(ev.calc_orig_latency(_two_h_one_cx(), backend=None), 4.8e-8)

    def test_custom_1q_time_scales(self):
        # t_1q = 10 ns -> total 2 x 10 + 40 = 60 ns
        conf = ControllerConfig(127, 10)
        ev = EvalV2(conf, t_1q=1e-8)
        assert isclose(ev.calc_orig_latency(_two_h_one_cx(), backend=None), 6e-8)


class TestKLMapperDeterminismOptions:
    def _make_inputs(self):
        qc = QuantumCircuit(6, 6)
        for q in range(5):
            qc.measure(q, q)
            qc.h(q + 1).c_if(q, 1)
        cm = [[i, i + 1] for i in range(11)] + [[11, 0]]
        conf = ControllerConfig(12, 3, strategy=MapStratety.CONNECT, cm=cm)
        return conf, CircProperty(qc)

    def test_max_iters_with_seed_is_reproducible(self):
        conf, prop = self._make_inputs()
        m1 = KLMapper(conf, prop, max_iters=20, rng_seed=123).run()
        m2 = KLMapper(conf, prop, max_iters=20, rng_seed=123).run()
        assert m1 == m2

    def test_seeded_mapping_is_valid_and_scored_consistently(self):
        conf, prop = self._make_inputs()
        mapper = KLMapper(conf, prop, max_iters=20, rng_seed=123)
        mapping = mapper.run()
        assert len(mapping) == prop.num_qubits
        assert len(set(mapping)) == len(mapping)
        pq2c = conf.pq_to_ctrl
        expected = sum(
            1 for q1, q2 in prop.cif_pairs if pq2c[mapping[q1]] != pq2c[mapping[q2]]
        )
        assert mapper.evaluate_mapping(mapping) == expected

    def test_default_constructor_still_works(self):
        # legacy call signature (wall-clock budget, module-global RNG)
        conf, prop = self._make_inputs()
        mapping = KLMapper(conf, prop).run()
        assert len(set(mapping)) == prop.num_qubits


class TestLayoutHeuristicSwitch:
    """The layout-stage heuristic override must (a) accept the documented
    values and produce a valid circuit, and (b) leave results unchanged when
    unset or set to the same value as the routing heuristic."""

    @pytest.fixture(scope="class")
    def setup(self):
        from qiskit.providers.fake_provider import Fake5QV1

        dev = Fake5QV1()
        cm = dev.configuration().coupling_map
        conf = ControllerConfig(5, 2, strategy=MapStratety.CONNECT, cm=cm)

        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.x(2).c_if(0, 1)
        qc.cx(1, 2)
        qc.measure(1, 1)
        qc.z(2).c_if(1, 1)
        qc.measure(2, 2)
        return dev, conf, qc

    def _compile(self, setup, layout_heuristic):
        from dqcmap.compilers.multi_ctrl_compiler import MultiCtrlCompiler

        dev, conf, qc = setup
        return MultiCtrlCompiler(conf).run(
            qc,
            backend=dev,
            routing_method="dqcswap",
            seed_transpiler=1900,
            opt_level=6,
            heuristic="dqcmap",
            swap_trials=5,
            layout_heuristic=layout_heuristic,
        )

    def test_none_equals_explicit_same_value(self, setup):
        # layout_heuristic=None must behave exactly like "dqcmap" here,
        # because the routing heuristic is "dqcmap"
        t_default = self._compile(setup, None)
        t_same = self._compile(setup, "dqcmap")
        assert t_default == t_same

    def test_decay_layout_produces_valid_circuit(self, setup):
        dev, conf, qc = setup
        tqc = self._compile(setup, "decay")
        assert tqc.num_qubits == 5
        ev = EvalV2(conf)
        total = ev(tqc, backend=None)
        assert total > 0

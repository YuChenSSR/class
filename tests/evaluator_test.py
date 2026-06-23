import os
from math import isclose

from qiskit import QuantumCircuit, transpile
from qiskit.providers.fake_provider import Fake127QPulseV1

from dqcmap.controller import ControllerConfig
from dqcmap.evaluator import Eval, EvalV3
from dqcmap.utils import get_cif_qubit_pairs


class TestEval:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.measure(0, 0)
    qc.cx(0, 1).c_if(0, 1)
    cif_pairs = get_cif_qubit_pairs(qc)

    dev = Fake127QPulseV1()
    tqc = transpile(qc, dev)

    # Here we use the default trivial mapping because the results are reproducible
    conf = ControllerConfig(127, 10)

    def test_get_phy_cond_pairs_true(self):
        e = Eval(TestEval.conf, TestEval.cif_pairs)
        pairs = e.get_phy_cond_pairs(TestEval.tqc, TestEval.dev)

        assert pairs == [[0, 0], [1, 0]]

    def test_get_phy_cond_pairs_false(self):
        e = Eval(TestEval.conf)
        pairs = e.get_phy_cond_pairs(TestEval.tqc, TestEval.dev)

        assert pairs is None

    def test_calc_latency(self):
        e = Eval(TestEval.conf, TestEval.cif_pairs)
        print(TestEval.conf.pq_to_ctrl)
        pairs = [[1, 0], [3, 15]]

        t = e.calc_ctrl_latency(pairs)

        assert isclose(t, 5.5e-7)

    def test_get_init_layout_ctrl_latency(self):
        e = Eval(TestEval.conf, TestEval.cif_pairs)

        init_layout = [0, 21]

        t = e.get_init_layout_ctrl_latency(TestEval.qc, init_layout)

        assert isclose(t, 5.5e-7)

    def test_eval_v3_ctrl_latency(self):
        e = EvalV3(TestEval.conf)
        qft_path = "benchmarks/veriq-benchmark/dynamic/qft/dqc_qft_4.qasm"
        assert os.path.exists(qft_path)

        qc = QuantumCircuit.from_qasm_file(qft_path)
        pairs = get_cif_qubit_pairs(qc, with_states=True)

        latency = e.calc_ctrl_latency(pairs)

        assert isclose(latency, 5e-8 * 3)

    def test_eval_v3_get_init_layout_ctrl_latency(self):
        """EvalV3 must compute the init-layout ctrl latency using the
        broadcast-aware (deduped) semantics, not the placeholder 0."""
        e = EvalV3(TestEval.conf)

        # TestEval.qc has a single cif pair (q1 conditioned on the measurement
        # of q0). Mapping the two logical qubits to *different* controllers
        # yields a single inter-controller communication (dt_inter = 5e-7).
        inter_layout = [0, 21]
        assert isclose(e.get_init_layout_ctrl_latency(TestEval.qc, inter_layout), 5e-7)

        # Mapping both qubits to the *same* controller yields one inner
        # communication (dt_inner = 5e-8).
        intra_layout = [0, 1]
        assert isclose(e.get_init_layout_ctrl_latency(TestEval.qc, intra_layout), 5e-8)

        # An identity layout must agree with calc_ctrl_latency on the same
        # (logical) stateful pairs.
        identity_layout = list(range(TestEval.qc.num_qubits))
        pairs = get_cif_qubit_pairs(TestEval.qc, with_states=True)
        assert isclose(
            e.get_init_layout_ctrl_latency(TestEval.qc, identity_layout),
            e.calc_ctrl_latency(pairs),
        )

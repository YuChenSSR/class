"""End-to-end smoke test for the multi-controller compile pipeline.

This deliberately exercises the full stack -- importing the Rust
``dqcmap._accelerate`` extension, building a controller configuration,
pruning the coupling map and running the Qiskit transpiler through the
``MultiCtrlCompiler``. It is intentionally small (opt level 1) so it stays
fast while still catching build / wiring regressions in CI.
"""

from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import Fake27QPulseV1

from dqcmap.compilers.multi_ctrl_compiler import MultiCtrlCompiler
from dqcmap.controller import ControllerConfig, MapStratety


def _build_dqc(num_qubits: int = 4) -> QuantumCircuit:
    """A tiny dynamic circuit with a measure -> conditional dependency."""
    qc = QuantumCircuit(num_qubits, num_qubits)
    qc.h(0)
    qc.measure(0, 0)
    qc.x(1).c_if(0, 1)
    qc.cx(1, 2)
    qc.measure(2, 2)
    qc.x(3).c_if(2, 1)
    return qc


def test_multi_ctrl_compile_smoke():
    dev = Fake27QPulseV1()
    cm = dev.configuration().coupling_map
    conf = ControllerConfig(
        dev.configuration().n_qubits,
        num_controllers=4,
        strategy=MapStratety.CONNECT,
        cm=cm,
    )

    compiler = MultiCtrlCompiler(conf)
    qc = _build_dqc()

    tqc = compiler.run(qc, backend=dev, opt_level=1, seed_transpiler=1900)

    assert isinstance(tqc, QuantumCircuit)
    # The transpiled circuit must fit on the device.
    assert tqc.num_qubits == dev.configuration().n_qubits
    # The conditional logic should be preserved through compilation.
    assert tqc.count_ops().get("measure", 0) >= 1


def _build_star_dqc() -> QuantumCircuit:
    """A dynamic circuit whose interaction graph is *not* embeddable in the
    degree-3 heavy-hex topology (qubit 0 couples to four neighbours), forcing
    the DqcMapLayout pass to actually run rather than being short-circuited by
    a trivial VF2 layout."""
    qc = QuantumCircuit(8, 8)
    qc.h(0)
    for t in (1, 2, 3, 4):
        qc.cx(0, t)
    qc.measure(0, 0)
    qc.x(5).c_if(0, 1)
    qc.cx(5, 6)
    qc.measure(6, 6)
    qc.x(7).c_if(6, 1)
    return qc


def test_multi_ctrl_opt1_layout_no_panic():
    """Regression test for the SABRE layout panic.

    At ``opt_level`` 1 the DqcMapLayout pass is configured with
    ``layout_trials=0`` and no ``sabre_starting_layouts``; previously this left
    the Rust ``sabre_layout_and_routing`` trial iterator empty and panicked on
    ``min_by_key(...).unwrap()``. The compile must now complete.
    """
    dev = Fake27QPulseV1()
    cm = dev.configuration().coupling_map
    conf = ControllerConfig(
        dev.configuration().n_qubits,
        num_controllers=4,
        strategy=MapStratety.CONNECT,
        cm=cm,
    )

    compiler = MultiCtrlCompiler(conf)
    qc = _build_star_dqc()

    tqc = compiler.run(
        qc,
        backend=dev,
        opt_level=1,
        routing_method="dqcswap",
        seed_transpiler=1900,
    )

    assert isinstance(tqc, QuantumCircuit)
    assert tqc.num_qubits == dev.configuration().n_qubits

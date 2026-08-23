# tests/test_stress.py
"""
Automated Stress Testing Suite for Quantum Virtual Machine (QVM).

This suite stresses front-end ingestion (OpenQASM 3.0 parser), compilation/transpilation
(Decomposer, SABRE/Greedy routing), and execution backends (Dense Statevector Simulator,
Matrix Product State Simulator) on large-scale circuits with 1000+ operations.

It collects performance metrics (wall-clock time, gate throughput, peak memory,
allocation delta) and verifies graceful failure/bottleneck handling across scale boundaries.
"""

import contextlib
from dataclasses import dataclass, field
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytest

from qvm.architecture import TargetArchitecture, get_linear_architecture
from qvm.decomposer import Decomposer
from qvm.ir import QuantumCircuit
from qvm.mps_simulator import MPSSimulator
from qvm.parameter import Parameter
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator
from qvm.transpiler import Transpiler


# =====================================================================
# 1. Performance Telemetry & Profiling Infrastructure
# =====================================================================

@dataclass
class PerformanceMetrics:
    """Performance telemetry record for benchmarked workloads."""
    name: str
    num_qubits: int
    num_operations: int
    wall_clock_time_sec: float
    gate_throughput_ops_per_sec: float
    peak_memory_mb: float
    memory_delta_mb: float
    extra_info: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"PerformanceMetrics({self.name!r}: qubits={self.num_qubits}, "
            f"ops={self.num_operations}, time={self.wall_clock_time_sec * 1000:.2f}ms, "
            f"throughput={self.gate_throughput_ops_per_sec:.0f} ops/s, "
            f"peak_mem={self.peak_memory_mb:.2f}MB, delta_mem={self.memory_delta_mb:.2f}MB)"
        )


@contextlib.contextmanager
def measure_performance(name: str, num_operations: int, num_qubits: int):
    """
    Context manager to accurately measure execution wall-clock time,
    throughput (ops/sec), peak memory, and allocation delta using
    time.perf_counter() and tracemalloc.
    """
    tracemalloc.start()
    tracemalloc.reset_peak()
    start_mem, _ = tracemalloc.get_traced_memory()
    start_time = time.perf_counter()
    metrics_holder: Dict[str, Any] = {}
    try:
        yield metrics_holder
    finally:
        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        wall_time = max(end_time - start_time, 1e-9)
        throughput = num_operations / wall_time
        peak_mb = peak_mem / (1024 * 1024)
        delta_mb = max(0.0, (current_mem - start_mem) / (1024 * 1024))

        extra = metrics_holder.get("extra", {})
        metrics = PerformanceMetrics(
            name=name,
            num_qubits=num_qubits,
            num_operations=num_operations,
            wall_clock_time_sec=wall_time,
            gate_throughput_ops_per_sec=throughput,
            peak_memory_mb=peak_mb,
            memory_delta_mb=delta_mb,
            extra_info=extra,
        )
        metrics_holder["metrics"] = metrics


# =====================================================================
# 2. Four Programmatic Circuit Generation Utilities (1000+ Operations)
# =====================================================================

def generate_deep_rotation_circuit(num_qubits: int = 4, num_gates: int = 1000) -> QuantumCircuit:
    """
    1. Deep 1D Rotation Chain: Generates 1000+ single-qubit rotation gates
       chaining Rx, Ry, Rz, H, and T across target qubits.

    Args:
        num_qubits: Number of qubits in the circuit.
        num_gates: Total number of single-qubit rotation gates to emit.

    Returns:
        QuantumCircuit containing exactly `num_gates` operations.
    """
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")
    if num_gates <= 0:
        raise ValueError("num_gates must be positive")

    qc = QuantumCircuit(num_qubits)
    gate_types = ["rx", "ry", "rz", "h", "t"]

    for i in range(num_gates):
        gate_name = gate_types[i % len(gate_types)]
        target_q = i % num_qubits
        if gate_name in ["rx", "ry", "rz"]:
            angle = ((i + 1) * np.pi) / 16.0
            qc.add_operation(gate_name, [target_q], [angle])
        else:
            qc.add_operation(gate_name, [target_q], [])

    return qc


def generate_qft_circuit(num_qubits: int = 25) -> QuantumCircuit:
    """
    2. Scaled Quantum Fourier Transform: Generates an N-qubit QFT circuit
       with Hadamard gates and controlled-phase rotations decomposed into
       native operations (RZ and CX), plus terminal SWAPs.

    For N=25, generates 1537 operations (1000+ operations).

    Args:
        num_qubits: Number of qubits in the QFT circuit.

    Returns:
        QuantumCircuit containing the full QFT network.
    """
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")

    qc = QuantumCircuit(num_qubits)
    for i in range(num_qubits):
        qc.add_operation("h", [i], [])
        for j in range(i + 1, num_qubits):
            theta = np.pi / (2 ** (j - i))
            # Controlled-phase rotation CP(theta) decomposed into native RZ + CX gates:
            qc.add_operation("rz", [j], [theta / 2.0])
            qc.add_operation("rz", [i], [theta / 2.0])
            qc.add_operation("cx", [j, i], [])
            qc.add_operation("rz", [i], [-theta / 2.0])
            qc.add_operation("cx", [j, i], [])

    # Final bit-reversal SWAP network
    for i in range(num_qubits // 2):
        qc.add_operation("swap", [i, num_qubits - 1 - i], [])

    return qc


def generate_hea_ansatz_circuit(
    num_qubits: int = 6,
    layers: int = 60,
    entangler: str = "cx",
    parameterized: bool = True
) -> QuantumCircuit:
    """
    3. Variational Hardware-Efficient Ansatz (HEA): Generates 1000+ alternating
       parameterized single-qubit rotation layers (Ry, Rz) and entangling CNOT/CZ ladders.

    For N=6, L=60, generates 1026 operations (1000+ operations).

    Args:
        num_qubits: Number of qubits in the register.
        layers: Number of variational ansatz layers.
        entangler: Entangling gate type ("cx" or "cz").
        parameterized: If True, uses symbolic Parameter instances; if False, uses concrete floats.

    Returns:
        QuantumCircuit containing the HEA circuit.
    """
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")
    if layers <= 0:
        raise ValueError("layers must be positive")
    if entangler not in ["cx", "cz"]:
        raise ValueError(f"Unsupported entangler: {entangler}")

    qc = QuantumCircuit(num_qubits)

    for l in range(layers):
        # Parameterized rotation layer: Ry(theta) and Rz(phi) on each qubit
        for q in range(num_qubits):
            if parameterized:
                p_y = Parameter(f"theta_{l}_{q}_y")
                p_z = Parameter(f"phi_{l}_{q}_z")
                qc.add_operation("ry", [q], [p_y])
                qc.add_operation("rz", [q], [p_z])
            else:
                qc.add_operation("ry", [q], [0.1 * (l + 1) + 0.05 * q])
                qc.add_operation("rz", [q], [0.2 * (l + 1) + 0.03 * q])

        # Entangling ladder: nearest-neighbor entangling gates along the 1D chain
        for q in range(num_qubits - 1):
            qc.add_operation(entangler, [q, q + 1], [])

    # Final rotation layer
    for q in range(num_qubits):
        if parameterized:
            p_final = Parameter(f"theta_final_{q}")
            qc.add_operation("ry", [q], [p_final])
        else:
            qc.add_operation("ry", [q], [0.05 * (q + 1)])

    return qc


def generate_qasm3_loop_stream(iterations: int = 200, num_qubits: int = 4) -> str:
    """
    4. OpenQASM 3.0 Programmatic Text Stream: Generates an OpenQASM 3.0 string
       stream with declarations and loop unrolling constructs testing parser throughput.

    For iterations=200 on 4 qubits, unrolls into 1200+ operations.

    Args:
        iterations: Loop upper bound for the for-loop.
        num_qubits: Number of qubits in the declared register.

    Returns:
        Valid OpenQASM 3.0 program string.
    """
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if num_qubits < 2:
        raise ValueError("num_qubits must be at least 2")

    lines = [
        "OPENQASM 3.0;",
        f"qubit[{num_qubits}] q;",
        f"bit[{num_qubits}] c;",
        f"for i in [0:{iterations}] {{",
        "    rx(0.785398) q[0];",
        "    ry(0.392699) q[1];",
        "    rz(1.570796) q[0];",
        "    h q[1];",
        "    cx q[0], q[1];",
        "    t q[0];",
    ]
    if num_qubits >= 3:
        lines.append("    cx q[1], q[2];")
    if num_qubits >= 4:
        lines.append("    cx q[2], q[3];")
    lines.extend([
        "}",
        "c[0] = measure q[0];",
    ])
    return "\n".join(lines)


# =====================================================================
# 3. Test Suite: Circuit Generation Verification
# =====================================================================

class TestCircuitGenerators:
    """Verify that all 4 programmatic generator utilities correctly emit 1000+ operation workloads."""

    def test_deep_rotation_generator_1000_ops(self):
        num_gates = 1200
        qc = generate_deep_rotation_circuit(num_qubits=4, num_gates=num_gates)
        assert isinstance(qc, QuantumCircuit)
        assert qc.num_qubits == 4
        assert len(qc.operations) == num_gates
        # All operations must be single-qubit gates
        for op in qc.operations:
            assert op["name"] in ["rx", "ry", "rz", "h", "t"]
            assert len(op["qubits"]) == 1
            assert 0 <= op["qubits"][0] < 4

    def test_qft_circuit_generator_scaling(self):
        num_qubits = 25
        qc = generate_qft_circuit(num_qubits=num_qubits)
        assert isinstance(qc, QuantumCircuit)
        assert qc.num_qubits == num_qubits
        assert len(qc.operations) >= 1000
        # Check presence of Hadamards, RZs, CXs, and SWAPs
        gate_names = {op["name"] for op in qc.operations}
        assert {"h", "rz", "cx", "swap"}.issubset(gate_names)

    def test_hea_ansatz_generator_scaling_and_parameters(self):
        num_qubits = 6
        layers = 60
        qc = generate_hea_ansatz_circuit(num_qubits=num_qubits, layers=layers, parameterized=True)
        assert isinstance(qc, QuantumCircuit)
        assert qc.num_qubits == num_qubits
        assert len(qc.operations) >= 1000
        # Check parameter extraction
        params = qc.parameters
        assert len(params) > 0
        # Bind parameters to concrete values and ensure all parameters are resolved
        bindings = {p: 0.123 for p in params}
        bound_qc = qc.bind_parameters(bindings)
        assert len(bound_qc.parameters) == 0
        assert len(bound_qc.operations) == len(qc.operations)

    def test_qasm3_loop_stream_generator_syntax(self):
        stream = generate_qasm3_loop_stream(iterations=200, num_qubits=4)
        assert isinstance(stream, str)
        assert "OPENQASM 3.0;" in stream
        assert "qubit[4] q;" in stream
        assert "for i in [0:200]" in stream


# =====================================================================
# 4. Test Suite: Dense Statevector Simulator Stress & Bottleneck Handling
# =====================================================================

class TestSimulatorStress:
    """Stress tests and bottleneck verification for the Dense Statevector Simulator."""

    @pytest.mark.parametrize("num_qubits, num_gates", [
        (2, 1000),
        (4, 1500),
        (6, 2000),
    ])
    def test_simulator_stress_deep_rotations(self, num_qubits, num_gates):
        qc = generate_deep_rotation_circuit(num_qubits=num_qubits, num_gates=num_gates)
        sim = Simulator()

        with measure_performance("Simulator_Deep_Rotations", num_gates, num_qubits) as perf:
            state, classical_mem = sim.simulate(qc, max_ops=100000)
            norm = np.linalg.norm(state)
            perf["extra"] = {"state_norm": float(norm)}

        metrics: PerformanceMetrics = perf["metrics"]
        assert np.isclose(metrics.extra_info["state_norm"], 1.0, atol=1e-6), "State vector must remain normalized"
        assert metrics.wall_clock_time_sec > 0
        assert metrics.gate_throughput_ops_per_sec > 1000, f"Expected >1000 ops/sec, got {metrics.gate_throughput_ops_per_sec}"

    def test_simulator_stress_hea_ansatz(self):
        num_qubits = 5
        layers = 50
        qc = generate_hea_ansatz_circuit(num_qubits=num_qubits, layers=layers, parameterized=False)
        assert len(qc.operations) >= 700

        sim = Simulator()
        with measure_performance("Simulator_HEA_Ansatz", len(qc.operations), num_qubits) as perf:
            state, _ = sim.simulate(qc, max_ops=50000)
            norm = np.linalg.norm(state)
            perf["extra"] = {"state_norm": float(norm)}

        metrics: PerformanceMetrics = perf["metrics"]
        assert np.isclose(metrics.extra_info["state_norm"], 1.0, atol=1e-6)
        assert metrics.gate_throughput_ops_per_sec > 1000

    def test_simulator_identity_cancellation_stress(self):
        """1000 alternating Pauli-X gates (X * X = I) must preserve |0...0> state with probability 1.0."""
        num_qubits = 3
        num_gates = 1000
        qc = QuantumCircuit(num_qubits)
        for _ in range(num_gates):
            qc.add_operation("x", [0], [])

        sim = Simulator()
        state, _ = sim.simulate(qc, max_ops=50000)
        prob_zero = float(np.abs(state[0]) ** 2)
        assert np.isclose(prob_zero, 1.0, atol=1e-6), f"Expected prob(|000>) = 1.0, got {prob_zero}"

    def test_simulator_max_ops_limit_bottleneck_graceful_handling(self):
        """Cleanly assert that exceeding max_ops raises RuntimeError without crashing."""
        qc = generate_deep_rotation_circuit(num_qubits=2, num_gates=1500)
        sim = Simulator()

        with pytest.raises(RuntimeError) as exc_info:
            sim.simulate(qc, max_ops=1000)

        assert "Exceeded maximum operations limit" in str(exc_info.value)

    def test_simulator_measurement_sampling_stress(self):
        qc = QuantumCircuit(3)
        qc.add_classical_register("c", 1)
        qc.add_operation("h", [0], [])
        qc.add_operation("cx", [0, 1], [])
        qc.add_operation("cx", [1, 2], [])
        # Add 1000 identity/rotation operations before measurement
        for i in range(1000):
            qc.add_operation("id", [i % 3], [])
        qc.add_operation("measure", [0], target_bit=("c", 0))

        sim = Simulator()
        state, mem = sim.simulate(qc, max_ops=50000)
        assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-6)
        assert "c" in mem
        assert mem["c"][0] in [0, 1]


# =====================================================================
# 5. Test Suite: Matrix Product State (MPS) Simulator Stress
# =====================================================================

class TestMPSSimulatorStress:
    """Stress tests and scaling verification for the Matrix Product State (MPS) Simulator."""

    @pytest.mark.parametrize("num_qubits", [10, 20, 30])
    def test_mps_simulator_stress_deep_rotations(self, num_qubits):
        num_gates = 1200
        qc = generate_deep_rotation_circuit(num_qubits=num_qubits, num_gates=num_gates)
        mps = MPSSimulator(max_bond_dim=16)

        with measure_performance(f"MPS_Deep_Rotations_{num_qubits}Q", num_gates, num_qubits) as perf:
            tensors, classical_mem = mps.simulate(qc)
            perf["extra"] = {"num_tensors": len(tensors)}

        metrics: PerformanceMetrics = perf["metrics"]
        assert len(tensors) == num_qubits
        # Verify rank-3 tensor shapes: (L, physical=2, R)
        for t in tensors:
            assert t.ndim == 3
            assert t.shape[1] == 2
            assert t.shape[0] <= 16
            assert t.shape[2] <= 16
        assert metrics.gate_throughput_ops_per_sec > 5000

    def test_mps_simulator_hea_ansatz_scalability(self):
        num_qubits = 15
        layers = 30
        qc = generate_hea_ansatz_circuit(num_qubits=num_qubits, layers=layers, parameterized=False)
        assert len(qc.operations) >= 800

        mps = MPSSimulator(max_bond_dim=16)
        with measure_performance("MPS_HEA_Ansatz_15Q", len(qc.operations), num_qubits) as perf:
            tensors, _ = mps.simulate(qc)

        assert len(tensors) == num_qubits
        metrics: PerformanceMetrics = perf["metrics"]
        assert metrics.wall_clock_time_sec < 2.0, "MPS 1000-op HEA simulation should execute within 2 seconds"

    def test_mps_simulator_non_nearest_neighbor_bottleneck_handling(self):
        """Verify that MPSSimulator cleanly rejects non-nearest-neighbor two-qubit gates."""
        qc = QuantumCircuit(5)
        qc.add_operation("h", [0], [])
        qc.add_operation("cx", [0, 4], [])  # Non-adjacent: |0 - 4| = 4 != 1

        mps = MPSSimulator()
        with pytest.raises(ValueError) as exc_info:
            mps.simulate(qc)

        assert "nearest-neighbor" in str(exc_info.value).lower()

    def test_mps_vs_statevector_small_baseline_consistency(self):
        """Verify that MPS and Statevector produce identical measurement statistics on small circuits."""
        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.add_operation("h", [0], [])
        qc.add_operation("cx", [0, 1], [])
        qc.add_operation("cx", [1, 2], [])
        for i in range(100):
            qc.add_operation("rz", [i % num_qubits], [0.1])

        sim = Simulator()
        state, _ = sim.simulate(qc, max_ops=50000)
        probs_statevector = np.abs(state) ** 2

        mps = MPSSimulator(max_bond_dim=16)
        tensors, _ = mps.simulate(qc)
        sv_mps = mps.get_statevector()
        probs_mps = np.abs(sv_mps) ** 2

        assert np.allclose(probs_statevector, probs_mps, atol=1e-5)


# =====================================================================
# 6. Test Suite: Transpiler & Routing Stress
# =====================================================================

class TestTranspilerStress:
    """Stress tests for circuit routing and architectural transpilation passes."""

    @pytest.mark.parametrize("strategy, restore_mapping", [
        ("greedy", True),
        ("sabre", False),
    ])
    def test_transpiler_stress_routing_1000_ops(self, strategy, restore_mapping):
        num_qubits = 5
        arch = get_linear_architecture(num_qubits)

        # Create a 1000+ gate circuit containing non-adjacent two-qubit interactions
        qc = QuantumCircuit(num_qubits)
        for i in range(250):
            qc.add_operation("h", [i % num_qubits], [])
            qc.add_operation("cx", [i % num_qubits, (i + 2) % num_qubits], [])
            qc.add_operation("rz", [(i + 2) % num_qubits], [0.5])
            qc.add_operation("cx", [(i + 1) % num_qubits, (i + 4) % num_qubits], [])

        assert len(qc.operations) == 1000

        transpiler = Transpiler(arch, strategy=strategy, restore_mapping=restore_mapping)
        with measure_performance(f"Transpiler_{strategy}_1000_Ops", len(qc.operations), num_qubits) as perf:
            physical_qc = transpiler.transpile(qc)
            perf["extra"] = {"physical_ops": len(physical_qc.operations)}

        metrics: PerformanceMetrics = perf["metrics"]
        assert len(physical_qc.operations) >= 1000

        # Verify that EVERY 2-qubit gate in the transpiled circuit satisfies physical connectivity
        for op in physical_qc.operations:
            if len(op["qubits"]) == 2:
                q1, q2 = op["qubits"]
                assert arch.is_connected(q1, q2), f"Routed gate {op['name']} on qubits [{q1}, {q2}] is not connected on architecture"

        assert metrics.gate_throughput_ops_per_sec > 1000

    def test_transpiler_qft_routing_stress(self):
        """Transpiles a scaled QFT circuit (1000+ ops) onto a linear architecture."""
        num_qubits = 20
        qft = generate_qft_circuit(num_qubits=num_qubits)
        assert len(qft.operations) >= 900

        arch = get_linear_architecture(num_qubits)
        transpiler = Transpiler(arch, strategy="greedy", restore_mapping=True)

        with measure_performance("Transpiler_QFT_Routing", len(qft.operations), num_qubits) as perf:
            physical_qc = transpiler.transpile(qft)
            perf["extra"] = {"physical_ops": len(physical_qc.operations)}

        for op in physical_qc.operations:
            if len(op["qubits"]) == 2:
                q1, q2 = op["qubits"]
                assert arch.is_connected(q1, q2)

    def test_transpiler_capacity_bottleneck_handling(self):
        """Verify that transpiling to an architecture with insufficient qubits cleanly raises ValueError."""
        qc = QuantumCircuit(8)
        arch = get_linear_architecture(5)  # 5 physical qubits < 8 logical qubits

        transpiler = Transpiler(arch)
        with pytest.raises(ValueError) as exc_info:
            transpiler.transpile(qc)

        assert "more qubits than the target architecture" in str(exc_info.value)


# =====================================================================
# 7. Test Suite: OpenQASM 3.0 Parser Stress & Throughput
# =====================================================================

class TestOpenQASM3ParserStress:
    """Stress tests and throughput evaluation for OpenQASM 3.0 parsing."""

    def test_qasm3_parser_stress_unrolling_1000_ops(self):
        stream = generate_qasm3_loop_stream(iterations=200, num_qubits=4)
        parser = OpenQASM3Parser()

        with measure_performance("OpenQASM3Parser_Unrolling", 1200, 4) as perf:
            qc = parser.parse(stream)
            perf["extra"] = {"parsed_ops": len(qc.operations)}

        metrics: PerformanceMetrics = perf["metrics"]
        assert isinstance(qc, QuantumCircuit)
        assert qc.num_qubits == 4
        assert len(qc.operations) >= 1200
        assert metrics.gate_throughput_ops_per_sec > 1000

    def test_qasm3_parser_direct_stream_1000_lines(self):
        """Parse a 1000+ line flat OpenQASM 3.0 file without loops."""
        lines = ["OPENQASM 3.0;", "qubit[4] q;", "bit[4] c;"]
        for i in range(1000):
            target = i % 4
            next_target = (i + 1) % 4
            lines.append(f"rx(0.5) q[{target}];")
            lines.append(f"cx q[{target}], q[{next_target}];")
        lines.append("c[0] = measure q[0];")
        qasm_text = "\n".join(lines)

        parser = OpenQASM3Parser()
        with measure_performance("OpenQASM3Parser_Direct_1000_Lines", 2000, 4) as perf:
            qc = parser.parse(qasm_text)
            perf["extra"] = {"parsed_ops": len(qc.operations)}

        assert len(qc.operations) == 2001

    def test_qasm3_parser_syntax_error_graceful_handling(self):
        """Verify that malformed OpenQASM 3.0 syntax is caught cleanly without interpreter crash."""
        bad_qasm = "OPENQASM 3.0;\nqubit[4] q;\nINVALID_TOKEN_HERE ???\n"
        parser = OpenQASM3Parser()

        with pytest.raises(Exception):  # Lark UnexpectedToken / ParseError
            parser.parse(bad_qasm)


# =====================================================================
# 8. Test Suite: Decomposer Stress
# =====================================================================

class TestDecomposerStress:
    """Stress tests for multi-gate decomposition passes."""

    def test_decomposer_stress_multi_toffoli_1500_ops(self):
        """100 Toffoli gates decompose into 1500 native gates (15 gates/Toffoli)."""
        qc = QuantumCircuit(3)
        for _ in range(100):
            qc.add_operation("ccx", [0, 1, 2], [])

        assert len(qc.operations) == 100
        decomposer = Decomposer(native_gates={"h", "cx", "rz"})

        with measure_performance("Decomposer_100_Toffoli", 100, 3) as perf:
            decomposed_qc = decomposer.decompose_circuit(qc)
            perf["extra"] = {"decomposed_ops": len(decomposed_qc.operations)}

        assert len(decomposed_qc.operations) == 1500
        for op in decomposed_qc.operations:
            assert op["name"] in ["h", "cx", "rz"]

        # Simulate the decomposed 1500-op circuit
        sim = Simulator()
        state, _ = sim.simulate(decomposed_qc, max_ops=50000)
        assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-6)


# =====================================================================
# 9. Test Suite: End-to-End Pipeline Stress
# =====================================================================

class TestEndToEndPipelineStress:
    """End-to-end integration stress tests exercising the complete compilation and execution pipeline."""

    def test_e2e_stress_pipeline_1000_ops(self):
        """
        Complete E2E workflow:
        1. Ingest 1000+ op OpenQASM 3.0 stream.
        2. Transpile onto a constrained 5-qubit linear architecture.
        3. Simulate using the Dense Statevector Simulator.
        4. Profile total execution telemetry.
        """
        stream = generate_qasm3_loop_stream(iterations=200, num_qubits=4)
        arch = get_linear_architecture(5)

        # Stage 1: Parse
        with measure_performance("E2E_Stage1_Parse", 1200, 4) as perf_parse:
            parser = OpenQASM3Parser()
            logical_qc = parser.parse(stream)
        assert len(logical_qc.operations) >= 1200

        # Stage 2: Transpile
        with measure_performance("E2E_Stage2_Transpile", len(logical_qc.operations), 5) as perf_transpile:
            transpiler = Transpiler(arch, strategy="greedy")
            physical_qc = transpiler.transpile(logical_qc)
        assert len(physical_qc.operations) >= len(logical_qc.operations)

        # Stage 3: Simulate
        with measure_performance("E2E_Stage3_Simulate", len(physical_qc.operations), 5) as perf_sim:
            sim = Simulator()
            state, classical_mem = sim.simulate(physical_qc, max_ops=100000)
            norm = np.linalg.norm(state)
            perf_sim["extra"] = {"state_norm": float(norm)}

        assert np.isclose(perf_sim["extra"]["state_norm"], 1.0, atol=1e-6)

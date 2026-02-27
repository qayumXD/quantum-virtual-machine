"""
Detailed parser module for Qiskit and Cirq circuits.

This is a lightweight, self-contained parser used by the legacy examples
(`src/examples_bell_state_parser_demo.py`). It converts framework-specific
circuits into the `QuantumCircuitIR` defined in `src/ir.py`. The main QVM
pipeline continues to live under `src/qvm/`.
"""

from typing import Any

try:
    from qiskit import QuantumCircuit  # type: ignore
    QISKIT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in tests via skip
    QuantumCircuit = None
    QISKIT_AVAILABLE = False

from src.ir import QuantumCircuitIR, QuantumGate


class QiskitParser:
    """Parser for Qiskit `QuantumCircuit` objects."""

    def __init__(self):
        self.supported_gates = {
            "h",
            "x",
            "y",
            "z",
            "cx",
            "cnot",
            "cz",
            "rx",
            "ry",
            "rz",
            "measure",
        }

    def parse(self, circuit: Any) -> QuantumCircuitIR:
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is not installed. Install with: pip install qiskit")
        if not isinstance(circuit, QuantumCircuit):
            raise TypeError("Expected a qiskit.QuantumCircuit instance")

        ir = QuantumCircuitIR(num_qubits=circuit.num_qubits)

        for instruction, qubits, clbits in circuit.data:
            gate_name = instruction.name.lower()

            if gate_name == "measure":
                q_idx = circuit.qubits.index(qubits[0])
                c_idx = circuit.clbits.index(clbits[0])
                ir.add_measurement(q_idx, c_idx)
                continue

            if gate_name not in self.supported_gates:
                raise ValueError(f"Unsupported gate: {gate_name}")

            qubit_indices = [circuit.qubits.index(q) for q in qubits]
            params = list(instruction.params) if instruction.params else []

            ir.add_gate(
                QuantumGate(
                    gate_type=self._normalize_gate_name(gate_name),
                    qubits=qubit_indices,
                    params=params,
                )
            )

        return ir

    def _normalize_gate_name(self, gate_name: str) -> str:
        mapping = {
            "h": "H",
            "x": "X",
            "y": "Y",
            "z": "Z",
            "cx": "CX",
            "cnot": "CX",
            "cz": "CZ",
            "rx": "RX",
            "ry": "RY",
            "rz": "RZ",
        }
        return mapping.get(gate_name, gate_name.upper())


class CirqParser:
    """
    Placeholder for a future Cirq parser. Kept for interface completeness;
    not implemented yet.
    """

    def parse(self, circuit: Any):  # pragma: no cover - not implemented
        raise NotImplementedError("CirqParser is not implemented yet")

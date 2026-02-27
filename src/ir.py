"""
Intermediate Representation (IR) for hardware-agnostic quantum circuits.

This module provides a lightweight dataclass-based IR that is used by the
top-level (non-qvm) examples, such as `src/examples_bell_state_parser_demo.py`.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class QuantumGate:
    """Represents a single quantum gate in the IR."""
    gate_type: str
    qubits: List[int]
    params: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.gate_type, "qubits": self.qubits, "params": self.params}


class QuantumCircuitIR:
    """
    Hardware-agnostic intermediate representation of a quantum circuit.

    This IR is intentionally simple: a list of gates plus optional measurements.
    It is separate from the `src/qvm/ir.py` (which is used by the main QVM
    pipeline) so that example scripts depending on this legacy IR continue to
    work without affecting the QVM internals.
    """

    def __init__(self, num_qubits: int):
        if not isinstance(num_qubits, int) or num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer.")
        self.num_qubits = num_qubits
        self.gates: List[QuantumGate] = []
        self.measurements: List[Dict[str, int]] = []

    def add_gate(self, gate: QuantumGate) -> None:
        self.gates.append(gate)

    def add_measurement(self, qubit: int, classical_bit: int) -> None:
        self.measurements.append({"qubit": qubit, "classical_bit": classical_bit})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_qubits": self.num_qubits,
            "gates": [g.to_dict() for g in self.gates],
            "measurements": self.measurements,
        }

    def __repr__(self) -> str:
        return f"QuantumCircuitIR(qubits={self.num_qubits}, gates={len(self.gates)}, measurements={len(self.measurements)})"

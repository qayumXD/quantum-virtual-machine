"""
Detailed parser module for Qiskit and Cirq circuits.

This is a lightweight, self-contained parser used by the legacy examples
(`src/examples_bell_state_parser_demo.py`). It converts framework-specific
circuits into the `QuantumCircuitIR` defined in `src/ir.py`. The main QVM
pipeline continues to live under `src/qvm/`.
"""

from typing import Any, Dict, List

import math

try:
    from qiskit import QuantumCircuit  # type: ignore
    QISKIT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in tests via skip
    QuantumCircuit = None
    QISKIT_AVAILABLE = False

try:
    import cirq  # type: ignore
    CIRQ_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in tests via skip
    cirq = None
    CIRQ_AVAILABLE = False

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
    Parser for Cirq Circuit objects.

    Supported gates:
      - H, X, Y, Z
      - CNOT / CX
      - CZ
      - SWAP
      - RX / RY / RZ (angles in radians)
      - Measurement (qubit -> classical bit mapping in encounter order)
    """

    def parse(self, circuit: Any) -> QuantumCircuitIR:
        if not CIRQ_AVAILABLE:
            raise ImportError("Cirq is not installed. Install with: pip install cirq")
        if not isinstance(circuit, cirq.Circuit):
            raise TypeError("Expected a cirq.Circuit instance")

        qubit_list = sorted(circuit.all_qubits())
        qubit_index: Dict[Any, int] = {q: i for i, q in enumerate(qubit_list)}
        ir = QuantumCircuitIR(num_qubits=len(qubit_list))
        meas_bit_counter = 0

        for op in circuit.all_operations():
            gate = op.gate
            targets = [qubit_index[q] for q in op.qubits]

            # Measurement
            if isinstance(gate, cirq.MeasurementGate):
                for q in targets:
                    ir.add_measurement(q, meas_bit_counter)
                    meas_bit_counter += 1
                continue

            name, params = self._map_gate(gate)
            if name is None:
                raise ValueError(f"Unsupported Cirq gate: {gate!r}")
            ir.add_gate(QuantumGate(gate_type=name, qubits=targets, params=params))

        return ir

    def _map_gate(self, gate) -> tuple[str | None, List[float]]:
        """
        Map Cirq gate object to IR gate name and parameters.
        Returns (name, params) or (None, []) if unsupported.
        """
        # Exact matches
        if gate == cirq.H:
            return "H", []
        if gate == cirq.X:
            return "X", []
        if gate == cirq.Y:
            return "Y", []
        if gate == cirq.Z:
            return "Z", []
        if gate == cirq.CNOT or gate == cirq.CX:
            return "CX", []
        if gate == cirq.CZ:
            return "CZ", []
        if gate == cirq.SWAP:
            return "SWAP", []

        # Rotation gates (PowGates)
        if isinstance(gate, cirq.ops.common_gates.XPowGate):
            angle = float(gate.exponent * math.pi)
            return "RX", [angle]
        if isinstance(gate, cirq.ops.common_gates.YPowGate):
            angle = float(gate.exponent * math.pi)
            return "RY", [angle]
        if isinstance(gate, cirq.ops.common_gates.ZPowGate):
            angle = float(gate.exponent * math.pi)
            return "RZ", [angle]

        # Controlled gates encoded via ControlledGate
        if isinstance(gate, cirq.ops.controlled_gate.ControlledGate):
            # Only support controlled X and Z with one control
            if gate.num_controls() == 1:
                sub = gate.sub_gate
                if sub == cirq.X:
                    return "CX", []
                if sub == cirq.Z:
                    return "CZ", []

        return None, []

"""
Cirq -> QVM IR demo.

Builds a simple Bell circuit in Cirq, parses it into the lightweight
QuantumCircuitIR (src/ir.py), and prints a JSON-compatible gate list that can
be fed to the QVM CLI.
"""

import json

try:
    import cirq
except ImportError:
    print("Cirq is not installed. Install with: pip install cirq")
    raise SystemExit(1)

from qvm.parser import CirqParser


def main():
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    print("Cirq circuit:")
    print(circuit)

    ir = CirqParser().parse(circuit)
    print("\nParsed IR:")
    print(ir.to_dict())

    # Convert IR to the JSON gate list accepted by the QVM CLI
    gate_list = [
        {"name": g.gate_type.lower(), "qubits": g.qubits, "params": g.params}
        for g in ir.gates
    ]
    print("\nGate list for QVM CLI (JSON):")
    print(json.dumps(gate_list, indent=2))
    print("\nRun with:")
    print("  python -m qvm.cli <json-file> --nqubits 2 --transpile")


if __name__ == "__main__":
    main()

# src/qvm/parser.py

"""
Parser for converting a simple circuit description into the Intermediate Representation (IR).
"""

from typing import List, Dict, Any
from src.qvm.ir import QuantumCircuit

class QASMParser:
    """
    A minimal parser that converts a list of gate descriptions into a QuantumCircuit IR.
    The input format is expected to be a list of dictionaries.
    Example:
    [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "rz", "qubits": [2], "params": [0.5]}
    ]
    """
    @staticmethod
    def parse(circuit_description: List[Dict[str, Any]], num_qubits: int) -> QuantumCircuit:
        """
        Parses a circuit description and returns a QuantumCircuit object.

        Args:
            circuit_description (List[Dict[str, Any]]): A list of dictionaries,
                                                        each describing a gate operation.
            num_qubits (int): The total number of qubits in the circuit.

        Returns:
            QuantumCircuit: The IR representation of the circuit.
        """
        qc = QuantumCircuit(num_qubits)
        for op_data in circuit_description:
            gate_name = op_data.get("name")
            qubits = op_data.get("qubits")
            params = op_data.get("params")

            if not all([gate_name, qubits]):
                raise ValueError(f"Each operation must have 'name' and 'qubits'. Missing in: {op_data}")

            qc.add_operation(gate_name, qubits, params)
        return qc


class OpenQASM2Parser:
    """
    Minimal OpenQASM 2.0 parser for a common subset (h, x, y, z, rx, ry, rz, cx, swap, measure).
    """

    SUPPORTED_GATES = {"h", "x", "y", "z", "rx", "ry", "rz", "cx", "swap", "id"}

    @staticmethod
    def parse_file(path: str) -> QuantumCircuit:
        with open(path, "r") as f:
            text = f.read()
        return OpenQASM2Parser.parse(text)

    @staticmethod
    def parse(text: str) -> QuantumCircuit:
        lines = []
        for raw in text.splitlines():
            stripped = raw.split("//")[0].strip()
            if stripped:
                lines.append(stripped.rstrip(";"))

        if not lines or not lines[0].lower().startswith("openqasm"):
            raise ValueError("Missing OPENQASM header")

        num_qubits = None
        qc = None

        for line in lines:
            if line.lower().startswith("openqasm") or line.lower().startswith("include"):
                continue
            if line.lower().startswith("qreg"):
                num_qubits = OpenQASM2Parser._parse_register_size(line)
                qc = QuantumCircuit(num_qubits)
                continue
            if qc is None:
                raise ValueError("qreg must be declared before gates")

            if line.lower().startswith("creg"):
                # creg ignored for now
                continue
            if line.lower().startswith("measure"):
                q, c = OpenQASM2Parser._parse_measure(line)
                qc.add_operation("measure", [q], [])
                continue
            gate_name, qubits, params = OpenQASM2Parser._parse_gate(line)
            if gate_name not in OpenQASM2Parser.SUPPORTED_GATES:
                raise ValueError(f"Unsupported gate: {gate_name}")
            qc.add_operation(gate_name, qubits, params)

        if qc is None:
            raise ValueError("No qreg found in QASM")
        return qc

    @staticmethod
    def _parse_register_size(line: str) -> int:
        # qreg q[3];
        start = line.find("[")
        end = line.find("]")
        if start == -1 or end == -1:
            raise ValueError("Invalid qreg line")
        size = int(line[start + 1 : end])
        if size <= 0:
            raise ValueError("qreg size must be positive")
        return size

    @staticmethod
    def _parse_measure(line: str) -> tuple[int, int]:
        # measure q[0] -> c[0];
        parts = line.replace("measure", "").replace(" ", "").split("->")
        if len(parts) != 2:
            raise ValueError("Invalid measure syntax")
        q = OpenQASM2Parser._parse_qubit(parts[0])
        c = OpenQASM2Parser._parse_qubit(parts[1])
        return q, c

    @staticmethod
    def _parse_gate(line: str) -> tuple[str, List[int], List[float]]:
        # gate with optional params: rz(1.57) q[0];
        name_part, rest = line.split(None, 1)
        name_part = name_part.strip()
        params = []
        if "(" in name_part:
            name, param_str = name_part.split("(", 1)
            param_val = float(param_str.rstrip(")"))
            params = [param_val]
            gate_name = name.lower()
        else:
            gate_name = name_part.lower()

        qubit_tokens = rest.replace(" ", "").split(",")
        qubits = [OpenQASM2Parser._parse_qubit(tok) for tok in qubit_tokens]
        return gate_name, qubits, params

    @staticmethod
    def _parse_qubit(token: str) -> int:
        # q[0]
        start = token.find("[")
        end = token.find("]")
        if start == -1 or end == -1:
            raise ValueError(f"Invalid qubit token: {token}")
        return int(token[start + 1 : end])

# Example Usage (for testing during development)
if __name__ == "__main__":
    test_circuit_description = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "rz", "qubits": [2], "params": [0.5]}
    ]
    num_qubits = 3

    try:
        parsed_qc = QASMParser.parse(test_circuit_description, num_qubits)
        print("Parsed QuantumCircuit:")
        print(parsed_qc)
    except ValueError as e:
        print(f"Error parsing circuit: {e}")

    # Test with invalid input
    invalid_description = [
        {"name": "h", "qubits": [0]},
        {"qubits": [0, 1]} # Missing name
    ]
    try:
        QASMParser.parse(invalid_description, 2)
    except ValueError as e:
        print(f"Error parsing invalid circuit: {e}")

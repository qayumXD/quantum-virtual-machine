# src/qvm/parser.py

"""
Parser for converting a simple circuit description into the Intermediate Representation (IR).
"""

from typing import List, Dict, Any
from qvm.ir import QuantumCircuit

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
        cregs: Dict[str, int] = {}          # name -> size (QASM2 allows several)
        default_creg = "c"                  # fallback when no creg is declared

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
                # creg name[size];
                body = line.split(None, 1)[1]
                name = body.split("[", 1)[0].strip()
                size = int(body.split("[", 1)[1].split("]", 1)[0])
                qc.add_classical_register(name, size)
                cregs[name] = size
                default_creg = name
                continue
            if line.lower().startswith("measure"):
                triples = OpenQASM2Parser._parse_measure(line, num_qubits, cregs, default_creg)
                for qubit_idx, reg_name, bit_idx in triples:
                    qc.add_operation("measure", [qubit_idx],
                                     target_bit=(reg_name, bit_idx))
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
    def _parse_measure(line: str, num_qubits: int, cregs: Dict[str, int], default_creg: str):
        """Parse a measure statement into concrete (qubit, creg, bit) triples.

        Supported forms::

            measure q[0] -> c[1];    single qubit → single classical bit
            measure q -> c;          full register → full register
        """
        parts = line.replace("measure", "", 1).split("->")
        if len(parts) != 2:
            raise ValueError(f"Invalid measure syntax: {line!r}")
        lhs = parts[0].strip()
        rhs = parts[1].strip()

        # Source side
        if "[" in lhs:
            src = [int(lhs.split("[", 1)[1].split("]", 1)[0])]
        else:
            src = list(range(num_qubits))

        # Destination side
        if "[" in rhs:
            cname = rhs.split("[", 1)[0].strip()
            base = int(rhs.split("[", 1)[1].split("]", 1)[0])
            if len(src) != 1:
                raise ValueError(f"Invalid measure mapping: {line!r}")
            dests = [(cname, base)]
        else:
            cname = rhs
            size = cregs.get(cname)
            if size is None:
                raise ValueError(f"measure targets undeclared classical register '{cname}'")
            if size < len(src):
                raise ValueError(
                    f"register measure mismatch: {len(src)} qubits -> {cname}[{size}]"
                )
            dests = [(cname, i) for i in range(len(src))]

        return [(q, d[0], d[1]) for q, d in zip(src, dests)]

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

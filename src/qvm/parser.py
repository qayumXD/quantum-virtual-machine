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

# src/qvm/ir.py

"""
Intermediate Representation (IR) for Quantum Circuits.
Defines data structures to represent quantum circuits in a hardware-agnagnostic way.
"""

class QuantumCircuit:
    def __init__(self, num_qubits: int):
        if not isinstance(num_qubits, int) or num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer.")
        self.num_qubits = num_qubits
        self.operations = [] # List of dictionaries, each representing a gate operation

    def add_operation(self, gate_name: str, qubits: list, params: list = None):
        """
        Adds a quantum gate operation to the circuit.

        Args:
            gate_name (str): The name of the quantum gate (e.g., "h", "cx", "rz").
            qubits (list): A list of integer indices representing the target qubits.
            params (list, optional): A list of parameters for the gate (e.g., angle for RZ gate). Defaults to None.
        """
        if not isinstance(gate_name, str) or not gate_name:
            raise ValueError("Gate name must be a non-empty string.")
        if not isinstance(qubits, list) or not all(isinstance(q, int) and 0 <= q < self.num_qubits for q in qubits):
            raise ValueError(f"Qubits must be a list of integers within [0, {self.num_qubits-1}].")
        if params is not None and not isinstance(params, list):
            raise ValueError("Parameters must be a list or None.")

        operation = {
            "name": gate_name,
            "qubits": qubits,
            "params": params if params is not None else []
        }
        self.operations.append(operation)

    def __str__(self):
        s = f"QuantumCircuit(num_qubits={self.num_qubits})\n"
        for op in self.operations:
            s += f"  {op['name']} {op['qubits']}"
            if op['params']:
                s += f" {op['params']}"
            s += "\n"
        return s

    def __repr__(self):
        return f"QuantumCircuit(num_qubits={self.num_qubits}, operations={self.operations})"

# Example Usage (for testing during development)
if __name__ == "__main__":
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("rz", [2], [0.5])
    qc.add_operation("measure", [0, 1, 2])
    print(qc)

    # Test error handling
    try:
        QuantumCircuit(0)
    except ValueError as e:
        print(f"Error: {e}")

    try:
        qc.add_operation("h", [5])
    except ValueError as e:
        print(f"Error: {e}")

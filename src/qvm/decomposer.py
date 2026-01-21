# src/qvm/decomposer.py

"""
Decomposes complex quantum gates into a sequence of simpler, native gates.
"""

from src.qvm.ir import QuantumCircuit

class Decomposer:
    """
    A simple decomposer that can break down specific complex gates.
    """
    def __init__(self, native_gates: set):
        self.native_gates = native_gates

    def decompose_operation(self, op: dict) -> list:
        """
        Decomposes a single gate operation if it's not in the native gate set.
        Returns a list of simpler operations.
        """
        gate_name = op["name"]
        
        if gate_name in self.native_gates:
            return [op] # Already native, no decomposition needed

        if gate_name == "toffoli" or gate_name == "ccx":
            return self._decompose_toffoli(op)
        
        # In a real decomposer, you would add more decompositions here.
        raise ValueError(f"No decomposition rule available for gate: {gate_name}")

    def _decompose_toffoli(self, op: dict) -> list:
        """
        Decomposes a Toffoli (CCX) gate into H, CNOT, and RZ(pi/4) (T) gates.
        This is a standard decomposition. T = RZ(pi/4), Tdg = RZ(-pi/4).
        """
        qubits = op["qubits"]
        if len(qubits) != 3:
            raise ValueError("Toffoli gate must act on 3 qubits.")
        c1, c2, t = qubits[0], qubits[1], qubits[2]
        
        import numpy as np
        pi_4 = np.pi / 4

        # The sequence of gates to replace the Toffoli gate
        decomposition = [
            {"name": "h", "qubits": [t], "params": []},
            {"name": "cx", "qubits": [c2, t], "params": []},
            {"name": "rz", "qubits": [t], "params": [-pi_4]}, # Tdg
            {"name": "cx", "qubits": [c1, t], "params": []},
            {"name": "rz", "qubits": [t], "params": [pi_4]},  # T
            {"name": "cx", "qubits": [c2, t], "params": []},
            {"name": "rz", "qubits": [t], "params": [-pi_4]}, # Tdg
            {"name": "cx", "qubits": [c1, t], "params": []},
            {"name": "rz", "qubits": [c2], "params": [pi_4]},  # T on c2
            {"name": "rz", "qubits": [t], "params": [pi_4]},   # T on t
            {"name": "h", "qubits": [t], "params": []},
            {"name": "cx", "qubits": [c1, c2], "params": []},
            {"name": "rz", "qubits": [c1], "params": [pi_4]},  # T on c1
            {"name": "rz", "qubits": [c2], "params": [-pi_4]}, # Tdg on c2
            {"name": "cx", "qubits": [c1, c2], "params": []},
        ]
        return decomposition

    def decompose_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Decomposes all non-native gates in a circuit.
        """
        decomposed_circuit = QuantumCircuit(circuit.num_qubits)
        for op in circuit.operations:
            decomposed_ops = self.decompose_operation(op)
            for new_op in decomposed_ops:
                decomposed_circuit.add_operation(new_op["name"], new_op["qubits"], new_op["params"])
        return decomposed_circuit

# Example Usage
if __name__ == "__main__":
    # Define a circuit with a Toffoli gate
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("h", [1])
    qc.add_operation("toffoli", [0, 1, 2]) # Should flip |000> to |001> after H gates
    
    print("Original Circuit:")
    print(qc)
    
    # Define a native gate set and decompose
    native_gates = {"h", "cx", "rz"}
    decomposer = Decomposer(native_gates)
    
    decomposed_qc = decomposer.decompose_circuit(qc)
    
    print("\nDecomposed Circuit:")
    print(decomposed_qc)

    # We could now simulate this decomposed_qc to verify it does the same as a Toffoli.

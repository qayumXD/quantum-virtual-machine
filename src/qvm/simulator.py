# src/qvm/simulator.py

"""
Statevector simulator for quantum circuits.
"""

import numpy as np
from src.qvm.ir import QuantumCircuit

class Simulator:
    def __init__(self):
        # Define common quantum gate matrices
        self.H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        self.X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.Z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.I = np.array([[1, 0], [0, 1]], dtype=complex) # Identity gate

        # Placeholder for CNOT, which is more complex to define generally
        # and better constructed dynamically or applied specifically.

    def _get_rotation_matrix(self, angle: float, axis: str) -> np.ndarray:
        """Returns the rotation matrix for a given angle and axis."""
        if axis == 'x':
            return np.array([
                [np.cos(angle/2), -1j * np.sin(angle/2)],
                [-1j * np.sin(angle/2), np.cos(angle/2)]
            ], dtype=complex)
        elif axis == 'y':
            return np.array([
                [np.cos(angle/2), -np.sin(angle/2)],
                [np.sin(angle/2), np.cos(angle/2)]
            ], dtype=complex)
        elif axis == 'z':
            return np.array([
                [np.exp(-1j * angle/2), 0],
                [0, np.exp(1j * angle/2)]
            ], dtype=complex)
        else:
            raise ValueError(f"Invalid rotation axis: {axis}. Must be 'x', 'y', or 'z'.")

    def _get_gate_matrix(self, gate_name: str, params: list = None) -> np.ndarray:
        """Returns the matrix for a given gate name."""
        if gate_name == "h":
            return self.H
        elif gate_name == "x":
            return self.X
        elif gate_name == "y":
            return self.Y
        elif gate_name == "z":
            return self.Z
        elif gate_name == "rx":
            if not params: raise ValueError("RX gate requires an angle parameter.")
            return self._get_rotation_matrix(params[0], 'x')
        elif gate_name == "ry":
            if not params: raise ValueError("RY gate requires an angle parameter.")
            return self._get_rotation_matrix(params[0], 'y')
        elif gate_name == "rz":
            if not params: raise ValueError("RZ gate requires an angle parameter.")
            return self._get_rotation_matrix(params[0], 'z')
        elif gate_name == "id":
            return self.I
        else:
            # CNOT is handled separately due to its multi-qubit nature and specific application
            raise ValueError(f"Unsupported gate for matrix retrieval: {gate_name}")

    def _apply_single_qubit_gate(self, statevector: np.ndarray, gate_matrix: np.ndarray, target_qubit: int, num_qubits: int) -> np.ndarray:
        """Applies a single-qubit gate to the statevector."""
        # Construct the tensor product of identity and gate matrices
        # Note: We assume Little Endian ordering (Qubit 0 is LSB).
        # In np.kron(A, B), B is the LSB (fastest changing index).
        # So op_list should be [Q_n-1, ..., Q_1, Q_0].
        op_list = [self.I] * num_qubits
        op_list[num_qubits - 1 - target_qubit] = gate_matrix
        
        full_gate_matrix = op_list[0]
        for i in range(1, num_qubits):
            full_gate_matrix = np.kron(full_gate_matrix, op_list[i])

        # Apply the full gate matrix to the statevector
        return full_gate_matrix @ statevector

    def _apply_cnot_gate(self, statevector: np.ndarray, control_qubit: int, target_qubit: int, num_qubits: int) -> np.ndarray:
        """Applies a CNOT gate to the statevector."""
        new_statevector = statevector.copy()
        for i in range(2**num_qubits):
            if (i >> control_qubit) & 1:
                flipped_i = i ^ (1 << target_qubit)
                # Only perform the swap once for each pair (i, flipped_i)
                if i < flipped_i:
                    new_statevector[i], new_statevector[flipped_i] = new_statevector[flipped_i], new_statevector[i]
        return new_statevector

    def _apply_swap_gate(self, statevector: np.ndarray, q1: int, q2: int, num_qubits: int) -> np.ndarray:
        """Applies a SWAP gate to the statevector."""
        new_statevector = statevector.copy()
        for i in range(2**num_qubits):
            # Check if the bits at positions q1 and q2 are different
            bit1 = (i >> q1) & 1
            bit2 = (i >> q2) & 1
            if bit1 != bit2:
                # If they are different, find the index of the state with these bits swapped
                j = i ^ ((1 << q1) | (1 << q2))
                # Only swap amplitudes for states i < j to avoid swapping twice
                if i < j:
                    new_statevector[i], new_statevector[j] = new_statevector[j], new_statevector[i]
        return new_statevector

    def simulate(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Simulates the given quantum circuit and returns the final statevector.
        """
        num_qubits = circuit.num_qubits
        statevector = np.zeros(2**num_qubits, dtype=complex)
        statevector[0] = 1.0 # Initialize in |0...0> state

        for op in circuit.operations:
            gate_name = op["name"]
            qubits = op["qubits"]
            params = op["params"]

            if gate_name in ["h", "x", "y", "z", "rx", "ry", "rz", "id"]:
                if len(qubits) != 1:
                    raise ValueError(f"{gate_name} gate must act on a single qubit, but got {qubits}")
                gate_matrix = self._get_gate_matrix(gate_name, params)
                statevector = self._apply_single_qubit_gate(statevector, gate_matrix, qubits[0], num_qubits)
            elif gate_name == "cx":
                if len(qubits) != 2:
                    raise ValueError(f"{gate_name} gate must act on two qubits, but got {qubits}")
                control_qubit, target_qubit = qubits[0], qubits[1]
                statevector = self._apply_cnot_gate(statevector, control_qubit, target_qubit, num_qubits)
            elif gate_name == "swap":
                if len(qubits) != 2:
                    raise ValueError(f"swap gate must act on two qubits, but got {qubits}")
                q1, q2 = qubits[0], qubits[1]
                statevector = self._apply_swap_gate(statevector, q1, q2, num_qubits)
            elif gate_name == "measure":
                # Measurement is handled separately; for statevector simulator,
                # we primarily care about probabilities, not collapse until explicitly asked.
                # For now, we just pass over measure operations in terms of state evolution.
                pass
            else:
                raise ValueError(f"Unsupported gate operation: {gate_name}")

        # Normalize the statevector to account for potential floating point inaccuracies
        statevector = statevector / np.linalg.norm(statevector)
        return statevector

    def get_probabilities(self, statevector: np.ndarray) -> np.ndarray:
        """Calculates measurement probabilities from a statevector."""
        return np.abs(statevector)**2

# Example Usage (for testing during development)
if __name__ == "__main__":
    from src.qvm.ir import QuantumCircuit
    from src.qvm.parser import QASMParser

    sim = Simulator()

    # Test Bell State circuit
    bell_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]}
    ]
    bell_qc = QASMParser.parse(bell_circuit_desc, 2)
    bell_state = sim.simulate(bell_qc)
    bell_probs = sim.get_probabilities(bell_state)
    print("Bell State Simulation:")
    print("Statevector:", bell_state)
    print("Probabilities:", bell_probs) # Expected: [0.5, 0., 0., 0.5] for |00> and |11>

    # Test GHZ State circuit (3 qubits)
    ghz_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    ghz_qc = QASMParser.parse(ghz_circuit_desc, 3)
    ghz_state = sim.simulate(ghz_qc)
    ghz_probs = sim.get_probabilities(ghz_state)
    print("\nGHZ State Simulation:")
    print("Statevector:", ghz_state)
    print("Probabilities:", ghz_probs) # Expected: [0.5, 0., 0., 0., 0., 0., 0., 0.5] for |000> and |111>

    # Test single qubit rotation
    rx_circuit_desc = [
        {"name": "rx", "qubits": [0], "params": [np.pi/2]}
    ]
    rx_qc = QASMParser.parse(rx_circuit_desc, 1)
    rx_state = sim.simulate(rx_qc)
    rx_probs = sim.get_probabilities(rx_state)
    print("\nRX(pi/2) on qubit 0 Simulation:")
    print("Statevector:", rx_state)
    print("Probabilities:", rx_probs) # Expected: [0.5, 0.5] for |0> and |1> (up to phase)

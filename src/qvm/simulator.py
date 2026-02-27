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
        """Applies a CNOT gate to the statevector using vectorized operations."""
        # Vectorized implementation for performance
        N = 2**num_qubits
        indices = np.arange(N)
        
        # Identify states where control qubit is 1
        control_mask = (indices >> control_qubit) & 1 == 1
        
        # Calculate the destination indices
        # If control is 0, dest is same as src (no change)
        # If control is 1, dest is src flipped at target bit
        target_bit_mask = 1 << target_qubit
        permuted_indices = indices.copy()
        permuted_indices[control_mask] = indices[control_mask] ^ target_bit_mask
        
        # Apply the permutation to the statevector
        # new_state[i] comes from old_state[permuted_indices[i]]? 
        # No, new_state[i] is the amplitude of state |i>.
        # If the operation maps |j> -> |k>, then new_state[k] = old_state[j].
        # Since CNOT is its own inverse (unitary and hermitian), |k> -> |j> also holds.
        # So new_state[i] = old_state[permuted_indices[i]] works.
        return statevector[permuted_indices]

    def _apply_swap_gate(self, statevector: np.ndarray, q1: int, q2: int, num_qubits: int) -> np.ndarray:
        """Applies a SWAP gate to the statevector using vectorized operations."""
        N = 2**num_qubits
        indices = np.arange(N)
        
        # Check bits at q1 and q2
        bit1 = (indices >> q1) & 1
        bit2 = (indices >> q2) & 1
        
        # Identify where bits are different
        diff_mask = bit1 != bit2
        
        # Calculate swap mask (flip both q1 and q2)
        swap_mask = (1 << q1) | (1 << q2)
        
        # Construct permutation indices
        permuted_indices = indices.copy()
        permuted_indices[diff_mask] = indices[diff_mask] ^ swap_mask
        
        return statevector[permuted_indices]

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

    def sample(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        seed: int | None = None,
        depol_prob: float = 0.0,
        readout_error: float = 0.0,
    ) -> dict:
        """
        Draws measurement samples from the final state of the circuit.

        Measurement gates in the circuit are treated as an instruction to
        include those qubits in the reported bitstrings. If no measurement
        operations are present, all qubits are measured.

        Args:
            circuit: QuantumCircuit to execute.
            shots: Number of samples to draw.
            seed: Optional RNG seed for reproducibility.

        Noise model (educational, simplified):
            depol_prob: mixes final distribution with uniform with weight p.
            readout_error: per-bit flip probability applied after sampling.

        Returns:
            dict mapping measured bitstrings -> counts.
        """
        if shots <= 0:
            raise ValueError("shots must be a positive integer")
        if not 0 <= depol_prob <= 1:
            raise ValueError("depol_prob must be in [0,1]")
        if not 0 <= readout_error <= 1:
            raise ValueError("readout_error must be in [0,1]")

        measured_qubits = self._extract_measured_qubits(circuit)
        if not measured_qubits:
            measured_qubits = list(range(circuit.num_qubits))

        state = self.simulate(circuit)
        probs = self.get_probabilities(state)

        # Apply simple depolarizing noise: mix with uniform distribution
        if depol_prob > 0:
            uniform = 1 / len(probs)
            probs = (1 - depol_prob) * probs + depol_prob * uniform

        rng = np.random.default_rng(seed)
        outcomes = rng.choice(len(probs), size=shots, p=probs)

        counts: dict[str, int] = {}
        for outcome in outcomes:
            bitstring = format(outcome, f"0{circuit.num_qubits}b")
            # Little-endian convention: qubit 0 is LSB (rightmost)
            measured_bits = "".join(bitstring[circuit.num_qubits - 1 - q] for q in measured_qubits)

            if readout_error > 0:
                measured_bits = self._apply_readout_noise(measured_bits, readout_error, rng)

            counts[measured_bits] = counts.get(measured_bits, 0) + 1

        return counts

    def sample_with_collapse(self, circuit: QuantumCircuit, shots: int = 1024, seed: int | None = None) -> dict:
        """
        Execute the circuit shot-by-shot, applying projective measurements when encountered.
        Outputs counts keyed by measured-qubit bitstrings (sorted qubit indices).
        """
        if shots <= 0:
            raise ValueError("shots must be a positive integer")

        measured_qubits = self._extract_measured_qubits(circuit)
        if not measured_qubits:
            measured_qubits = list(range(circuit.num_qubits))

        rng = np.random.default_rng(seed)
        counts: dict[str, int] = {}

        for _ in range(shots):
            state = np.zeros(2 ** circuit.num_qubits, dtype=complex)
            state[0] = 1.0

            for op in circuit.operations:
                name, qubits, params = op["name"], op["qubits"], op["params"]
                if name in ["h", "x", "y", "z", "rx", "ry", "rz", "id"]:
                    gate_matrix = self._get_gate_matrix(name, params)
                    state = self._apply_single_qubit_gate(state, gate_matrix, qubits[0], circuit.num_qubits)
                elif name == "cx":
                    state = self._apply_cnot_gate(state, qubits[0], qubits[1], circuit.num_qubits)
                elif name == "swap":
                    state = self._apply_swap_gate(state, qubits[0], qubits[1], circuit.num_qubits)
                elif name == "measure":
                    outcome, state = self._measure_and_collapse(state, qubits, circuit.num_qubits, rng)
                else:
                    raise ValueError(f"Unsupported gate operation: {name}")

            # Final measurement of requested qubits
            measured_bits, _ = self._measure_and_collapse(state, measured_qubits, circuit.num_qubits, rng)
            counts[measured_bits] = counts.get(measured_bits, 0) + 1

        return counts

    @staticmethod
    def _extract_measured_qubits(circuit: QuantumCircuit) -> list:
        """Return sorted unique qubit indices that are explicitly measured."""
        measured = []
        for op in circuit.operations:
            if op["name"] == "measure":
                measured.extend(op["qubits"])
        return sorted(set(measured))

    @staticmethod
    def _apply_readout_noise(bitstring: str, flip_prob: float, rng) -> str:
        bits = list(bitstring)
        for i, b in enumerate(bits):
            if rng.random() < flip_prob:
                bits[i] = "0" if b == "1" else "1"
        return "".join(bits)

    @staticmethod
    def _measure_and_collapse(statevector: np.ndarray, qubits: list, num_qubits: int, rng) -> tuple[str, np.ndarray]:
        """
        Measure the given qubits, collapse the state, and return (bitstring, collapsed_state).
        """
        if not qubits:
            return "", statevector

        # Compute probabilities for each outcome on the measured subset
        probs = {}
        indices = np.arange(len(statevector))
        for outcome in range(2 ** len(qubits)):
            mask = np.ones_like(statevector, dtype=bool)
            for i, q in enumerate(qubits):
                bit = (outcome >> i) & 1
                mask &= ((indices >> q) & 1) == bit
            probs[outcome] = float(np.sum(np.abs(statevector[mask]) ** 2))

        outcomes = np.array(list(probs.keys()))
        prob_vals = np.array(list(probs.values()))
        prob_vals = prob_vals / prob_vals.sum()
        sampled_outcome = int(rng.choice(outcomes, p=prob_vals))

        # Collapse state
        mask = np.ones_like(statevector, dtype=bool)
        indices = np.arange(len(statevector))
        for i, q in enumerate(qubits):
            bit = (sampled_outcome >> i) & 1
            mask &= ((indices >> q) & 1) == bit
        collapsed = np.zeros_like(statevector)
        collapsed[mask] = statevector[mask]
        collapsed = collapsed / np.linalg.norm(collapsed)

        bitstring = format(sampled_outcome, f"0{len(qubits)}b")[::-1]  # maintain little-endian order
        return bitstring, collapsed

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

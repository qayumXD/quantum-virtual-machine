# src/qvm/mps_simulator.py

"""
Matrix Product State (MPS) simulator for larger qubit counts.
Uses SVD-based compression to maintain a compact state representation.
"""

import numpy as np
from src.qvm.ir import QuantumCircuit

class MPSSimulator:
    def __init__(self, max_bond_dim: int = 16):
        self.max_bond_dim = max_bond_dim
        # Basis gate matrices
        self.H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        self.X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.I = np.array([[1, 0], [0, 1]], dtype=complex)

    def simulate(self, circuit: QuantumCircuit, seed: int = None) -> tuple[list, dict]:
        """
        Simulates the circuit using MPS.
        Returns: (list of tensors, classical_memory)
        """
        n = circuit.num_qubits
        self.tensors = [np.array([[[1.0], [0.0]]], dtype=complex) for _ in range(n)]
        classical_memory = {name: np.zeros(size, dtype=int) for name, size in circuit.classical_registers.items()}
        rng = np.random.default_rng(seed)
        
        for op in circuit.operations:
            name = op["name"]
            qubits = op["qubits"]
            params = op["params"]

            if name in ["h", "x", "y", "z", "rx", "ry", "rz", "p", "id"]:
                gate = self._get_gate_matrix(name, params)
                self._apply_single_qubit(qubits[0], gate)
            elif name == "cx":
                self._apply_cx(qubits[0], qubits[1])
            elif name == "swap":
                self._apply_swap(qubits[0], qubits[1])
            elif name == "measure":
                outcome = self._measure_qubit(qubits[0], rng)
                if op["target_bit"]:
                    reg_name, reg_idx = op["target_bit"]
                    classical_memory[reg_name][reg_idx] = outcome
        
        return self.tensors, classical_memory

    def _measure_qubit(self, q, rng) -> int:
        """Projective measurement on an MPS tensor."""
        # Compute probability of |0>
        # Trace out all other tensors (in our simple 1D chain, just contract local tensor)
        # Prob(0) = <psi | P0 | psi>
        # Since our tensors are normalized during SVD, we just check local norm
        t = self.tensors[q]
        # Contract over bond indices: sum_{L,R} |A(L, 0, R)|^2
        prob_0 = np.sum(np.abs(t[:, 0, :])**2)
        
        outcome = 0 if rng.random() < prob_0 else 1
        
        # Collapse: project and re-normalize
        if outcome == 0:
            t[:, 1, :] = 0
        else:
            t[:, 0, :] = 0
        
        norm = np.linalg.norm(t)
        if norm > 0:
            self.tensors[q] = t / norm
            
        return outcome

    def _get_gate_matrix(self, name, params):
        # Re-using logic from statevector simulator for simplicity
        if name == "h": return self.H
        if name == "x": return self.X
        if name == "id": return self.I
        angle = params[0] if params else 0
        if name == "rx": return np.array([[np.cos(angle/2), -1j*np.sin(angle/2)], [-1j*np.sin(angle/2), np.cos(angle/2)]])
        if name == "ry": return np.array([[np.cos(angle/2), -np.sin(angle/2)], [np.sin(angle/2), np.cos(angle/2)]])
        if name == "rz" or name == "p": return np.array([[1, 0], [0, np.exp(1j*angle)]])
        return self.I

    def _apply_single_qubit(self, q, gate):
        # Contract tensor with gate: (L, p, R) * (p_new, p) -> (L, p_new, R)
        self.tensors[q] = np.einsum('ijk,aj->iak', self.tensors[q], gate)

    def _apply_cx(self, ctrl, target):
        # For simplicity, assume ctrl and target are adjacent.
        # If not, we would normally use swaps (handled by transpiler).
        if abs(ctrl - target) != 1:
            # Educational shortcut: In a real MPS, you'd use a chain of swaps.
            # Here, we'll just fail if not adjacent to reinforce the MPS topology constraint.
            raise ValueError("MPSSimulator currently only supports nearest-neighbor CX gates.")
        
        q1, q2 = min(ctrl, target), max(ctrl, target)
        
        # 1. Contract A[q1] and A[q2]
        # A1: (L1, p1, R1), A2: (L2, p2, R2) where R1 == L2
        combined = np.einsum('ijk,klm->ijlm', self.tensors[q1], self.tensors[q2])
        # Result shape: (L1, p1, p2, R2)
        
        # 2. Apply CX
        # CX matrix for 2 qubits (4x4)
        cx_mat = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex).reshape(2, 2, 2, 2)
        
        # Contract: (L1, p1, p2, R2) with (p1_new, p2_new, p1, p2)
        if ctrl < target: # Standard CX
            combined = np.einsum('abcd,xybc->axyd', combined, cx_mat)
        else: # Reversed CX
            combined = np.einsum('abcd,xycb->axyd', combined, cx_mat)
            
        # 3. SVD to split back
        # Reshape for SVD: (L1 * p1_new, p2_new * R2)
        L1, p1, p2, R2 = combined.shape
        reshaped = combined.reshape(L1 * p1, p2 * R2)
        
        u, s, vh = np.linalg.svd(reshaped, full_matrices=False)
        
        # 4. Truncate
        dim = min(len(s), self.max_bond_dim)
        u = u[:, :dim]
        s = s[:dim]
        vh = vh[:dim, :]
        
        # 5. Distribute singular values (keep it canonical if possible)
        # We'll just put 's' into the left tensor for now
        u = u * s
        
        # 6. Store back
        self.tensors[q1] = u.reshape(L1, p1, dim)
        self.tensors[q2] = vh.reshape(dim, p2, R2)

    def _apply_swap(self, q1, q2):
        if abs(q1 - q2) != 1:
            raise ValueError("MPSSimulator currently only supports nearest-neighbor SWAP gates.")
        
        idx1, idx2 = min(q1, q2), max(q1, q2)
        # Contract
        combined = np.einsum('ijk,klm->ijlm', self.tensors[idx1], self.tensors[idx2])
        # Swap physical indices: (L1, p1, p2, R2) -> (L1, p2, p1, R2)
        combined = np.transpose(combined, (0, 2, 1, 3))
        # SVD split
        L1, p2, p1, R2 = combined.shape
        u, s, vh = np.linalg.svd(combined.reshape(L1*p2, p1*R2), full_matrices=False)
        dim = min(len(s), self.max_bond_dim)
        self.tensors[idx1] = (u[:, :dim] * s[:dim]).reshape(L1, p2, dim)
        self.tensors[idx2] = vh[:dim, :].reshape(dim, p1, R2)

    def get_statevector(self) -> np.ndarray:
        """Contracts the full MPS to return a standard statevector (for small N)."""
        res = self.tensors[0]
        for i in range(1, len(self.tensors)):
            res = np.einsum('ijk,klm->ijlm', res, self.tensors[i])
            # Reshape to merge bond index: (L_start, p1, p2, ..., pi, R_i)
            # Actually easier to merge into (1, p1*p2*...*pi, 1)
            L, *phys, R = res.shape
            new_phys_dim = np.prod(phys)
            res = res.reshape(L, new_phys_dim, R)
        
        return res.flatten()

if __name__ == "__main__":
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("cx", [1, 2]) # Bell state spread out
    
    sim = MPSSimulator()
    tensors = sim.simulate(qc)
    sv = sim.get_statevector()
    print("MPS Statevector (GHZ-ish):", np.round(sv, 3))
    # Expected: 1/sqrt(2) (|000> + |111>) -> [0.707, 0, 0, 0, 0, 0, 0, 0.707]

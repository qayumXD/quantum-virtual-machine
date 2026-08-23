# src/qvm/mps_simulator.py

"""
Matrix Product State (MPS) simulator for larger qubit counts.
Uses SVD-based compression to maintain a compact state representation.
"""

import numpy as np
from qvm.ir import QuantumCircuit
from qvm.parameter import resolve_param
from qvm.exceptions import UnsupportedGateError

class MPSSimulator:
    def __init__(self, max_bond_dim: int = 16):
        self.max_bond_dim = max_bond_dim
        # Basis gate matrices
        self.H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        self.X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.Z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.I = np.array([[1, 0], [0, 1]], dtype=complex)
        self.SX = 0.5 * np.array([[1+1j, 1-1j], [1-1j, 1+1j]], dtype=complex)
        self.S = np.array([[1, 0], [0, 1j]], dtype=complex)
        self.T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

    def simulate(self, circuit: QuantumCircuit, seed: int = None) -> tuple[list, dict]:
        """
        Simulates the circuit using MPS.
        Returns: (list of tensors, classical_memory)
        """
        circuit = circuit.lowered()   # expand multi-controlled macros
        n = circuit.num_qubits
        self.tensors = [np.array([[[1.0], [0.0]]], dtype=complex) for _ in range(n)]
        classical_memory = {name: np.zeros(size, dtype=int) for name, size in circuit.classical_registers.items()}
        rng = np.random.default_rng(seed)
        
        for op in circuit.operations:
            name = op["name"]
            qubits = op["qubits"]
            params = op["params"]

            if name in ["h", "x", "y", "z", "rx", "ry", "rz", "p", "id",
                        "sx", "sxdg", "s", "sdg", "t", "tdg"]:
                gate = self._get_gate_matrix(name, params)
                self._apply_single_qubit(qubits[0], gate)
            elif name == "cx":
                self._apply_cx(qubits[0], qubits[1])
            elif name == "cz":
                self._apply_cz(qubits[0], qubits[1])
            elif name == "swap":
                self._apply_swap(qubits[0], qubits[1])
            elif name == "rzz":
                self._apply_rzz(qubits[0], qubits[1],
                                float(resolve_param(params[0])))
            elif name == "rxx":
                self._apply_rxx(qubits[0], qubits[1],
                                float(resolve_param(params[0])))
            elif name == "cp":
                self._apply_cp(qubits[0], qubits[1],
                               float(resolve_param(params[0])))
            elif name in ("barrier", "delay"):
                pass
            elif name == "measure":
                outcome = self._measure_qubit(qubits[0], rng)
                if op["target_bit"]:
                    reg_name, reg_idx = op["target_bit"]
                    classical_memory[reg_name][reg_idx] = outcome
            else:
                raise UnsupportedGateError(
                    f"MPSSimulator cannot execute gate '{name}'. "
                    f"Run the Decomposer first or extend the engine."
                )
        
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
        if name == "h": return self.H
        if name == "x": return self.X
        if name == "y": return self.Y
        if name == "z": return self.Z
        if name == "id": return self.I
        if name == "sx": return self.SX
        if name == "sxdg": return self.SX.conj().T
        if name == "s": return self.S
        if name == "sdg": return self.S.conj().T
        if name == "t": return self.T
        if name == "tdg": return self.T.conj().T
        # Resolve symbolic parameters
        angle = resolve_param(params[0]) if params else 0
        if name == "rx": return np.array([[np.cos(angle/2), -1j*np.sin(angle/2)], [-1j*np.sin(angle/2), np.cos(angle/2)]])
        if name == "ry": return np.array([[np.cos(angle/2), -np.sin(angle/2)], [np.sin(angle/2), np.cos(angle/2)]])
        if name == "rz": return np.array([[np.exp(-1j*angle/2), 0], [0, np.exp(1j*angle/2)]])
        if name == "p": return np.array([[1, 0], [0, np.exp(1j*angle)]])
        raise ValueError(f"Unknown gate in MPS simulator: {name}")

    def _apply_single_qubit(self, q, gate):
        # Contract tensor with gate: (L, p, R) * (p_new, p) -> (L, p_new, R)
        self.tensors[q] = np.einsum('ijk,aj->iak', self.tensors[q], gate)

    def _route_and_apply(self, a, b, adjacent_fn):
        """Apply a two-site gate on non-adjacent wires by walking the states
        together with SWAP gates, applying at adjacency, then undoing.

        Logical wire identities are restored exactly, so subsequent
        operations are unaffected apart from bond-dimension truncation.
        """
        if a == b:
            raise ValueError("two-qubit gate needs distinct wires")
        swaps = []
        cur = b
        while abs(cur - a) != 1:
            nxt = cur - 1 if cur > a else cur + 1
            self._apply_swap(cur, nxt)
            swaps.append((cur, nxt))
            cur = nxt
        adjacent_fn(a, cur)
        for x, y in reversed(swaps):
            self._apply_swap(x, y)

    def _apply_cx(self, ctrl, target):
        if abs(ctrl - target) != 1:
            self._route_and_apply(ctrl, target, self._apply_cx_adjacent)
            return
        self._apply_cx_adjacent(ctrl, target)

    def _apply_cx_adjacent(self, ctrl, target):
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
            self._route_and_apply(q1, q2, self._apply_swap_adjacent)
            return
        self._apply_swap_adjacent(q1, q2)

    def _apply_swap_adjacent(self, q1, q2):
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

    def _apply_cz(self, ctrl, target):
        """Apply CZ gate using CX decomposition: H-CX-H."""
        self._apply_single_qubit(target, self.H)
        self._apply_cx(ctrl, target)
        self._apply_single_qubit(target, self.H)

    def _apply_rzz(self, a, b, theta):
        """RZZ(theta) = CX . RZ_b(theta) . CX  (exact, any distance)."""
        def block(x, y):
            self._apply_cx(x, y)
            self._apply_single_qubit(y, self._get_gate_matrix("rz", [theta]))
            self._apply_cx(x, y)
        self._route_and_apply(a, b, block)

    def _apply_rxx(self, a, b, theta):
        h = self._get_gate_matrix("h", [])
        self._apply_single_qubit(a, h)
        self._apply_single_qubit(b, h)
        self._apply_rzz(a, b, theta)
        self._apply_single_qubit(a, h)
        self._apply_single_qubit(b, h)

    def _apply_cp(self, a, b, lam):
        """CP(lam) ~ rz_a(lam/2) . rz_b(lam/2) . RZZ(-lam/2)   (up to global phase)."""
        self._apply_single_qubit(a, self._get_gate_matrix("rz", [lam / 2]))
        self._apply_single_qubit(b, self._get_gate_matrix("rz", [lam / 2]))
        self._apply_rzz(a, b, -lam / 2)

    def sample(self, circuit: QuantumCircuit, shots: int = 1024,
               seed: int = None) -> dict:
        """Run the circuit multiple times and collect measurement statistics.

        Each shot re-runs the full simulation for correct probabilistic behavior.
        """
        if shots <= 0:
            raise ValueError("shots must be a positive integer")

        rng = np.random.default_rng(seed)
        counts: dict[str, int] = {}

        for _ in range(shots):
            run_seed = int(rng.integers(0, 2**31 - 1))
            tensors, mem = self.simulate(circuit, seed=run_seed)
            sv = self.get_statevector()
            probs = np.abs(sv) ** 2
            probs = probs / probs.sum()  # Renormalize
            outcome = rng.choice(len(probs), p=probs)
            bitstring = format(outcome, f"0{circuit.num_qubits}b")
            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts

    def get_statevector(self) -> np.ndarray:
        """Contracts the full MPS to return a standard statevector (small N).

        Output uses QVM's little-endian convention (qubit 0 = least
        significant bit), matching Simulator / Qiskit.
        """
        res = self.tensors[0]
        for i in range(1, len(self.tensors)):
            res = np.einsum('ijk,klm->ijlm', res, self.tensors[i])
            L, *phys, R = res.shape
            res = res.reshape(L, int(np.prod(phys)), R)

        n = len(self.tensors)
        vec = res.reshape(-1).reshape([2] * n)      # site 0 = slowest axis
        vec = np.transpose(vec, axes=tuple(reversed(range(n))))
        return vec.reshape(-1)

if __name__ == "__main__":
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("cx", [1, 2]) # Bell state spread out
    
    sim = MPSSimulator()
    tensors, mem = sim.simulate(qc)
    sv = sim.get_statevector()
    print("MPS Statevector (GHZ-ish):", np.round(sv, 3))
    # Expected: 1/sqrt(2) (|000> + |111>) -> [0.707, 0, 0, 0, 0, 0, 0, 0.707]

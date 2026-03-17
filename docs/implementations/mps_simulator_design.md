# Matrix Product State (MPS) Simulator Design

**Timestamp:** 2026-03-17T22:30:00Z

## 1. Rationale
The standard statevector simulator scales exponentially ($2^N$), limiting the QVM to ~12-15 qubits on consumer hardware. Matrix Product States (MPS) represent the quantum state as a 1D chain of tensors, allowing for linear scaling $O(N)$ for states with limited entanglement. This enables the simulation of hundreds of qubits for "shallow" or low-entanglement circuits.

## 2. Mathematical Foundation
A state $|\psi\rangle$ is decomposed into $N$ local tensors $A^{(i)}$:
$$|\psi\rangle = \sum_{j_1...j_n} A_{1, \alpha_1}^{(1)j_1} A_{\alpha_1, \alpha_2}^{(2)j_2} ... A_{\alpha_{n-1}, 1}^{(n)j_n} |j_1 j_2 ... j_n\rangle$$
where $j_i$ are physical indices ($0, 1$) and $\alpha_i$ are bond indices.

## 3. Implementation Strategy

### 3.1. Data Structure
`MPSSimulator` will store a list of `numpy` arrays.
*   Initial $|0\rangle^{\otimes N}$ state: $N$ tensors of shape `(1, 2, 1)`.

### 3.2. Operations
*   **Single-Qubit Gate:** Direct contraction with the physical index of tensor $i$.
*   **Two-Qubit Gate (Adjacent):** 
    1.  Contract $A^{(i)}$ and $A^{(i+1)}$ into a single tensor.
    2.  Apply the two-qubit gate.
    3.  Perform **Singular Value Decomposition (SVD)**.
    4.  Truncate singular values (bond dimension $\chi$) to maintain efficiency.
*   **Non-Adjacent Gates:** Require SWAP gates to bring qubits together (Transpiler integration).

## 4. Truncation & Bond Dimension
The efficiency of MPS comes from limiting the bond dimension $\chi$. If $\chi$ is allowed to grow to $2^{N/2}$, it is exact but exponential. By setting a `max_bond_dimension` (e.g., 16 or 32), we trade fidelity for performance.

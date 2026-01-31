# Quantum Logic Implementation

This document explains the mathematical and physical logic used in the simulator.

## 1. Statevector Representation
A quantum state of $N$ qubits is represented by a complex vector of size $2^N$.
$$ |\psi\rangle = \alpha_0|0...00\rangle + \alpha_1|0...01\rangle + ... + \alpha_{2^N-1}|1...11\rangle $$
Constraint: $\sum |\alpha_i|^2 = 1$.

In `simulator.py`, this is `self.statevector`: a 1D NumPy array of `dtype=complex128`.

## 2. Gate Application (Linear Algebra)

### Single Qubit Gates
A gate $U$ acting on qubit $k$ in an $N$-qubit system is mathematically the tensor product:
$$ U_{global} = I^{\otimes (N-1-k)} \otimes U \otimes I^{\otimes k} $$
*(Note: Ordering depends on Little Endian vs Big Endian conventions. We use Little Endian where $q_0$ is LSB).*

**Implementation:**
We use `np.kron` (Kronecker product) to construct this matrix.
*   Pro: Simple to implement.
*   Con: Creates a $2^N \times 2^N$ matrix. For $N=10$, this is $1024 \times 1024$ (8MB). For $N=20$, this is huge (Terabytes).
*   *Optimization used:* We only support up to 10-12 qubits, so `np.kron` is acceptable.

### CNOT (Controlled-NOT)
Matrix form is a permutation matrix.
Instead of multiplying by a matrix, we use **Index Permutation**.

Rule: $CNOT(c, t)|x\rangle$:
*   If bit $c$ of $x$ is 0: $|x\rangle \to |x\rangle$
*   If bit $c$ of $x$ is 1: $|x\rangle \to |x \oplus 2^t\rangle$ (flip bit $t$)

**Vectorized Logic:**
1.  Create array of indices `[0, 1, ..., 2^N-1]`.
2.  Mask: `mask = (indices >> c) & 1` (find where control is 1).
3.  Target indices: `new_indices = indices ^ (1 << t)` (flip target bit).
4.  Permute: `state[indices where mask] = state[new_indices where mask]`.
   *(Actually, since it's a swap of pairs, we can just permute the whole array index map)*.

### SWAP
Rule: $SWAP(a, b)|x\rangle$:
*   If bit $a$ != bit $b$: Swap amplitudes.

**Vectorized Logic:**
1.  Identify indices where `bit_a != bit_b`.
2.  Compute swap partner index: `partner = index ^ (1<<a | 1<<b)`.
3.  Swap amplitudes.

## 3. Probability & Measurement
The probability of measuring basis state $|i\rangle$ is given by the Born rule:
$$ P(i) = |\alpha_i|^2 $$

**Implementation:**
`probs = np.abs(statevector)**2`

## 4. Qubit Ordering Convention
The project uses **Little Endian**.
*   Qubit 0 is the Least Significant Bit (LSB).
*   State index 1 ($...001_2$) corresponds to $|...001\rangle$ (Qubit 0 is 1).
*   In tensor products, Qubit 0 is the "fastest changing" index (rightmost in bitstring, rightmost in Kron product list).

---
tags: [simulation, statevector, linear-algebra, vectorization, numpy, measurement]
---
# 🧮 Exact Statevector Simulation

The Statevector Simulator, implemented in [simulator.py](file:///home/qayum/projects/quantum-virtual-machine/src/qvm/simulator.py), is the exact execution engine of the QVM. It represents the quantum state as a complex vector and applies unitary matrices to evolve the state.

---

## 💾 Mathematical State Representation

For an $N$-qubit system, the statevector is a $1\text{D}$ complex NumPy array of size $2^N$ (`dtype=complex128`):
$$ |\psi\rangle = \sum_{x=0}^{2^N-1} \alpha_x |x\rangle = \alpha_0|0\dots00\rangle + \alpha_1|0\dots01\rangle + \dots + \alpha_{2^N-1}|1\dots11\rangle $$

Under the **Born Rule**, the amplitudes must satisfy the normalization condition:
$$ \sum_{x=0}^{2^N-1} |\alpha_x|^2 = 1 $$

### Little-Endian Qubit Ordering
QVM uses the **Little-Endian** convention:
*   Qubit $0$ is the **Least Significant Bit (LSB)** (rightmost in bitstrings).
*   State index $1$ (binary $\dots001$) corresponds to state $|0\dots01\rangle$ (where Qubit $0$ is $1$, and all others are $0$).
*   In tensor products, Qubit $0$ is the fastest-changing index (rightmost in Kronecker products).

---

## ⚡ Vectorized Gate Application

Applying a gate to target qubits requires evolving the statevector $|\psi\rangle \to U |\psi\rangle$. To simulate this efficiently in Python, the simulator uses NumPy vectorization instead of loops.

### 1. Single-Qubit Gates (Tensor Product)
For a single-qubit gate $U$ acting on target qubit $k$, the global operator $U_{\text{global}}$ is:
$$ U_{\text{global}} = I^{\otimes (N-1-k)} \otimes U \otimes I^{\otimes k} $$

The simulator builds this $2^N \times 2^N$ matrix using `np.kron` and multiplies it by the statevector:
```python
def _apply_single_qubit_gate(self, state, gate, target, n):
    op_list = [self.I] * n
    op_list[n - 1 - target] = gate  # Reverse index for little-endian order
    full_op = op_list[0]
    for i in range(1, n):
        full_op = np.kron(full_op, op_list[i])
    return full_op @ state
```

---

### 2. Multi-Qubit Gates (Vectorized Index Permutation)
Creating a $2^N \times 2^N$ matrix for multi-qubit gates (like CNOT, CZ, SWAP) becomes memory intensive as $N$ grows. To avoid this, QVM uses **vectorized index permutation** to update the statevector directly.

#### A. CNOT Gate (Control $c$, Target $t$)
A CNOT gate flips the target qubit $t$ if the control qubit $c$ is $1$.
*   **Permutation Rule**: For all indices where the bit at position $c$ is $1$, swap the amplitude with the index where the bit at position $t$ is flipped.

```python
def _apply_cnot_gate(self, state, ctrl, target, n):
    indices = np.arange(2**n)
    # 1. Find indices where control bit is 1
    mask = (indices >> ctrl) & 1 == 1
    # 2. Compute partner indices by flipping target bit
    perm = indices.copy()
    perm[mask] = indices[mask] ^ (1 << target)
    # 3. Swap amplitudes via index slicing
    return state[perm]
```

#### B. SWAP Gate (Qubits $q_1, q_2$)
A SWAP gate swaps the states of qubits $q_1$ and $q_2$.
*   **Permutation Rule**: For all indices where the bit at position $q_1$ differs from the bit at position $q_2$, swap their amplitudes.

```python
def _apply_swap_gate(self, state, q1, q2, n):
    indices = np.arange(2**n)
    # Find indices where bit_q1 != bit_q2
    diff = ((indices >> q1) & 1) != ((indices >> q2) & 1)
    perm = indices.copy()
    # Flip both bits to find swap partner
    perm[diff] = indices[diff] ^ ((1 << q1) | (1 << q2))
    return state[perm]
```

#### C. CZ Gate (Control $c$, Target $t$)
A Controlled-Z gate applies a phase flip (multiplies by $-1$) only if both qubits are in the $|1\rangle$ state.
*   **Permutation Rule**: Identify indices where both bits at positions $c$ and $t$ are $1$, and multiply those amplitudes by $-1$.

```python
def _apply_cz_gate(self, state, ctrl, target, n):
    indices = np.arange(2**n)
    mask = ((indices >> ctrl) & 1 == 1) & ((indices >> target) & 1 == 1)
    result = state.copy()
    result[mask] = -result[mask]
    return result
```

---

## 📉 Projective Measurement and State Collapse

Mid-circuit measurement causes the quantum state to collapse. When measuring a subset of qubits $Q$:

1.  **Calculate Probabilities**: Computes the probability of each outcome on the measured qubits by summing the squared magnitudes of the matching statevector entries:
    $$ P(\text{outcome}) = \sum_{x \in \text{matching}} |\alpha_x|^2 $$
2.  **Stochastic Choice**: Samples an outcome based on these probabilities.
3.  **State Projection**: Set amplitudes of non-matching states to $0$:
    $$ \alpha_x \to 0 \quad \forall x \notin \text{matching} $$
4.  **Renormalization**: Renormalizes the remaining statevector to preserve probability conservation:
    $$ |\psi_{\text{collapsed}}\rangle = \frac{|\psi_{\text{projected}}\rangle}{\| |\psi_{\text{projected}}\rangle \|} $$

```python
# Project and collapse slice
collapsed = np.zeros_like(statevector)
collapsed[mask] = statevector[mask]
collapsed = collapsed / np.linalg.norm(collapsed)
```

---

## 🖥️ Classical Register Operations (`classical_op`)

The simulator contains a classical register execution engine. When it encounters a `classical_op` instruction, it evaluates classical bitwise expressions:

| Operator | Action | Implementation |
| :--- | :--- | :--- |
| `=` | Direct copy | `mem[target] = val` |
| `&` | Bitwise AND | `mem[target] = val1 & val2` |
| `\|` | Bitwise OR | `mem[target] = val1 \| val2` |
| `^` | Bitwise XOR | `mem[target] = val1 ^ val2` |
| `~` | Bitwise NOT | `mem[target] = ~val1 & 1` (keeps it single bit) |

This classical logic engine allows QVM to run hybrid quantum-classical algorithms, where future gate decisions are based on classical registers updated by mid-circuit measurements.

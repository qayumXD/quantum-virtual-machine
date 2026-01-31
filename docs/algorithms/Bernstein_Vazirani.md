# Bernstein-Vazirani Algorithm

The Bernstein-Vazirani algorithm is a quantum algorithm that finds a hidden bitstring $s$ in a single query ($O(1)$), whereas a classical computer would need $N$ queries (one for each bit).

## Problem Statement
Given a "black box" oracle function $f(x)$ defined as:
$$ f(x) = s  x \pmod 2 $$
Find the secret string $s = s_0s_1...s_{n-1}$.

## The Circuit
1.  **Initialization:** Start with $n$ input qubits in $|0\rangle$ and one ancilla qubit in $|1\rangle$.
2.  **Superposition:** Apply Hadamard ($H$) gates to all qubits.
    *   Input qubits become $|+\rangle^{\otimes n}$.
    *   Ancilla qubit becomes $|-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$.
3.  **Oracle:** Apply the function $f(x)$. In a quantum circuit, this is implemented using CNOT gates.
    *   If the $i$-th bit of $s$ is 1, apply a CNOT gate controlled by input qubit $i$ targeting the ancilla.
    *   This triggers "Phase Kickback", flipping the phase of the input state $|x\rangle$ only if $s \cdot x = 1$.
4.  **Interference:** Apply Hadamard ($H$) gates to all input qubits again.
    *   This constructive interference causes the state to collapse exactly to $|s\rangle$.
5.  **Measurement:** Measure the input qubits. The result is exactly the string $s$.

## Running the Example on QVM

We have provided a helper script to generate the circuit for any secret string.

### 1. Generate the Circuit
Generate a circuit for the secret string "101" (requires 3 input + 1 ancilla = 4 qubits).

```bash
python examples/generate_bv.py --secret 101 --output examples/bv_101.json
```

### 2. Run the Simulation
Run the QVM on the generated file. Note that we need 4 qubits.

```bash
python -m src.qvm.cli examples/bv_101.json --nqubits 4
```

### 3. Verify Results
The output should show a probability of 1.0 (or close to it) for the state `1010` (or `0101` depending on qubit ordering).
*   **Note on Ordering:** The QVM simulator uses Little Endian.
    *   If `q0` corresponds to the first bit of the secret, and the output format is `|q3 q2 q1 q0>`, you might need to interpret the bits accordingly.
    *   The ancilla is usually the last qubit.

**Expected Output for "101":**
The input qubits (0, 1, 2) should read "101". The ancilla (3) will be in $|-\rangle$ (superposition of 0 and 1), so you will see probabilities split across states ending in 0 and 1, but the input bits will effectively be fixed.

Actually, since we don't measure the ancilla in the script (it stays in $|-\rangle$), the statevector will be a tensor product $|-\rangle \otimes |101\rangle$.
Probabilities:
*   State `|1-101>` (ancilla=1) -> prob 0.5
*   State `|0-101>` (ancilla=0) -> prob 0.5
*   (Where `-` separates ancilla from inputs).

Look for the pattern in the input bits.

# Module Deep Dive

This document provides a detailed technical explanation of every function and class in the QVM source code (`src/qvm/`).

---

## 1. `src/qvm/ir.py`: Intermediate Representation

**Class:** `QuantumCircuit`

The backbone of the project. It represents the quantum program.

*   `__init__(self, num_qubits: int)`: Initializes an empty circuit with $N$ qubits.
*   `add_operation(self, name: str, qubits: list, params: list = [])`:
    *   **Logic:** Appends a dictionary `{'name': ..., 'qubits': ..., 'params': ...}` to `self.operations`.
    *   **Validation:** Basic checks could be added here (e.g., ensuring qubit index < num_qubits).
*   `__str__(self)`: Returns a simple string representation for debugging.

---

## 2. `src/qvm/simulator.py`: The Physics Engine

**Class:** `Simulator`

The heavy lifter. It maintains the statevector and evolves it.

*   **State Representation:**
    *   `statevector`: A NumPy array of complex numbers (dtype=`complex128`).
    *   Size: $2^N$. Index $i$ corresponds to the amplitude of basis state $|i\rangle$.
    *   Ordering: **Little Endian**. Index 0 is state $|0...00\rangle$, Index 1 is $|0...01\rangle$.

*   `simulate(self, circuit)` -> `np.ndarray`:
    *   Iterates through `circuit.operations`.
    *   Dispatches to specific handlers (`_apply_single_qubit_gate`, `_apply_cnot_gate`, `_apply_swap_gate`).

*   `_apply_single_qubit_gate(state, gate_matrix, target, n)`:
    *   **Technique:** Tensor Product.
    *   Ideally: $U_{full} = I \otimes ... \otimes U_{target} \otimes ... \otimes I$.
    *   Implementation: We construct `op_list` and use `np.kron` to build the $2^N \times 2^N$ matrix.
    *   *Note:* This is efficient for small $N$ but memory intensive. Future optimization: apply without full matrix construction.

*   `_apply_cnot_gate(state, ctrl, target, n)`:
    *   **Technique:** Vectorized Permutation.
    *   Logic: CNOT swaps amplitudes of $|...0...1...\rangle$ and $|...1...1...\rangle$ (where target bit flips) **if** control bit is 1.
    *   Code:
        ```python
        indices = np.arange(2**N)
        # Find indices where control bit is 1
        control_mask = (indices >> ctrl) & 1
        # Flip target bit for those indices
        permuted_indices = indices ^ (1 << target)
        # Update state (only where control_mask is true)
        return state[permuted_indices]
        ```

*   `_apply_swap_gate(state, q1, q2, n)`:
    *   **Technique:** Vectorized Permutation.
    *   Logic: If bit at `q1` != bit at `q2`, swap the amplitude with the state where those bits are flipped.

---

## 3. `src/qvm/transpiler.py`: The Topology Mapper

**Class:** `Transpiler`

Adapts the circuit to hardware.

*   `__init__(self, architecture)`: Accepts a `TargetArchitecture` object (defines connectivity).
*   `transpile(self, circuit)` -> `QuantumCircuit`:
    *   Maintain a `qubit_map` (Logical -> Physical).
    *   Iterate through gates.
    *   **Single Qubit Gates:** Just remap the qubit ID: `q_phys = map[q_log]`.
    *   **Two Qubit Gates (CNOT):**
        1.  Get physical locations `p1, p2` of the logical qubits.
        2.  Check `architecture.is_connected(p1, p2)`.
        3.  **If Connected:** Apply CNOT on `p1, p2`.
        4.  **If Not:**
            *   Find shortest path using `_bfs_shortest_path`.
            *   Insert `SWAP` gates along the path to move `p1` next to `p2`.
            *   **CRITICAL:** Update `qubit_map` after every SWAP! The logical qubit physically moves.
            *   Apply CNOT on the new adjacent positions.

---

## 4. `src/qvm/decomposer.py`: The Translator

**Class:** `Decomposer`

Breaks down high-level gates.

*   `decompose_circuit(self, circuit)`:
    *   Creates a new empty circuit.
    *   For each op, if it's in `native_gates`, copy it.
    *   If not (e.g., `toffoli`), call `_decompose_toffoli` and add the resulting list of operations.

*   `_decompose_toffoli(op)`:
    *   Hardcoded sequence of H, CNOT, T, Tdg gates that is mathematically equivalent to CCX.

---

## 5. `src/qvm/cli.py`: The Coordinator

The main script that ties everything together.

**Flow:**
1.  `argparse` reads command line args.
2.  `QASMParser` reads JSON file.
3.  `Decomposer` normalizes gates.
4.  (Optional) `Transpiler` maps to Linear topology.
5.  `Simulator` runs the circuit.
6.  `Visual` plots results.

```
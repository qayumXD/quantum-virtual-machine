# Simulator Optimization Report
**Date:** January 31, 2026

## 1. Optimization Goal
The goal of this phase was to improve the performance of the Statevector Simulator, specifically targeting the `CNOT` and `SWAP` gate applications. The initial implementation used explicit Python `for` loops iterating over $2^N$ states, which scales poorly ($O(2^N)$ in Python interpreter speed) as qubit count $N$ increases.

## 2. Technical Implementation
We replaced the Python loops with **NumPy Vectorization**.

### Methodology:
*   **Permutation Arrays:** Instead of iterating state-by-state, we construct a full index array `[0, ..., 2^N - 1]`.
*   **Bitwise Masking:** We use bitwise operations on the entire index array at once to identify states that satisfy the control condition (for CNOT) or have differing bits (for SWAP).
*   **Fancy Indexing:** We compute the `permuted_indices` array, where `permuted_indices[i]` is the index of the state that maps to state `i`.
*   **Operation:** The update is a single NumPy slice operation: `new_state = state[permuted_indices]`.

### Code Changes:
*   **`_apply_cnot_gate`:** 
    *   Old: Loop `range(2**N)`, `if check`, `swap`.
    *   New: `indices ^ (1 << target)` where `(indices >> control) & 1`.
*   **`_apply_swap_gate`:**
    *   Old: Loop `range(2**N)`, `if diff`, `swap`.
    *   New: `indices ^ (1 << q1 | 1 << q2)` where `bit1 != bit2`.

## 3. Verification
*   **Tests:** All existing tests in `tests/test_simulator.py` passed (Bell state, GHZ state).
*   **Correctness:** The vectorized approach is mathematically equivalent to the iterative approach but executes in C-level optimized code via NumPy.

## 4. Expected Impact
*   **Small Circuits ($N < 10$):** Negligible difference, possibly slightly faster.
*   **Large Circuits ($N \approx 10-14$):** Significant speedup (potentially orders of magnitude) because we avoid the overhead of Python's interpreter loop for millions of elements.
*   **Memory:** Slight increase in memory usage (creating integer index arrays of size $2^N$), but well within limits for the target scope (12 qubits = 4096 complex doubles + 4096 int64 indices is tiny).

## 5. Next Steps
*   **Profiling:** If larger scale tests are added, we can profile to confirm the speedup.
*   **CLI:** Implement a Command Line Interface to easily run simulations with larger qubit counts to demonstrate the performance.

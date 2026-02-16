# Report: Transpiler Correction and Future Enhancements

**Date:** 2026-02-16

This report documents the proposed fix for the transpiler correctness bug discovered during our analysis session and outlines several other potential enhancements for the QVM project.

---

## 1. High-Priority: Transpiler Correctness Bug Fix

A critical bug was identified in the transpiler's logic, as documented in `docs/steps/known_issues.md` and proven by the `test_transpilation_is_logically_correct` unit test.

### Proposed Solution: "Swap-Operate-Unswap" Strategy

The current "greedy" move-and-leave strategy is flawed. The proposed solution is to replace it with a logically sound **"Swap-Operate-Unswap"** algorithm within the `transpile` method of `src/qvm/transpiler.py`.

The new algorithm for handling a non-adjacent 2-qubit gate will be:

1.  **Find Path:** Use the existing `_bfs_shortest_path` method to find the shortest path of physical qubits between the two target physical qubits.

2.  **Generate & Apply Forward SWAPs:** Iterate along the path to generate a sequence of `SWAP` operations needed to make the qubits adjacent. Apply these `SWAP`s to the `physical_circuit` and update the `qubit_map` accordingly. Keep this sequence of SWAPs in a list.

3.  **Apply Core Gate:** Apply the original gate (e.g., `CX`) to the now-adjacent physical qubits.

4.  **Apply Backward SWAPs:** Iterate through the list of SWAPs from step 2 **in reverse order**. Apply each `SWAP` again to the `physical_circuit` and update the `qubit_map`. This "un-swaps" the qubits, restoring the logical-to-physical mapping and ensuring correctness for subsequent operations.

### Verification Plan

The success of this fix will be verified when the `test_transpilation_is_logically_correct` test case in `tests/test_transpiler.py` passes successfully.

---

## 2. Other Proposed Enhancements

Beyond the critical bug fix, several areas of the project could be enhanced to increase its capability and realism.

### A. Transpiler Optimizations

The "Swap-Operate-Unswap" method is correct, but not always the most efficient in terms of the total number of gates. Future work could explore more advanced transpilation strategies that aim to minimize the overall circuit depth or SWAP count, such as:
- **Lookahead Strategies:** Analyzing several upcoming gates to find a more optimal qubit mapping.
- **Global SWAP Optimization:** Using more complex routing algorithms (e.g., A* search) that consider the full circuit.

### B. Decomposer Expansion

The `Decomposer` currently only has a rule for the Toffoli (`ccx`) gate. It could be expanded to support other common gates, making the QVM more versatile.
- **Fredkin (CSWAP) gate**
- **Controlled Rotation gates (CRX, CRY, CRZ)**
- **Multi-controlled gates (e.g., CCCX)**

### C. Architecture Flexibility

The project could be enhanced to support more realistic hardware topologies beyond a simple linear chain.
- **Implementation:** Add new functions to `src/qvm/architecture.py` to generate different connectivity graphs (e.g., `get_grid_architecture(rows, cols)`, `get_heavy_hex_architecture`).
- **Testing:** Test the transpiler's performance and correctness against these more complex layouts.

### D. CLI Enhancements

The Command Line Interface (`src/qvm/cli.py`) could be improved for better usability.
- **Direct QASM Input:** Add support for directly reading standard OpenQASM 2.0 (`.qasm`) files instead of only the custom JSON format. This would require expanding the `parser`.
- **Dynamic Architecture Selection:** Allow the user to specify a target architecture (e.g., `--arch linear:5` or `--arch grid:2x3`) from the command line instead of it being hardcoded.

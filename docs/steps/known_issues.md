# Known Issues

This document lists known bugs and logical issues in the QVM project.

---

## 1. Transpiler Correctness Bug in Greedy Strategy

A bug has been identified in the current transpilation logic within `src/qvm/transpiler.py`.

**Symptoms:**
- The transpiler uses a "greedy" or "move-and-leave" strategy to handle non-adjacent two-qubit gates. It inserts SWAP gates to move logical qubits to adjacent physical locations but does not move them back.
- This strategy produces a physical circuit that is runnable but is **not logically equivalent** to the original circuit.
- The final quantum state produced by the transpiled circuit is incorrect.

**Example:**
- **Logical Circuit:** `H(0); CX(0,2)` on a 3-qubit system.
- **Hardware:** A linear architecture (`0-1-2`).
- **Expected Final State:** An equal superposition of `|000>` and `|101>`.
- **Actual Final State:** The transpiled circuit produces an equal superposition of `|000>` and `|110>` (assuming little-endian qubit ordering).

**Evidence:**
- This bug is formally captured and proven by the `test_transpilation_is_logically_correct` test case added to `tests/test_transpiler.py`.
- Running `pytest` shows this specific test failing with an `AssertionError` when comparing the expected and actual final statevectors.

---

## 2. Recommended Next Steps

The immediate priority for the next development session should be to fix this correctness bug.

**Action Items for the Next Session:**
1.  **Fix the Transpiler Logic:** Modify `src/qvm/transpiler.py` to implement a correct routing algorithm, such as the "swap, operate, un-swap" strategy.
2.  **Verify the Fix:** Run the test suite (`pytest tests/test_transpiler.py`). The fix is considered successful when the `test_transpilation_is_logically_correct` test case passes.

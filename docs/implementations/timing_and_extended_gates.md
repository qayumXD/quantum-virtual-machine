# Timing Semantics and Extended Gate Set

**Timestamp:** 2026-03-17T20:45:00Z

## 1. Rationale
OpenQASM 3.0 introduces physical timing and a standardized set of gates (`stdgates.inc`). To support hardware-realistic simulations and complex algorithms, the QVM must recognize temporal delays and a broader array of unitary operations.

## 2. Timing Implementation
*   **Grammar:** Added `delay[duration] qubits;` where duration includes a value and a unit (e.g., `ns`, `us`, `ms`).
*   **IR:** Operations now include an optional `duration` field.
*   **Simulator:** `delay` is currently treated as a "no-operation" (NOP) in terms of statevector evolution but is tracked for future pulse-level or decoherence simulation.

## 3. Extended Gate Set
The simulator now supports the following additional gates from `stdgates.inc`:
*   **Single-Qubit:** `sx` (sqrt-X), `sxdg`, `s`, `sdg`, `t`, `tdg`, `p(λ)`.
*   **Three-Qubit:** `ccx` (Toffoli) - natively supported in the simulator for performance.

## 4. Implementation Details
*   **Lark Grammar:** Updated to support `duration` and `delay` statements.
*   **Simulator:** Expanded `_get_gate_matrix` and added a `_apply_ccx_gate` method for vectorized Toffoli execution.

# Classical Memory Integration & Active Feedback

**Timestamp:** 2026-03-17T20:15:00Z

## 1. Rationale
To achieve OpenQASM 3.0 compliance, the QVM must support "Active Feedback"—the ability to perform quantum operations based on real-time classical measurement results. This requires a decoupled but synchronized classical memory bank that persists alongside the quantum statevector.

## 2. Architectural Changes

### 2.1. Intermediate Representation (IR)
*   **ClassicalRegister:** A new entity in `QuantumCircuit` to track named bit arrays.
*   **Conditional Operations:** Operations now optionally include a `condition` field, mapping a classical bit index and value to the execution of the gate.

### 2.2. Simulator Logic
*   **Classical Memory:** The `Simulator` now maintains a `classical_memory` dictionary (mapping register names to bit arrays).
*   **Real-time Collapse:** When a `measure` operation is encountered, the simulator performs a projective measurement, collapses the statevector, and immediately writes the result to the designated classical memory slot.
*   **Branching:** The simulation loop evaluates the `condition` of each operation against the `classical_memory` before applying the corresponding unitary matrix.

## 3. Implementation Details
*   **File:** `src/qvm/ir.py` -> Added `add_classical_register` and `condition` support.
*   **File:** `src/qvm/simulator.py` -> Integrated `classical_memory` and conditional branching in `simulate()`.

## 4. Edge Cases
*   **Mid-circuit Measurement:** The statevector must be correctly normalized after each collapse to ensure subsequent gates remain unitary.
*   **Uninitialized Bits:** Classical bits default to `0` unless written to by a `measure` instruction.

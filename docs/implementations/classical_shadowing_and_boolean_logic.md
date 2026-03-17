# Classical Shadowing and Boolean Logic

**Timestamp:** 2026-03-17T21:20:00Z

## 1. Rationale
OpenQASM 3.0 treats classical computation as a first-class citizen. "Classical Shadowing" refers to the ability to manipulate classical registers using standard boolean logic (AND, OR, XOR, NOT) to compute complex branching conditions or store parity results without additional quantum gates.

## 2. Implementation Strategy

### 2.1. Grammar Expansion
*   **Assignments:** `bit[i] = bit[j] ^ bit[k];`
*   **Expressions:** Support for `&` (AND), `|` (OR), `^` (XOR), and `~` (NOT).

### 2.2. IR Integration
A new operation type `classical_op` will be added to the `QuantumCircuit`.
*   Format: `{"name": "classical_op", "op": "^", "target": (reg, idx), "args": [(reg, idx), (reg, idx)]}`

### 2.3. Simulator Execution
The `Simulator` will evaluate these expressions using Python's bitwise operators and update the `classical_memory` bank during the execution loop.

## 3. Implementation Details
*   **File:** `src/qvm/qasm3.lark` -> Added `assignment` and `boolean_expr` rules.
*   **File:** `src/qvm/ir.py` -> Added support for `classical_op`.
*   **File:** `src/qvm/simulator.py` -> Implemented logic for boolean operations on bit registers.

## 4. Edge Cases
*   **Type Safety:** Ensuring operations are only performed on compatible classical bit types.
*   **Immediate Values:** Supporting assignments from literals (e.g., `c[0] = 1;`).

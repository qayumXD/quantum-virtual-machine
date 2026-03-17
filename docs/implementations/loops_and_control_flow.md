# Loops and Advanced Control Flow

**Timestamp:** 2026-03-17T21:05:00Z

## 1. Rationale
To support repetitive quantum algorithms (like Grover's iterations or Variational Quantum Eigensolvers) and interactive protocols, the QVM must support `for` and `while` loops. This moves the runtime from a simple directed acyclic graph (DAG) of instructions to a full-featured imperative execution model.

## 2. Implementation Strategy

### 2.1. Grammar
*   **For Loops:** `for i in [start:end] { ... }` (Standard OpenQASM 3.0 range syntax).
*   **While Loops:** `while(condition) { ... }` (Classical bit monitoring).

### 2.2. Execution (The Interpreter Pattern)
Since the `Simulator` processes the `QuantumCircuit` IR linearly, loops can be handled in two ways:
1.  **Unrolling (Static):** The parser expands the loop into a long list of instructions in the IR.
2.  **Interpreting (Dynamic):** The `_process_node` walker in the parser handles the repetition by re-visiting AST nodes.

**Decision:** We will use **Dynamic Interpretation** within the `OpenQASM3Parser._process_node` to keep the IR concise and allow for `while` loops that depend on real-time measurement results (which cannot be unrolled statically).

## 3. Implementation Details
*   **File:** `src/qvm/qasm3.lark` -> Added `for_loop`, `while_loop`, and `range` rules.
*   **File:** `src/qvm/qasm3_parser.py` -> Updated `_process_node` to implement loop logic.

## 4. Edge Cases
*   **Infinite Loops:** `while` loops must have a safety timeout or maximum iteration count to prevent the simulator from hanging.
*   **Nested Loops:** The recursive nature of `_process_node` naturally supports nesting.

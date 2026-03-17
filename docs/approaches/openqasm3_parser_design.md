# OpenQASM 3.0 Parser Design & Specification

**Timestamp:** 2026-03-17T19:58:00Z

## 1. Rationale: Choosing Lark over ANTLR4
For the QVM Final Year Project, **Lark** has been selected as the primary parsing engine for OpenQASM 3.0.

*   **Zero-Dependency Build:** Lark is a pure Python library. This aligns with the "lightweight" requirement in the Scope Document, avoiding the need for a Java Runtime Environment (JRE) which ANTLR4 requires for parser generation.
*   **Rapid Iteration:** Lark allows for EBNF grammar definitions directly within the Python source or as a sidecar `.lark` file, facilitating quick changes to the supported subset of OpenQASM 3.0.
*   **Visitor Pattern Compatibility:** Lark's `Transformer` and `Visitor` classes provide a clean, idiomatic way to map abstract syntax tree (AST) nodes directly to the QVM's `QuantumCircuit` and `ClassicalRegister` objects.

## 2. Supported Grammar Subset (Phase 1)
The initial implementation will support:
*   **Header:** `OPENQASM 3.0;`
*   **Declarations:** 
    *   `qubit[size] name;` (Quantum registers)
    *   `bit[size] name;` (Classical registers)
*   **Standard Gates:** Single-qubit (U, local basis) and Two-qubit (CX) gates.
*   **Control Flow:** 
    *   `if (condition) { statement; }`
*   **Measurement:** `target_bit = measure qubit;`

## 3. Implementation Strategy: The Transformer Pattern
The `OpenQASM3Transformer` will walk the AST:
1.  **Declaration Nodes:** Initialize `QuantumCircuit` and track logical-to-physical name mappings.
2.  **Gate Nodes:** Append operations to `QuantumCircuit.operations`.
3.  **Classical Nodes:** Manage a new `ClassicalMemory` state in the `Simulator`.

## 4. Edge Cases & Risks
*   **Recursive Gates:** User-defined gates (`gate name(...) { ... }`) require a recursive expansion in the transformer.
*   **Timing:** `delay` instructions will initially be treated as NOPs in the statevector simulator but recorded in the IR for potential future pulse-level backend integration.

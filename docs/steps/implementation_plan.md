# Quantum Virtual Machine (QVM) — Actionable Implementation Plan

This document captures a concise, actionable implementation plan derived from `docs/ScopeDocumentV1.md` for the QVM project.

## Overview
- Goal: Build a lightweight, educational Python QVM (statevector simulator + transpiler) that supports up to ~10 qubits, IR-based transpilation, SWAP insertion, gate decomposition, visualization, and OpenQASM export.
- Tech: Python 3.10+, NumPy, NetworkX, Matplotlib, pytest.

## Modules & Tasks

1. Quantum Program Parser
- Define a small Python DSL or accept a structured JSON input for circuits.
- Implement a parser that validates gate names, qubit indices, and parameters.
- Output: AST or list of instructions.

2. Intermediate Representation (IR) Engine
- Design IR as either a linear instruction list or DAG (choose DAG if optimizations planned).
- Provide APIs: `from_parser()`, `to_list()`, `to_dag()`.
- Ensure IR carries metadata (gate type, params, logical qubits, original source location).

3. Transpiler (Topology Mapper)
- Implement target architecture description (connectivity graph + native gate set).
- Use `networkx` to model connectivity and compute shortest paths.
- Implement logical->physical mapping and SWAP insertion heuristics (greedy, shortest-path, lookahead).
- APIs: `transpile(ir, target_arch)` returning transformed IR.

4. Gate Decomposer
- Identify non-native gates and decompose into native primitives (e.g., Toffoli -> CNOTs + rotations).
- Provide decomposition registry so new decompositions can be registered.

5. Statevector Simulator Engine
- Represent state as a NumPy complex vector of length 2^n.
- Implement single-qubit and two-qubit gate application routines (using sparseKronecker or direct index-based operations for efficiency).
- Provide execution API: `simulate(ir, n_qubits)` returning final statevector and measurement probabilities.
- Add deterministic measurement routines (exact probabilities) and optional pseudo-random sampling helper.

6. Visualization & Export
- Circuit diagrams: simple ASCII or Matplotlib-based visual showing logical vs physical circuits.
- Probability histograms using Matplotlib.
- Export IR -> OpenQASM 2.0 string for external execution.

## Testing & Validation
- Add unit tests for parser, IR conversions, decompositions, transpiler invariants, and simulator correctness.
- Test cases: Bell state, GHZ, Bernstein-Vazirani, Grover (small n), Teleportation.
- Use `pytest` and include expected statevectors/probabilities for assertions.

## Suggested File Layout
```
docs/           # docs (existing)
src/
  qvm/
    parser.py
    ir.py
    transpiler.py
    decomposer.py
    simulator.py
    visual.py
  examples_bell_state_parser_demo.py
requirements.txt
tests/
  test_parser.py
  test_ir.py
  test_transpiler.py
  test_simulator.py
```

## Quick Implementation Steps (first sprint)
1. Implement minimal parser and IR (accept simple gate list).  
2. Implement statevector simulator for single- and two-qubit gates and verify Bell/GHZ.  
3. Implement simple target architecture (linear chain) and greedy SWAP insertion.  
4. Add gate decomposition registry for a small set (CNOT, H, X, Y, Z, RX, RY, RZ, Toffoli).  
5. Add OpenQASM export and matplotlib probability plotting.  
6. Add tests and basic README usage examples.

## Example CLI / Usage snippets
```
# run example simulator
python -m src.qvm.simulator --circuit examples/bell.json --nqubits 2

# run tests
pytest -q
```

## Next Steps
- Implement parser + IR and the simulator first (Iteration 1).  
- When ready, I can scaffold `src/qvm/*` files and create starter unit tests.

---
Generated from `docs/ScopeDocumentV1.md`.

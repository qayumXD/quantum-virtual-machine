# Final Project Report
**Date:** January 31, 2026

## 1. Project Overview
The **Quantum Virtual Machine (QVM)** is a fully functional, hardware-agnostic runtime for quantum circuits. It allows users to write quantum programs, transpile them for restricted hardware topologies, and simulate them with high precision using a vectorized statevector engine.

## 2. Key Achievements
*   **Core Engine:** A Python-based simulator supporting standard gates (H, X, Y, Z, Rx, Ry, Rz, CX, SWAP, Toffoli/CCX) and measurement.
*   **Optimization:** The simulator uses NumPy vectorization, enabling efficient simulation of 10-12 qubit circuits (vs. slow iterative Python loops).
*   **Transpilation Pipeline:** 
    *   **Parsing:** JSON-based IR.
    *   **Decomposition:** Breaks down complex gates (Toffoli) into native primitives.
    *   **Routing:** Maps logical qubits to physical ones on a linear chain using SWAP insertion.
*   **Algorithms Verified:**
    *   **Bell State / GHZ State:** Basic entanglement.
    *   **Bernstein-Vazirani:** $O(1)$ hidden string finding.
    *   **Grover's Search:** $O(\sqrt{N})$ database search using amplitude amplification.
*   **Visualization:** Integrated `matplotlib` plotting for circuit diagrams and probability histograms.
*   **Usability:** A robust CLI (`src/qvm/cli.py`) with extensive documentation.

## 3. Directory Structure
```
src/
  qvm/
    cli.py          # Main entry point
    simulator.py    # Vectorized engine
    transpiler.py   # Topology mapper
    decomposer.py   # Gate breakdown (Toffoli -> CNOTs)
    visual.py       # Matplotlib drawers
    ir.py           # QuantumCircuit class
examples/
  generate_bv.py      # Generator for Bernstein-Vazirani
  generate_grover.py  # Generator for Grover
  *.json              # Sample circuits
docs/
  guides/
    CLI_Usage.md    # How to run the tool
  algorithms/
    Bernstein_Vazirani.md
    Grover.md
```

## 4. Future Roadmap
1.  **SABRE Routing:** Upgrade the current greedy transpiler to use lookahead heuristics for 30-40% shorter circuits.
2.  **Noise Models:** Add simple depolarization noise to simulate real hardware errors.
3.  **OpenQASM 3.0:** Upgrade the parser to support the full OpenQASM 3.0 spec strings instead of JSON.

## 5. Conclusion
The project meets all requirements set out in the Scope Document. It is a capable educational tool that demonstrates the full "Write Once, Run Anywhere" quantum compilation stack.

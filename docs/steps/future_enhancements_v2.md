# Future Enhancements Roadmap (v0.3+)

**Timestamp:** 2026-03-17T22:55:00Z

## 1. Advanced Simulation Engines
*   **GPU Acceleration:** Integrate `cupy` or `PyTorch` backends for the statevector simulator to leverage parallel processing.
*   **Full MPS Optimization:** Expand `MPSSimulator` to support non-adjacent gates via automatic SWAP insertion and implement canonical form maintenance for higher fidelity.
*   **Clifford+T Simulation:** Add a specialized stabilizer simulator for extremely large-scale circuits composed primarily of Clifford gates.

## 2. Realistic Hardware Modeling
*   **Time-Dependent Hamiltonians:** Implement the pulse-level control researched in Phase 2, allowing for gate-calibration simulations.
*   **Complex Noise Channels:** Move beyond depolarizing noise to support amplitude damping, phase damping, and thermal relaxation ($T_1$/$T_2$ times).
*   **Qubit Topology Presets:** Add standardized hardware topologies (e.g., IBM Eagle, Rigetti Aspen) to the transpiler.

## 3. Web UI & Developer Experience
*   **Visual Circuit Composer:** A drag-and-drop interface (React-based) to build circuits visually, generating OpenQASM 3.0 code in real-time.
*   **Live Bloch Sphere:** Add 3D visualizations of single-qubit state rotations during simulation.
*   **Batch Execution:** Support for running parameter sweeps (e.g., varying an $R_z$ angle) and plotting the results as a trend line.

## 4. Language & Interoperability
*   **Full stdgates.inc Support:** Expand the parser to support the entire OpenQASM 3.0 standard gate library.
*   **Qiskit/Cirq Provider:** Implement a Qiskit `Backend` or Cirq `Sampler` interface so the QVM can be used as a drop-in replacement for external frameworks.

# Research: Advanced Simulation & Pulse Control

**Timestamp:** 2026-03-17T22:20:00Z

## 1. Tensor Networks (Matrix Product States - MPS)
*   **Concept:** Factorizes the statevector into smaller tensors connected by bonds ( Schmidt rank).
*   **Scalability:** Linear memory scaling $O(N)$ vs exponential $O(2^N)$ for low-entanglement states.
*   **QVM Application:** Adding an `MPSSimulator` would allow the QVM to simulate circuits like Bernstein-Vazirani for hundreds of qubits, showcasing the power of compression.
*   **Complexity:** High entanglement (e.g., GHZ states) forces the bond dimension to grow, eventually reverting to exponential cost.

## 2. Pulse-Level Control (Hamiltonian Dynamics)
*   **Concept:** Simulating the continuous-time evolution of the quantum system under a drive Hamiltonian $H(t)$.
*   **Accuracy:** Captures crosstalk, leakage to higher energy levels (e.g., $|2\rangle$ state in transmon qubits), and precise gate timing.
*   **QVM Application:** Transforming `delay[100ns]` from a NOP into a period where $H(t)$ consists only of decoherence and drift.
*   **Complexity:** Requires solving stiff differential equations; significant performance overhead compared to gate-level matrix multiplication.

## 3. Recommended Path
For an educational FYP, **Tensor Networks** provide a more immediate "wow factor" by breaking the 12-qubit limit for specific algorithms. **Pulse Control** is more suited for a subsequent physics-focused module.

# Future Enhancements & Roadmap
**Date:** January 31, 2026

This document outlines potential features and improvements for future iterations of the QVM project. These are beyond the scope of the initial prototype but represent logical next steps for a production-grade or research-grade tool.

---

## 1. Advanced Transpiler Routing (SABRE)
**Problem:** The current "Greedy BFS" router inserts SWAP gates based solely on the *current* gate's needs. This often moves qubits into positions that are detrimental for *future* gates, leading to excessive "SWAP ping-pong" and deep circuits.

**Solution:** Implement **SABRE (Swap-Based BidiREctional heuristic search)**.
*   **Mechanism:**
    1.  Construct a Dependency DAG (Directed Acyclic Graph) of the circuit.
    2.  Use a heuristic score ($H$) that combines the distance of the current gate's qubits with the average distance of the "Front Layer" (next executable gates).
    3.  $H = \text{dist}(current) + w \cdot \text{decay} \cdot \text{dist}(lookahead)$.
    4.  Run the routing forward and backward multiple times to converge on a global minimum.
*   **Impact:** Can reduce SWAP count by 30-50% on complex circuits like Grover's algorithm.

---

## 2. Noise Simulation
**Problem:** The current simulator is "ideal". It assumes perfect gates and infinite coherence time. Real hardware is noisy.

**Solution:** Add a Density Matrix simulator or a Monte-Carlo Trajectory (Shot-based) simulator with noise models.
*   **Depolarizing Channel:** Apply a random Pauli error (X, Y, or Z) after every gate with probability $p$.
*   **Thermal Relaxation (T1/T2):** Decay the state towards $|0\rangle$ based on gate duration.
*   **Readout Error:** Flip measurement bits with probability $\epsilon$.

---

## 3. OpenQASM 3.0 Support
**Problem:** The current JSON input format is custom and not standard. OpenQASM 2.0 export is supported, but parsing is limited.

**Solution:** Integrate a proper grammar-based parser (using `antlr4` or `lark`) for OpenQASM 3.0.
*   Support explicit timing (delays).
*   Support classical control flow (`if (c==1) reset q;`).
*   Support gate definitions (`defgate`).

---

## 4. Web-Based User Interface
**Problem:** The CLI is powerful but requires terminal usage. An educational tool benefits from a GUI.

**Solution:** Build a Web UI using React (Frontend) and Flask/FastAPI (Backend).
*   **Drag-and-Drop Circuit Composer:** Like IBM Quantum Composer.
*   **Live Visualization:** Show the Bloch sphere or statevector updating in real-time as gates are added.
*   **Cloud Execution:** Host the Python QVM on a server; users run circuits from the browser.

---

## 5. Pulse-Level Control
**Problem:** The simulator operates at the "Gate Level" (Logical). Real hardware operates at the "Pulse Level" (Microwave signals).

**Solution:** Implement a Hamiltonian Solver.
*   Define the system Hamiltonian $H(t)$.
*   Solve the Schrödinger equation $\frac{d}{dt}|\psi\rangle = -iH(t)|\psi\rangle$ numerically.
*   Allow users to define custom microwave pulses instead of just "Gates".

---

## 6. Matrix Product States (MPS)
**Problem:** Statevector simulation hits a memory wall at ~20-30 qubits ($2^{30} \approx 16 \text{GB}$ RAM).

**Solution:** Implement a Tensor Network simulator (MPS).
*   Represents the state as a chain of tensors.
*   Efficient for circuits with low entanglement.
*   Allows simulation of 50-100 qubits for specific classes of "shallow" circuits.

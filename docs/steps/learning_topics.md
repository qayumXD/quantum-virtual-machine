# QVM Learning Roadmap — Topics & Resources

This document lists the practical topics, libraries, concepts, and resources you should learn to implement the Quantum Virtual Machine (QVM) described in `docs/ScopeDocumentV1.md` and `docs/steps/implementation_plan.md`.

---

## 1) High-level study plan (recommended order)
- Week 1: Python fundamentals + environment and tooling.
- Week 2: NumPy, linear algebra refresher, complex arithmetic.
- Week 3: Quantum fundamentals (qubits, gates, measurement, entanglement).
- Week 4: Implement a basic statevector simulator and test Bell/GHZ circuits.
- Week 5: Graph theory basics + `networkx` for topology mapping.
- Week 6: Transpiler concepts (IR, DAGs, SWAP insertion heuristics).
- Week 7: Gate decomposition and OpenQASM export.
- Week 8: Visualization, testing, and polishing; prepare demos and documentation.

Adjust pacing based on prior experience. Expect 6–12 weeks for a solid prototype.

---

## 2) Programming & tooling (Python)
- Core Python: syntax, data types, control flow, functions, list/dict comprehensions.
- Intermediate: classes, modules, packages, exceptions, context managers.
- Environment: `venv` or `virtualenv`, `pip`, `requirements.txt`, `pip-tools`.
- Typing: `typing` module basics (type hints) — helpful for maintainability.
- Packaging & entry points: `setuptools`, simple CLI (`argparse` / `click`).
- Testing & CI: `pytest`, test fixtures, basic GitHub Actions for CI.
- Debugging & profiling: `pdb`, `pytest -k`, `cProfile` and `line_profiler` (optional).

Key resources
- Official Python docs: https://docs.python.org/3/
- Real Python tutorials: https://realpython.com/

---

## 3) Scientific & support libraries
- NumPy: arrays, linear algebra, broadcasting, complex arrays. Essential for statevectors and gates.
- SciPy (optional): advanced linear algebra utilities.
- NetworkX: graph representation of hardware topologies, shortest paths, connectivity.
- Matplotlib: plotting histograms and simple circuit visualizations.
- pytest: unit and integration testing framework.
- tqdm (optional): progress bars for longer simulations.

Suggested learning
- NumPy quickstart: https://numpy.org/doc/stable/user/quickstart.html
- NetworkX guide: https://networkx.org/documentation/stable/tutorial.html

---

## 4) Mathematics & CS foundations
- Linear algebra: vectors, matrices, complex conjugate transpose, eigenvalues, unitary matrices, tensor products (Kronecker product).
- Probability and basic statistics: measurement probabilities, normalization.
- Complex numbers and complex arithmetic.
- Graph theory: nodes, edges, shortest paths, heuristics for mapping.
- Algorithms: greedy heuristics, graph search (BFS, Dijkstra), and basics of NP-hard problems (mapping/swapping is hard).

Key resources
- Gilbert Strang's *Linear Algebra* (MIT OCW / textbook) or Khan Academy linear algebra.

---

## 5) Quantum computing fundamentals
- Qubit mathematics: Bloch sphere intuition, statevectors (|0>, |1>, α|0>+β|1>), multi-qubit states.
- Gates: Pauli X/Y/Z, Hadamard, phase, rotation gates (RX/RY/RZ), CNOT, controlled gates, Toffoli.
- Measurement and post-measurement state collapse; measurement probabilities.
- Entanglement (Bell states, GHZ) and tensor product structure.
- Unitary evolution and reversibility.
- Basic noise models and why we ignore them initially.

Textbooks & canonical references
- Nielsen, M. A., & Chuang, I. L., *Quantum Computation and Quantum Information* (recommended).
- Qiskit Textbook: https://qiskit.org/textbook/ (practical & interactive)

---

## 6) Quantum software stack & libraries
- Qiskit (IBM): Terra for circuit representation and transpilation, Aer for simulation. Useful reference implementation.
  - https://qiskit.org/
  - Qiskit Terra source: https://github.com/Qiskit/qiskit-terra
- Cirq (Google): good for noisy-device experiments and topology-aware compilation.
  - https://quantumai.google/cirq
- PennyLane (Xanadu): hybrid quantum-classical, useful for circuit transformations.
  - https://pennylane.ai/
- ProjectQ and pyQuil (Rigetti): historic references for compilation ideas.
- OpenQASM: assembly format to export circuits (OpenQASM 2.0/3.0 docs).

Why study these
- Learn how production toolkits represent circuits, perform transpilation, and decompose gates; reuse ideas rather than reinventing everything.

---

## 7) Compiler & transpiler concepts
- Intermediate Representation (IR): instruction lists vs. DAGs, metadata, scheduling.
- Gate decomposition & synthesis: breaking complex gates into native gates.
- Qubit mapping / routing: logical -> physical mapping and SWAP insertion.
- Optimizations: gate cancellation, commutation, depth minimization.
- Heuristics: greedy mapping, lookahead, A* approaches for minimizing added gates.

Reading & references
- Qiskit transpiler docs and source (see `transpiler` module in Qiskit Terra).
- Academic papers on qubit mapping / routing (search arXiv for "qubit mapping" or "quantum circuit routing").

---

## 8) Simulator engineering
- Statevector simulation: representing a 2^n complex vector, gate application via tensor products or index-based updates.
- Performance considerations: avoid full Kronecker products when possible; apply operations by reshaping and tensordot or index math.
- Memory limits: 2^n complex numbers — plan for n ≤ 10–12 for local experiments.
- Testing: verify with analytic results for small circuits.

Practical reading
- Blog posts and notebooks implementing statevector simulators (search for "writing a quantum simulator numpy").

---

## 9) Visualization & UX
- Circuit diagrams: simple text or Matplotlib renderings; study how Qiskit draws circuits.
- Probability histograms: Matplotlib bar charts showing basis-state probabilities.
- Transpilation views: side-by-side logical vs physical circuits highlighting inserted SWAPs.

---

## 10) Software engineering & project practices
- Modular design: separate `parser`, `ir`, `transpiler`, `decomposer`, `simulator`, and `visual` modules.
- Tests: unit tests for mathematical correctness, property tests for preservation of unitary behavior.
- Documentation: usage examples, minimal README, and a couple of Jupyter notebooks as demos.
- Version control: frequent commits with small changes; descriptive messages.

---

## 11) Concrete learning resources (books, courses, platforms)
- Books
  - Nielsen & Chuang — *Quantum Computation and Quantum Information* (foundational).
  - Michael A. Nielsen, *Quantum Computation and Quantum Information* (same canonical reference).
  - "Quantum Computing for Computer Scientists" — useful intro for CS perspective.

- Online textbooks & tutorials
  - Qiskit Textbook: https://qiskit.org/textbook/
  - Cirq documentation & tutorials: https://quantumai.google/learn
  - Microsoft Quantum docs (Q#): https://learn.microsoft.com/quantum/

- Research platforms & organizations
  - IBM Quantum / IBM Research — OpenQiskit, cloud backends, tutorials: https://quantum-computing.ibm.com/
  - Google Quantum AI & Cirq — papers and software: https://quantumai.google/
  - Microsoft Quantum & Microsoft Research — Q# language and research: https://www.microsoft.com/quantum
  - Rigetti Computing / Forest (pyQuil): https://www.rigetti.com/
  - Xanadu / PennyLane — quantum ML and hybrid tools: https://pennylane.ai/
  - arXiv.org — search for recent papers on transpilation, routing, and decomposition.

- Courses
  - IBM Qiskit courses and community tutorials.
  - Coursera / edX quantum computing courses (various universities).
  - MIT OCW lectures on quantum computation.

---

## 12) Example projects & repositories to study
- Qiskit Terra (transpiler implementation): https://github.com/Qiskit/qiskit-terra
- Cirq (Google): https://github.com/quantumlib/Cirq
- Pennylane examples: https://github.com/PennyLaneAI/pennylane
- ProjectQ: https://github.com/ProjectQ-Framework/ProjectQ

---

## 13) Practice exercises (progressive)
- Implement a 1-qubit and 2-qubit statevector simulator and verify H and CNOT behaviors.
- Implement Bell state and GHZ circuits, check probabilities.
- Implement a parser that reads a simple JSON/YAML circuit and outputs an IR list.
- Implement a linear-chain topology mapper and greedy SWAP insertion.
- Decompose a Toffoli into CNOT + single qubit rotations and verify equivalence.
- Export a small circuit to OpenQASM and validate it against Qiskit parsing.

---

## 14) Estimated timeline & milestones
- Prototype (basic simulator + examples): 2–3 weeks.
- Add IR + simple transpiler (linear topology): 2–3 weeks.
- Gate decomposition + OpenQASM export + tests: 1–2 weeks.
- Visualization, documentation, polishing: 1–2 weeks.

---

## 15) Next steps I can do for you
- Scaffold `src/qvm/` modules with starter code and tests.
- Create example notebooks (Bell, GHZ, teleportation) and CI for `pytest`.

---

Generated to support `docs/ScopeDocumentV1.md` and the implementation plan.

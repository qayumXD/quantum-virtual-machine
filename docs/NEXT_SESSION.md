# Session Handoff: QVM Project Context
**Last Updated:** January 31, 2026

## 1. Project Status: ✅ STABLE / COMPLETE (Prototype)
The Quantum Virtual Machine (QVM) is currently in a stable, verified state. It functions as a standalone CLI tool for parsing, transpiling, simulating, and visualizing quantum circuits.

## 2. Recent Major Changes
*   **Vectorized Simulator:** Replaced Python loops with NumPy vectorization (`src/qvm/simulator.py`). It is fast for $N \le 12$ qubits.
*   **CLI Integration:** `src/qvm/cli.py` is the main entry point. It automatically uses the `Decomposer` to handle complex gates (like Toffoli) before simulation.
*   **Algorithm Verification:** Generators for **Bernstein-Vazirani** and **Grover's Search** were added to `examples/` and verified to work correctly with the pipeline.
*   **Documentation:** A full suite of technical reference docs was created in `docs/technical_reference/`.

## 3. Key Locations
*   **Source:** `src/qvm/`
*   **Tests:** `tests/` (Run with `python -m pytest`)
*   **Examples:** `examples/` (Run generators with `python examples/generate_*.py`)
*   **Docs:** `docs/` (See `docs/technical_reference/01_project_structure.md` for a file map).

## 4. Immediate Action Items (None)
There are no broken builds or failing tests. The project is ready for use.

## 5. Roadmap for Next Session
If you are picking this up to add new features, please consult **`docs/steps/future_enhancements.md`**.
Top priorities for expansion are:
1.  **SABRE Routing:** The current transpiler is greedy and suboptimal.
2.  **Noise Models:** The current simulator is noiseless.
3.  **Web UI:** Moving beyond the CLI.

## 6. How to Run
```bash
# Run a test
python -m pytest

# Run a simulation
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

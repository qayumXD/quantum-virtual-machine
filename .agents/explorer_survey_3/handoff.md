# Handoff Report — QVM Runtime Architecture, CLI, & Test Infrastructure Survey

**Agent**: Explorer Survey 3 (Runtime Architecture, CLI, & Test Infrastructure)  
**Date**: 2026-08-23  
**Working Directory**: `/home/qayum/projects/quantum-virtual-machine/.agents/explorer_survey_3`  
**Target Recipient**: Project Orchestrator (`026dea8e-7666-439e-b67e-20e5230e0ec7`)

---

## 1. Observation

### 1.1 CLI & Server Entry Points
- **`src/qvm/cli.py:16–38`**: CLI uses `argparse.ArgumentParser`. Flags supported: `input_file`, `--nqubits`, `--transpile`, `--routing` (`greedy`/`sabre`), `--no-restore-mapping`, `--visualize`, `--shots`, `--seed`, `--noise-depol`, `--noise-amp-damp`, `--noise-phase-damp`, `--device` (`fake_5q`/`fake_7q`/`ideal`), `--expectation`.
- **`src/qvm/cli.py:93`**: Hardcodes statevector simulation (`sim = Simulator()`). No `--engine` flag exists to select `MPSSimulator`, even though `api/app.py:48` supports `engine: Literal["statevector", "mps"]`.
- **`src/qvm/cli.py:101–112, 147–150`**: Output is printed directly to `stdout` as unstructured text (`"|{bin_str}>: {prob:.4f}"`, `"|{bitstring}>: {count}"`). There are no `--json`, `--output`, `--quiet`, `--verbose`, or `--benchmark` flags.
- **`src/qvm/cli.py:64, 75, 87, 98`**: Catches generic `Exception as e`, prints `"Error reading/parsing input file: {e}"`, and invokes `sys.exit(1)` with no distinct exit status codes or debug tracebacks.

### 1.2 Runtime Simulation & Scaling Bottlenecks
- **`src/qvm/simulator.py:160–166`**:
  ```python
  def _apply_single_qubit_gate(self, state, gate, target, n):
      op_list = [self.I] * n
      op_list[n - 1 - target] = gate
      full_op = op_list[0]
      for i in range(1, n):
          full_op = np.kron(full_op, op_list[i])
      return full_op @ state
  ```
  `_apply_single_qubit_gate` constructs a full $2^N \times 2^N$ matrix for every single-qubit gate via $N-1$ Kronecker products. For $N=10$, this allocates a $1024 \times 1024$ (16 MB) matrix per gate; for $N=15$, a $32768 \times 32768$ (16 GB) matrix; for $N \ge 16$, it triggers an immediate `MemoryError` or process OOM crash.
- **`src/qvm/simulator.py:45, 62–64, 376–380`**: Hardcoded `max_ops = 10000`. In `_simulate_with_noise`, `max_ops = 10000` is hardcoded. Circuits with $>10,000$ operations unconditionally raise `RuntimeError("Exceeded maximum operations limit (10000).")`.
- **`src/qvm/noise.py:112–120`**: `NoiseChannel._embed_operator` for 2-qubit channels executes a nested loop `for i in range(dim): for j in range(dim):` where $\text{dim} = 2^N$. For $N=12$, this is $4^{12} = 16,777,216$ iterations in pure Python; for $N=14$, $268,435,456$ iterations.
- **`src/qvm/visual.py:84`**: `plot_circuit` sets `figsize=(max(8, depth), max(4, num_qubits * 0.5))`. A circuit with $\text{depth} \ge 1000$ creates a 1000-inch wide Matplotlib figure, crashing with Matplotlib pixel limit errors or memory exhaustion.
- **`src/qvm/mps_simulator.py:194, 197–200, 206–218`**: `get_statevector()` and `sample()` reconstruct the full $2^N$ dense statevector on every call, defeating the purpose of MPS compression during sampling.

### 1.3 Parser Scalability & Grammar Limitations
- **`src/qvm/qasm3.lark:25, 47–48`**: `qubit: CNAME "[" INT "]"` requires an `INT` literal. In `for_loop: "for" CNAME "in" range "{" program "}"`, loop variables cannot be used as qubit indices (e.g. `for i in [0:3] { h q[i]; }` fails grammar parsing).
- **`src/qvm/qasm3_parser.py:19, 26, 29`**: `OpenQASM3Parser.parse()` performs full LALR parse tree generation followed by two full recursive AST traversals (`_find_declarations` and `_process_node`).
- **`src/qvm/parser.py:47–98`**: `OpenQASM2Parser` ignores `creg` declarations, does not store measurement targets, and only parses single literal float parameters (`float(param_str.rstrip(")"))`), failing on expressions like `pi/2`.

### 1.4 Test Suite Status & Infrastructure
- **Test execution command**: `.venv/bin/pytest` collected 114 test items, 114 passed, 1 skipped in 7.00s.
- **System python command**: `python3 -m pytest` collected 119 test items: 115 passed, 4 failed (failures in `test_api.py:86` due to missing `web/out` directory, and `test_backend_cross_conversion.py`, `test_qiskit_integration.py` due to missing `qiskit-aer` causing `qiskit` to be set to `None` in `src/qvm/ir.py:13–23`).
- **Test inventory**: 18 test files in `tests/`, plus 1 misplaced test file in `src/tests_test_parser.py`.
- **Zero test fixtures file**: No `tests/conftest.py` exists in the repository. Local `@pytest.fixture def sample_circuit()` is duplicated across 4 test files (`test_backend_cross_conversion.py:16`, `test_cirq_integration.py:11`, `test_json_serialization.py:7`, `test_qiskit_integration.py:11`).
- **Zero stress or performance tests**: Max circuit size tested across all 119 tests is $N=5$, $\text{gates} \le 15$. There are no stress, benchmark, or memory profiling tests.

### 1.5 Error Handling & Logging
- **Zero custom exceptions**: No custom exception classes (e.g., `QVMError`, `QVMParseError`, `QVMRuntimeError`) exist anywhere in `src/qvm/`. All errors raise standard built-in `ValueError`, `RuntimeError`, `TypeError`, or `ZeroDivisionError`.
- **Zero standard logging**: `import logging` is not used in `src/`. Debug information is emitted via raw `print()` statements (`simulator.py:134`, `export.py:63`, `api/app.py:241`).

---

## 2. Logic Chain

1. **Premise**: Standard production compilers and runtimes (e.g. Python, Node.js, GCC) require deterministic CLI UX (structured output flags, non-zero granular exit codes, telemetry), robust error categorization, predictable resource scaling, and automated stress testing suites.
2. **Observation $\to$ Inference on CLI**: `src/qvm/cli.py` prints string-formatted output to stdout, lacks `--json` / `--quiet` / `--engine` flags, and exits with generic code 1 on all exceptions (Observations in 1.1). Therefore, QVM cannot currently be used reliably as a standard automated CLI compiler/runtime in headless CI/CD or scripting pipelines without wrappers.
3. **Observation $\to$ Inference on Simulation Scalability**: `_apply_single_qubit_gate` computes dense $2^N \times 2^N$ Kronecker products (Observation in 1.2). For a 1000-gate circuit on 10 qubits, this allocates and computes 1000 dense matrix multiplications ($16\text{ GB}$ intermediate allocations). On 16 qubits, it crashes immediately. Therefore, executing 1000+ gate circuits on $\ge 15$ qubits is physically impossible under the current implementation.
4. **Observation $\to$ Inference on Noise Scalability**: The $O(4^N)$ loop in `noise.py:112–120` locks CPU execution when evaluating 2-qubit noise channels on $N \ge 12$.
5. **Observation $\to$ Inference on Visualization**: `plot_circuit` scaling by depth ($1000$ inches for 1000 gates) guarantees a Matplotlib crash or memory exhaustion if invoked on stress-test circuits.
6. **Observation $\to$ Inference on Test Infrastructure**: The existing 119 unit tests only cover microscopic circuits ($N \le 5$, $\text{ops} \le 15$) and lack a unified fixture structure (`conftest.py`). There are no performance regression guards or stress tests (Observation in 1.4).
7. **Deduction for Stress Test Suite**: Developing `tests/test_stress.py` requires generating synthetic circuits with 1000+ operations across four distinct patterns (Deep 1D rotation chains, Scaled QFT, Variational Hardware-Efficient Ansatz, and OpenQASM 3.0 multi-statement streams) with execution timing and memory profiling hooks to systematically expose and verify the resolution of these bottlenecks.

---

## 3. Caveats

1. **Hardware Architecture Assumptions**: The transpiler analysis focused on the `LinearArchitecture` provided by `get_linear_architecture(N)`. Highly connected topologies (e.g. `get_fully_connected_architecture`) will exhibit fewer SWAP insertions but will still encounter simulator Kronecker product bottlenecks.
2. **MPS Entanglement Limits**: While `MPSSimulator` scales efficiently for 1D low-entanglement circuits, deep circuits with extensive two-qubit entangling gates will suffer truncation error if `max_bond_dim` is small ($16$), or slow SVD execution if bond dimension grows.
3. **Frontend Build Dependency**: `test_static_client_served` failure in `test_api.py` is caused by the absence of a pre-built static directory `web/out/` rather than backend Python logic errors.

---

## 4. Conclusion

The Quantum Virtual Machine (QVM) has a functional foundational feature set (QASM 2/3 parsing, basic transpilation, noise modeling, VQA optimization), but exhibits **five critical architectural bottlenecks** preventing it from serving as a production-grade compiler/runtime for 1000+ operation quantum programs:

1. **Dense Kronecker Unitary Application**: $O(4^N)$ matrix allocation in `Simulator._apply_single_qubit_gate` causing severe performance degradation and OOM on $>14$ qubits.
2. **Hardcoded Execution Ceilings**: `max_ops = 10000` limit crashing linear programs and loops exceeding 10,000 operations.
3. **Unstructured CLI & Absence of Domain Exceptions**: Lack of structured JSON output, telemetry flags, engine selector (`--engine mps`), and domain exception hierarchy (`QVMError`).
4. **MPS Full-Vector Contraction Bottleneck**: `sample()` and `get_statevector()` reconstructing $2^N$ dense vectors during sampling.
5. **Absence of Stress & Performance Test Infrastructure**: No `conftest.py`, no scale tests, and no automated stress suite (`tests/test_stress.py`).

---

## 5. Verification Method

### 5.1 Test Suite Verification Commands
To reproduce the baseline test suite execution:
```bash
# 1. Run all tests in the project virtual environment
.venv/bin/pytest -v

# 2. Run test_v03 suite specifically
.venv/bin/pytest tests/test_v03.py -v

# 3. Inspect existing test coverage count
.venv/bin/pytest --collect-only
```

### 5.2 Bottleneck Verification Scripts
To verify the dense Kronecker memory bottleneck in `src/qvm/simulator.py`:
```python
# Run via: .venv/bin/python3 -c "..."
from src.qvm.ir import QuantumCircuit
from src.qvm.simulator import Simulator
import time

qc = QuantumCircuit(14)
for _ in range(100):
    qc.add_operation("h", [0])

sim = Simulator()
t0 = time.perf_counter()
sim.simulate(qc)
print(f"100 H gates on 14 qubits took {time.perf_counter() - t0:.3f}s")
```

### 5.3 Files to Inspect
- Detailed analysis: `/home/qayum/projects/quantum-virtual-machine/.agents/explorer_survey_3/analysis.md`
- CLI Entry Point: `/home/qayum/projects/quantum-virtual-machine/src/qvm/cli.py`
- Simulation Engine: `/home/qayum/projects/quantum-virtual-machine/src/qvm/simulator.py`
- Noise Channel Embedding: `/home/qayum/projects/quantum-virtual-machine/src/qvm/noise.py`
- QASM 3.0 Parser & Grammar: `/home/qayum/projects/quantum-virtual-machine/src/qvm/qasm3_parser.py`, `src/qvm/qasm3.lark`
- Existing Test Files: `/home/qayum/projects/quantum-virtual-machine/tests/`

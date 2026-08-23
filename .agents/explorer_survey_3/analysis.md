# Comprehensive Survey: QVM Runtime Architecture, CLI, & Test Infrastructure

**Surveyor**: Teamwork Explorer (Survey Specialist 3)  
**Date**: 2026-08-23  
**Working Directory**: `/home/qayum/projects/quantum-virtual-machine/.agents/explorer_survey_3`  
**Repository**: `/home/qayum/projects/quantum-virtual-machine`

---

## Executive Summary

This report delivers an exhaustive architectural investigation of the Quantum Virtual Machine (QVM) codebase, focusing on **CLI entry points and runtime harness**, **existing test suite structure and coverage**, **error handling and panic safety**, **benchmarking and telemetry hooks**, and **architectural design requirements for an automated stress testing suite (`tests/test_stress.py`) capable of handling 1000+ operation circuits**.

### Core Findings Matrix
| Subsystem | Current State | Critical Vulnerabilities / Bottlenecks | Production Readiness Gap |
| :--- | :--- | :--- | :--- |
| **CLI & Harness** (`src/qvm/cli.py`) | Basic `argparse` script supporting QASM/JSON, linear transpilation, noise, sampling, expectation values. | Hardcoded statevector engine only (no `--engine mps`), no structured `--json` output, no timing/telemetry flags, unhandled exit codes. | High: lacks compiler/runtime standard CLI UX (flags, exit codes, JSON mode, telemetry). |
| **Parser Scalability** (`src/qvm/qasm3_parser.py`) | Lark LALR parser for QASM 3.0, custom string parser for QASM 2.0. | AST traversal (`_find_declarations`, `_process_node`) walks full tree recursively; QASM 3 loop variables cannot bind to qubit indices; QASM 2 ignores `creg` and lacks expression math. | Medium-High: Lark tree traversal overhead on 1000+ line circuits; syntax error diagnostics lack line numbers. |
| **Simulation Runtime** (`src/qvm/simulator.py`) | Dense statevector with PC loop, classical memory, projective measurement collapse. | **CRITICAL**: `_apply_single_qubit_gate` builds dense $2^N \times 2^N$ matrix via `np.kron` on every single-qubit gate ($O(4^N)$ memory/time). Hardcoded `max_ops = 10000`. | Critical: 1000-gate circuits on $>14$ qubits cause severe memory allocation stalls or Out-Of-Memory (OOM) crashes. |
| **MPS Simulator** (`src/qvm/mps_simulator.py`) | 1D tensor chain with SVD truncation. | Nearest-neighbor two-qubit gates only; `sample()` and `get_statevector()` reconstruct full $2^N$ dense vector on every shot. | High: defeats tensor network compression during sampling. |
| **Transpiler** (`src/qvm/transpiler.py`) | Greedy BFS & SABRE routing with swap-back identity restoration. | Greedy swap routing inserts $2 \times \text{distance}$ SWAPs per disconnected gate; SABRE `enqueue_ready` scans linear slice. Circuit depth blows up exponentially on distant gates. | Medium-High: transpiling 1000+ gates on linear chain can generate $>30,000$ operations. |
| **Visualization** (`src/qvm/visual.py`) | Matplotlib grid plotting for circuits & histograms. | `plot_circuit` allocates `figsize=(max(8, depth), max(4, num_qubits * 0.5))`; depth $\ge 1000$ crashes Matplotlib with pixel dimension limits. | High: must be bypassed or chunked for large-scale circuits. |
| **Test Suite** (`tests/`) | 18 test files, 119 collected test items covering gates, parsing, loops, v0.3 features. | Zero stress tests, zero scale benchmarks, zero performance regression tests, no `conftest.py`, 1 misplaced test in `src/`. | High: test suite only tests circuits with $N \le 5$ and $\text{ops} \le 20$. |
| **Error Handling & Logging** | Generic standard exceptions (`ValueError`, `RuntimeError`, `TypeError`). | Zero custom exception hierarchy (`QVMError`), zero `logging` module usage, debug `print()` statements in production code. | High: runtime crashes cannot be programmatically categorized. |

---

## 1. CLI Entry Points, Input Parsing, Runtime Configuration, & Execution Harness

### 1.1 CLI Entry Points & Module Structure
The primary CLI entry points in the repository are:
1. **`src/qvm/cli.py` (Lines 16–180)**: Main command-line interface for local circuit execution, transpilation, noise simulation, and visualization. Invocation: `python -m src.qvm.cli <input_file> [flags]`.
2. **`src/qvm/server.py` (Lines 1–24)**: CLI wrapper to start the FastAPI Uvicorn server (`python -m src.qvm.server --host 127.0.0.1 --port 8000`).
3. **`api/app.py` (Lines 1–327)**: FastAPI HTTP API providing programmatic REST endpoints (`/run`, `/health`, `/circuits`, `/history`).
4. **Standalone Demo Scripts**:
   - `bell_state.py`, `ghz_state.py`, `superposition.py`
   - `src/examples_bell_state_parser_demo.py` (Lines 1–145): Uses legacy IR in `src/ir.py`.
   - `src/examples/full_pipeline.py` (Lines 1–72).

### 1.2 Input Argument Parsing & Configuration
`src/qvm/cli.py` uses standard Python `argparse.ArgumentParser` (Lines 17–38):
- **Positional**: `input_file` (Path to JSON or QASM file).
- **Qubit count**: `--nqubits` (`int`, optional for QASM, required for JSON).
- **Transpilation**:
  - `--transpile` (`action="store_true"`): Enables linear topology routing.
  - `--routing` (`choices=["greedy", "sabre"]`, default: `"greedy"`).
  - `--no-restore-mapping` (`dest="restore_mapping"`, `action="store_false"`): Disables reverse SWAPs.
- **Sampling & Seed**:
  - `--shots` (`int`, default: `0`): Number of stochastic measurement shots. If 0, computes exact statevector probabilities.
  - `--seed` (`int`, default: `None`): RNG seed for reproducible execution.
- **Noise Model Configuration**:
  - `--noise-depol` (`float`, default: `0.0`): Depolarizing noise probability $[0, 1]$.
  - `--noise-amp-damp` (`float`, default: `0.0`): Amplitude damping (T1) $\gamma \in [0, 1]$.
  - `--noise-phase-damp` (`float`, default: `0.0`): Phase damping (T2) $\gamma \in [0, 1]$.
  - `--device` (`choices=["fake_5q", "fake_7q", "ideal"]`, default: `None`): Preset noise profile.
- **Expectation Value**:
  - `--expectation` (`str`, default: `None`): Pauli string (e.g. `'ZZ'` or `'ZZ:-1.0,XI:0.5'`).
- **Visualization**:
  - `--visualize` (`action="store_true"`): Invokes Matplotlib plots.

### 1.3 Execution Harness Flow
The execution flow in `src/qvm/cli.py:40-177` follows an 8-stage pipeline:
```
1. Load Circuit File (QASM 2/3 or JSON)
   ├── Check extension .qasm -> inspect "OPENQASM 3.0" -> OpenQASM3Parser / OpenQASM2Parser
   └── Else -> json.load -> QASMParser.parse(circuit_data, nqubits)
2. Gate Decomposition
   └── Decomposer(native_gates).decompose_circuit(qc)
3. Architecture Transpilation (Optional)
   └── If --transpile: Transpiler(linear_arch, routing, restore_mapping).transpile(qc)
4. Statevector Simulation
   └── Simulator().simulate(qc, seed) -> state, classical_memory -> probs = |state|^2
5. Noise Model Construction (Optional)
   └── DeviceBackend or NoiseModel(depol, amp_damp, phase_damp)
6. Shot-Based Measurement Sampling (Optional)
   └── If --shots > 0: Simulator.sample(qc, shots, seed, noise_model)
7. Expectation Value Calculation (Optional)
   └── If --expectation: Hamiltonian.from_dict -> Simulator.expectation_value(qc, obs)
8. Visualizations (Optional)
   └── If --visualize: plot_circuit(qc), plot_histogram(probs), plt.show()
```

### 1.4 Critical Deficiencies in Current CLI Architecture
1. **No Engine Selector**: `cli.py` strictly instantiates `Simulator()` (dense statevector) at line 93. There is no `--engine` parameter to select `MPSSimulator`, preventing users from simulating larger circuits ($N > 25$) that MPS can handle. (Note: `api/app.py:48` supports `engine: Literal["statevector", "mps"]`, but CLI does not).
2. **Missing Structured Output Modes**: No `--json` or `--output <file>` flag. Outputs are formatted strings printed directly to `stdout`. Automations, shell scripts, and CI runners cannot parse structured results without regex scraping.
3. **No Execution Timing or Telemetry**: The CLI does not report execution time, parsing time, transpilation time, or memory usage.
4. **Poor Error Handling & Exit Codes**: Lines 64, 75, 87, 98 catch generic `Exception as e`, print an unstructured message to `stdout`, and call `sys.exit(1)`. No distinction exists between exit codes (e.g. 1 for parse error, 2 for validation error, 3 for OOM/runtime limit).
5. **No Quiet / Verbose Modes**: Informational prints (`"Detected OpenQASM 3.0..."`, `"Simulating..."`, `"Simulation complete."`) cannot be silenced (`-q` / `--quiet`) or set to debug (`-v` / `--verbose`).

---

## 2. Existing Test Suite Analysis

### 2.1 Test Directory Structure & Inventory
The repository contains 18 test files in `tests/` and 1 misplaced test file in `src/`:

| Test File | Lines | Test Count | Focus Area |
| :--- | :--- | :--- | :--- |
| `tests/test_simulator.py` | 166 | 14 | Statevector simulation of H, X, RY, Bell, GHZ; sampling; noise channels; measurement collapse. |
| `tests/test_v03.py` | 480 | 58 | Parameter, ParameterExpression, PauliOp, Hamiltonian, NoiseChannel, NoiseModel, DeviceBackend, Gradients, VQE, QAOA. |
| `tests/test_transpiler.py` | 145 | 5 | Linear routing (Greedy vs Sabre), SWAP counting, identity mapping restoration. |
| `tests/test_decomposer.py` | 65 | 4 | CCX / Toffoli decomposition, preservation of conditions and classical registers. |
| `tests/test_ir.py` | 72 | 3 | `QuantumCircuit` operations, parameters, registers, parameter binding. |
| `tests/test_qasm3_extended.py` | 62 | 4 | OpenQASM 3.0 bitwise operations, assignments, conditionals. |
| `tests/test_qasm3_loops.py` | 54 | 3 | OpenQASM 3.0 for loops and while loops with labels/jumps. |
| `tests/test_qasm3_shadow.py` | 36 | 2 | OpenQASM 3.0 classical shadow randomized Pauli measurements. |
| `tests/test_qasm_parser.py` | 31 | 3 | OpenQASM 2.0 parser (header, registers, gates). |
| `tests/test_qasm_roundtrip.py` | 27 | 1 | QASM 2 to IR to QASM 2 serialization roundtrip. |
| `tests/test_parser.py` | 52 | 3 | `QASMParser` (JSON gate list dictionary parsing). |
| `tests/test_json_serialization.py` | 22 | 1 | `to_json` and `from_json` roundtrip serialization. |
| `tests/test_cirq_parser.py` | 42 | 3 | Cirq circuit to QVM IR conversion. |
| `tests/test_cirq_integration.py` | 30 | 1 | Cirq execution and simulation verification. |
| `tests/test_qiskit_integration.py` | 32 | 1 | Qiskit circuit conversion and Aer simulation. |
| `tests/test_backend_cross_conversion.py`| 45 | 2 | Bidirectional Qiskit $\leftrightarrow$ Cirq conversion. |
| `tests/test_visual.py` | 50 | 4 | Matplotlib plot generation for histograms and circuits. |
| `tests/test_api.py` | 88 | 5 | FastAPI endpoint testing (`/health`, `/run`, `/web/index.html`). |
| `src/tests_test_parser.py` | 126 | 6 | *(Misplaced in `src/`)* Tests legacy `QiskitParser` in `src/parser.py`. |

### 2.2 Fixture Architecture & Test Configuration
- **No `conftest.py`**: The test suite completely lacks a global `conftest.py` root fixture file.
- **Ad-hoc Local Fixtures**:
  - `tests/test_backend_cross_conversion.py:16`: `@pytest.fixture def sample_circuit()`
  - `tests/test_cirq_integration.py:11`: `@pytest.fixture def sample_circuit()`
  - `tests/test_json_serialization.py:7`: `@pytest.fixture def sample_circuit()`
  - `tests/test_qiskit_integration.py:11`: `@pytest.fixture def sample_circuit()`
- **Import Fragility**:
  - `tests/test_v03.py:15` uses `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))` to resolve imports.
  - Other tests use `from src.qvm...` assuming the repository root is on `PYTHONPATH`.

### 2.3 Test Suite Execution & Flaky / Failing Tests
Running pytest across Python environments reveals two key dependency and packaging issues:
1. **System Python Environment (Python 3.14)**:
   - `test_static_client_served` (`tests/test_api.py:86`): Fails with `assert 404 == 200`. The API mounts `/web` conditionally only if `web/out` exists (`api/app.py:93-94`). In standard repository checkouts without a static frontend build, `web/out` is absent.
   - `test_qiskit_to_cirq_conversion`, `test_cirq_to_qiskit_conversion`, `test_qiskit_conversion_and_simulation`: Fail with `ImportError: Qiskit is not installed` or `assert None is not None`. This occurs because `src/qvm/ir.py:13-23` bundles `import qiskit` and `from qiskit_aer import AerSimulator` into a single `try` block. When `qiskit-aer` is missing, `qiskit` is set to `None`, even though `qiskit` core is installed.
2. **Virtual Environment (`.venv`)**:
   - `tests/test_api.py` is skipped entirely because `dotenv` (`python-dotenv`) is not installed in `.venv`, triggering `pytest.skip` at `test_api.py:9`.
   - Remaining 114 tests pass in 7.00s.

### 2.4 Coverage Gaps in Existing Tests
- **Scale & Stress Gap**: Max qubits tested is 5 (`fake_5q`). Max gate count in any test is $\sim 15$ operations. There are **zero tests** evaluating circuits with $> 20$ gates or $> 5$ qubits.
- **Resource Limit Gap**: No tests check behavior when `max_ops = 10000` is approached or exceeded.
- **MPS Scaling Gap**: No tests compare MPS vs Statevector on deep or scalable circuits to verify bond dimension truncation accuracy.
- **Syntax Error Diagnostics Gap**: No negative test cases verifying line/column error reporting on malformed QASM 3.0 syntax.

---

## 3. Error Handling, Exception Hierarchy, Panic Safety, & Logging

### 3.1 Exception Hierarchy Analysis
**Observation**: There is not a single custom exception defined in `src/qvm/`.
Every error is raised using generic Python built-ins:
- `ValueError`: Raised 45+ times for invalid qubit indices, unsupported gate names, invalid register declarations, out-of-bounds parameter values, disconnected architectures, or mismatched parameter counts.
- `RuntimeError`: Raised for disconnected routing paths (`transpiler.py:57, 125`), exceeding `max_ops` limit (`simulator.py:63, 379`), or missing external packages (`ir.py:309, 389`).
- `TypeError`: Raised in `parameter.py:208` and `visual.py:78`.
- `ZeroDivisionError`: Raised in `parameter.py:168`.
- `ImportError`: Raised in `ir.py:281, 350`.

**Impact**: Callers, API wrappers, and automated harnesses cannot catch domain-specific errors (e.g. distinguishing a `QVMParseError` from a `QVMResourceLimitError` or `QVMTopologyError`).

### 3.2 Panic Safety & Failure Modes in Scaled Execution
Detailed inspection of the simulation and transpilation engines reveals severe panic safety and resource exhaustion vulnerabilities when scaling to large circuits:

#### 1. Dense Kronecker Matrix Construction in Statevector Simulator (`src/qvm/simulator.py:160–166`)
```python
def _apply_single_qubit_gate(self, state, gate, target, n):
    op_list = [self.I] * n
    op_list[n - 1 - target] = gate
    full_op = op_list[0]
    for i in range(1, n):
        full_op = np.kron(full_op, op_list[i])
    return full_op @ state
```
- **Mechanism**: For every single-qubit gate, the simulator constructs the full $2^N \times 2^N$ dense matrix `full_op` via $N-1$ Kronecker products, then multiplies it against `state`.
- **Scaling Complexity**:
  - $N = 10$: $1024 \times 1024 = 1,048,576$ elements $= 16\text{ MB}$ per gate. For 1000 gates $= 16\text{ GB}$ of intermediate allocations.
  - $N = 15$: $32768 \times 32768 = 1,073,741,824$ elements $= 16\text{ GB}$ matrix per gate.
  - $N \ge 16$: Python raises `MemoryError` or triggers the OS OOM killer.
- **Remedy**: Single-qubit gates must be applied via tensor reshaping (`state.reshape([2]*n)`) or index bit-twiddling, operating in $O(2^N)$ memory and time without constructing dense $2^N \times 2^N$ operators.

#### 2. Hardcoded Loop Ceiling (`src/qvm/simulator.py:45, 62–64, 376–380`)
- `simulate()` defaults `max_ops: int = 10000`.
- In `_simulate_with_noise()`, `max_ops = 10000` is hardcoded.
- Executing a linear circuit with 10,001 gates or a while-loop iterating past 10,000 operations crashes unconditionally with `RuntimeError: Exceeded maximum operations limit (10000).`

#### 3. $O(4^N)$ Python Double Loop in 2-Qubit Noise Channels (`src/qvm/noise.py:106–126`)
- In `NoiseChannel._embed_operator` for 2-qubit channels, the operator is embedded using a nested Python loop:
  ```python
  for i in range(dim): # dim = 2^N
      for j in range(dim):
  ```
- For $N = 12$, $4^{12} = 16,777,216$ iterations in pure Python per Kraus operator. For $N = 14$, $268,435,456$ iterations. This locks the CPU indefinitely.

#### 4. Matplotlib Figure Dimension Overflow (`src/qvm/visual.py:84`)
- `plot_circuit()` computes figure width as `figsize=(max(8, depth), max(4, num_qubits * 0.5))`.
- For a circuit with $\text{depth} = 1000$, it attempts to allocate a figure 1000 inches wide ($100,000$ pixels at default 100 DPI), triggering `ValueError: Image size of ... pixels is too large. It must be less than 2^16 in each direction` or exhausting system RAM.

#### 5. Full Statevector Reconstitution in MPS Sampling (`src/qvm/mps_simulator.py:182–205`)
- `MPSSimulator.sample()` calls `sv = self.get_statevector()` and `outcome = rng.choice(len(probs), p=probs)` on every shot.
- `get_statevector()` contracts all tensors into a single $2^N$ vector. Simulating 50 qubits on MPS works during gate application, but invoking `sample()` or `api/app.py:194` crashes with `MemoryError`.

### 3.3 Logging & Diagnostics
- **No `logging` Configuration**: No logger instances (`logging.getLogger(__name__)`) are initialized in any module.
- **Stdout Pollution**:
  - `src/qvm/simulator.py:134`: `print(f"DEBUG: Error at PC {pc}, Op: {op}")`
  - `src/qvm/util/export.py:63`: `print(f"Warning: Gate '{gate_name}' not supported...")`
  - `api/app.py:241`: `print(f"Viz error: {e}")`
  - `api/app.py:275`: `print(f"Supabase logging error: {e}")`

---

## 4. Benchmarking and Telemetry Hooks

### 4.1 Current Telemetry Status
- **Zero In-Code Telemetry**: No execution timing, gate counting, circuit depth analysis, or memory profiling hooks exist in `src/qvm/simulator.py`, `src/qvm/transpiler.py`, or `src/qvm/cli.py`.
- **Dead Database Telemetry**: `api/app.py:154` queries `execution_time_ms` from Supabase `simulation_runs`, but line 259–273 does not calculate or insert `execution_time_ms` when logging runs.

### 4.2 Required Telemetry Architecture
For production readiness and automated stress testing, QVM requires a lightweight telemetry system:
```python
@dataclass
class ExecutionMetrics:
    num_qubits: int
    num_gates_initial: int
    num_gates_decomposed: int
    num_gates_transpiled: int
    circuit_depth: int
    parse_time_ms: float
    decomposition_time_ms: float
    transpilation_time_ms: float
    simulation_time_ms: float
    sampling_time_ms: float
    total_time_ms: float
    peak_memory_mb: float
    gate_throughput_ops_per_sec: float
```

---

## 5. Architectural Requirements & Design for Automated Stress Testing (`tests/test_stress.py`)

### 5.1 Objectives & Scope
The automated stress testing suite (`tests/test_stress.py`) must validate that QVM can reliably process, decompose, transpile, and execute circuits with **1000+ operations**, measuring performance metrics and reporting bottlenecks gracefully without unhandled process termination.

### 5.2 Circuit Generation Topologies (1000+ Operations)
To stress different subsystems, `tests/test_stress.py` should implement four synthetic benchmark generator classes:

```
                      ┌─────────────────────────────────────────┐
                      │ 1000+ Op Circuit Benchmark Generators   │
                      └────────────────────┬────────────────────┘
                                           │
         ┌──────────────────┬──────────────┴───────┬──────────────────┐
         ▼                  ▼                      ▼                  ▼
┌──────────────────┐ ┌────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ 1. Deep 1D Chain │ │ 2. Scaled QFT  │ │ 3. Variational   │ │ 4. QASM 3.0     │
│ Alternating Pauli│ │ O(N²) Phase    │ │ Hardware-        │ │ Text Stream     │
│ rotations & CX   │ │ ladder         │ │ Efficient Ansatz │ │ 1000+ lines     │
│ (Simulator focus)│ │ (Transpiler)   │ │ (VQE/Parameters) │ │ (Parser focus)  │
└──────────────────┘ └────────────────┘ └──────────────────┘ └─────────────────┘
```

1. **Deep 1D Rotation Chain (`generate_deep_rotation_circuit(num_qubits=4, num_gates=1000)`)**:
   - Structure: Alternating layers of single-qubit rotations ($R_X(\theta), R_Z(\phi), H, T$) and nearest-neighbor $CX$ gates.
   - Purpose: Stresses raw gate dispatch, PC loop throughput, and unitary application in `Simulator`.
   - Verification: Identity cancellation (e.g. $1000$ alternating $X$ gates must return $|0000\rangle$ with probability $1.0$).
2. **Scaled Quantum Fourier Transform (`generate_qft_circuit(num_qubits=15)`)**:
   - Structure: All-to-all controlled phase rotations $CP(\theta_{j,k})$ and Hadamard gates ($O(N^2)$ operations).
   - Purpose: Stresses `Decomposer` ($CP \to R_Z + CX$) and `Transpiler` (routing non-adjacent controlled gates across linear architecture).
3. **Variational Hardware-Efficient Ansatz (`generate_hea_circuit(num_qubits=6, layers=50)`)**:
   - Structure: Parameterized $R_Y(\theta_{i,l}), R_Z(\phi_{i,l})$ layers followed by entangling $CZ$ / $CX$ chains (totaling $1000+$ parameterized operations).
   - Purpose: Stresses `ParameterExpression` substitution, `bind_parameters()`, and `expectation_value()` calculation.
4. **OpenQASM 3.0 Programmatic Text Stream (`generate_qasm3_stream(num_lines=1500)`)**:
   - Structure: 1500-line OpenQASM 3.0 text file containing declarations, bitwise classical operations, if-conditionals, and gate calls.
   - Purpose: Stresses `Lark` LALR grammar parsing, AST recursion depth, and declaration resolution.

### 5.3 Test Suite Architecture for `tests/test_stress.py`
The test script should be structured as follows:

```python
# tests/test_stress.py Architecture Sketch

import time
import tracemalloc
import pytest
import numpy as np

from src.qvm.ir import QuantumCircuit
from src.qvm.simulator import Simulator
from src.qvm.mps_simulator import MPSSimulator
from src.qvm.transpiler import Transpiler
from src.qvm.decomposer import Decomposer
from src.qvm.architecture import get_linear_architecture
from src.qvm.qasm3_parser import OpenQASM3Parser

class PerformanceMonitor:
    def __enter__(self):
        tracemalloc.start()
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.wall_time_sec = self.end_time - self.start_time
        self.peak_memory_mb = peak / (1024 * 1024)

@pytest.mark.stress
class TestQVMStressAndScalability:
    """Automated stress testing suite for 1000+ operation circuits."""

    def test_stress_deep_circuit_statevector(self):
        """Execute 1000+ gate circuit on Statevector Simulator and measure throughput."""
        ...

    def test_stress_qasm3_parser_1000_lines(self):
        """Parse 1000+ line OpenQASM 3.0 file and measure parse latency."""
        ...

    def test_stress_transpiler_sabre_routing(self):
        """Route 1000+ gate circuit on linear architecture and measure SWAP overhead."""
        ...

    def test_stress_mps_simulator_scalability(self):
        """Simulate 1000+ nearest-neighbor gates on MPS across 20 qubits."""
        ...

    def test_stress_memory_and_ops_limit_graceful_handling(self):
        """Verify that circuits approaching max_ops are handled gracefully."""
        ...
```

---

## 6. Synthesis & Concrete Recommendations

### 6.1 Architectural Summary
1. **Simulator Unitary Optimization**: Replace the dense $O(4^N)$ `np.kron` matrix multiplication in `_apply_single_qubit_gate` with state tensor slicing/reshaping. This immediately reduces single-qubit gate memory consumption from 16 GB to 0 bytes of extra allocation on 15 qubits.
2. **Configurable Runtime Limits**: Change hardcoded `max_ops = 10000` to a configurable parameter on `Simulator(max_ops=100_000)` and expose it via CLI `--max-ops`.
3. **Structured Exception Hierarchy**: Create `src/qvm/exceptions.py` defining `QVMError`, `QVMParseError`, `QVMRuntimeError`, `QVMCompilationError`, `QVMResourceLimitError`.
4. **CLI Modernization**: Add `--engine {statevector,mps}`, `--json`, `--output <file>`, `--quiet`, `--verbose`, and `--benchmark` flags to `src/qvm/cli.py`.
5. **Shared Pytest Infrastructure**: Create `tests/conftest.py` with standard circuit fixtures, mock devices, and memory monitoring helpers. Move `src/tests_test_parser.py` into `tests/`.
6. **Stress Testing Suite**: Implement `tests/test_stress.py` with the 4 benchmark generators and performance telemetry reporting.

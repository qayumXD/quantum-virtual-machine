# Quantum Virtual Machine (QVM)

A Python quantum computing toolkit that works like a classical toolchain: **install it, point it at a circuit, run it**. QVM ingests quantum programs (OpenQASM 3.0 / 2.0 / JSON / Qiskit / Cirq), transpiles them onto hardware topologies, simulates them exactly, and exports them anywhere else — through one canonical Intermediate Representation.

```
QASM 3 ──┐                              ┌──► QVM Statevector / MPS simulation
QASM 2 ──┤   ┌────────────────┐         ├──► QVM Transpiler (Greedy / SABRE routing)
JSON  ───┼──►│    QVM IR      │─────────┼──► Qiskit  (export · Aer backend)
Qiskit ──┘   │  (the pivot)   │         └──► Cirq     (export · Cirq simulator)
Cirq  ──────►└────────────────┘
```

**v0.4 highlights**

- Installable package (`pip install`) with a `qvm` CLI entry point
- Strict framework interop: unsupported operations **raise**, they are never silently dropped
- Full bidirectional gate coverage between QVM ↔ Qiskit ↔ Cirq (22-gate vocabulary)
- Domain exception hierarchy (`QVMError` root) for reliable error handling
- In-place O(2^N) statevector kernels, configurable execution budgets, cached QASM3 parser

---

## Installation

Requires **Python ≥ 3.9**. The core depends only on `numpy` and `lark`; everything else is opt-in:

```bash
pip install quantum-virtual-machine              # lean core: parse, transpile, simulate
pip install "quantum-virtual-machine[qiskit]"    # + Qiskit & Aer interop
pip install "quantum-virtual-machine[cirq]"      # + Cirq interop
pip install "quantum-virtual-machine[viz]"       # + matplotlib visualizations
pip install "quantum-virtual-machine[server]"    # + FastAPI dashboard stack
pip install "quantum-virtual-machine[dev]"       # + pytest and dev tooling
```

From source (development):

```bash
git clone https://github.com/qayumXD/quantum-virtual-machine.git
cd quantum-virtual-machine
pip install -e ".[dev]"
```

Optional backends degrade gracefully: calling an interop API without the matching extra raises `MissingBackendError` with the exact `pip install` command to fix it.

---

## Quickstart

### CLI

```bash
qvm circuit.qasm                                   # simulate a QASM file
qvm circuit.json --nqubits 4                       # simulate a JSON gate list
qvm bell.qasm --shots 1024 --seed 42               # shot-based sampling
qvm bell.qasm --transpile --routing sabre          # route onto linear topology
qvm bell.qasm --device fake_5q                     # hardware noise profile
qvm vqe_circuit.json --nqubits 2 --expectation ZZ  # Pauli expectation value
```

### Python API

```python
from qvm.parser import OpenQASM2Parser
from qvm.transpiler import Transpiler
from qvm.simulator import Simulator
from qvm.architecture import get_linear_architecture

qc = OpenQASM2Parser.parse(open("examples/bell_state.qasm").read())

arch = get_linear_architecture(qc.num_qubits)
qc = Transpiler(arch, strategy="sabre").transpile(qc)

state, classical_memory = Simulator().simulate(qc)
print((abs(state) ** 2).round(3))
```

### Running Locally

You can run QVM as a CLI, a headless Python library, a FastAPI REST server, or a full-stack Next.js web dashboard:

#### 1. Backend REST Server (FastAPI)
```bash
# Start the API server on port 8000
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
# Verify health
curl http://127.0.0.1:8000/health
```

#### 2. Web Client Dashboard (Next.js)
```bash
cd web
npm install
npm run dev
# Dashboard available at http://localhost:3000
# Technical documentation available at http://localhost:3000/docs
```

---

## Web Dashboard & Visualizations

The QVM web application provides an interactive workspace for designing and executing quantum programs:

1. **Interactive Code Editor**: Write and edit circuits in OpenQASM 3.0, OpenQASM 2.0, or JSON.
2. **Execution Controls**:
   * **Engine Selection**: Toggle between `statevector` (exact amplitudes for $N \le 16$) and `mps` (Matrix Product States for low-entanglement circuits up to 24+ qubits).
   * **Transpilation & Routing**: Enable physical routing on linear topologies using `greedy` or `sabre` algorithms with optional uncomputation mapping restoration.
   * **Noise Configuration**: Inject depolarizing error, readout bit-flip error, or realistic $T_1/T_2$ amplitude and phase damping.
   * **Measurement Sampling**: Specify `shots` for projective measurement sampling or `0` for exact analytical statevector probabilities.
3. **Interpreting Results**:
   * **Circuit Diagram**: A clean SVG/PNG plot showing the routed gates, barriers, and measurements across physical qubits.
   * **Probability Histogram**: A bar chart displaying the probabilities of all basis states ($P(x) = |\langle x|\psi\rangle|^2$).
   * **Measurement Counts**: Sampled outcome frequencies when `shots > 0` (e.g. `{"00": 508, "11": 492}`).
   * **Classical Memory**: Final binary values recorded in named registers from mid-circuit and terminal measurements.

---

## Framework interoperability

All conversions go through the QVM IR pivot (N+M converters instead of N×M). The interop layer is governed by two guarantees:

1. **No silent drops.** Every operation either converts faithfully or raises `UnsupportedGateError` naming the offending gate. A conversion that returns means the returned circuit *is* your circuit.
2. **Physical equivalence.** Exported circuits reproduce QVM's measurement probability distributions (validated by a triple-engine test suite: QVM vs Qiskit vs Cirq).

Supported vocabulary:

| Class | Gates |
|---|---|
| 1-qubit, no parameters | `h`, `x`, `y`, `z`, `s`, `sdg`, `t`, `tdg`, `sx`, `sxdg`, `id` |
| 1-qubit, 1 angle | `rx(θ)`, `ry(θ)`, `rz(θ)`, `p(λ)` |
| 2-qubit, no parameters | `cx`, `cz`, `swap` |
| 2-qubit, 1 angle | `rxx(θ)`, `rzz(θ)`, `cp(λ)` |
| 3-qubit | `ccx` |
| Ancillary | `measure`, `barrier`, `delay` |

Notes:

- **Parameters**: symbolic parameters survive conversion (Qiskit `Parameter` ↔ QVM `Parameter` ↔ Cirq sympy symbols). Fully-bound expressions export as floats; partially-bound ones raise `QVMConversionError` until you call `bind_parameters()`.
- **Measurements**: Cirq keys use the canonical `"register[index]"` format; legacy tuple-string keys are still parsed on import.
- **Global phase** is not represented in the IR and is therefore not preserved (physically unobservable, same convention as OpenQASM).
- **Multi-controlled gates** (`mcx`, `mcphase`, `mcry`, `mcrz`, `ccz`, ...) are lowered *exactly* into basis gates during import — Grover oracles built with native `mcx` just work.
- Anything else outside the vocabulary fails loudly with a message listing the supported set (or pass `transpile_foreign=True` to auto-transpile via Qiskit).

Full details: [`docs/guides/INTEROP.md`](https://github.com/qayumXD/quantum-virtual-machine/main/docs/guides/INTEROP.md)

---

## Error handling

Every QVM error derives from one base class, so callers can catch broadly or narrowly:

```python
from qvm.exceptions import (
    QVMError,               # root
    QVMParseError,          # syntax / grammar failures        (ValueError)
    QVMCompilationError,    # routing / decomposition / conversion failures
    UnsupportedGateError,   # gate outside a subsystem's vocabulary
    QVMConversionError,     # unfaithful-or-impossible format conversion
    MissingBackendError,    # optional Qiskit/Cirq extra not installed (ImportError)
    QVMRuntimeError,        # simulation failures               (RuntimeError)
    QVMResourceLimitError,  # op-budget breaches                (RuntimeError)
)
```

Concrete classes also inherit the built-in shown in parentheses, so existing `except ValueError` / `except RuntimeError` code keeps working during migration.

Validation is eager: malformed arities (`cx` on one qubit), measurements into undeclared registers, and unknown gates all fail at circuit-construction time — never mid-simulation.

---

## Simulation engines

| Engine | Use case | Notes |
|---|---|---|
| `Simulator` (statevector) | Exact amplitudes, N ≲ 12–16 | In-place tensor-stride kernels, full classical memory + label/jump control flow, stochastic Kraus noise trajectories |
| `MPSSimulator` | Low-entanglement circuits, 20+ qubits | SVD evolution with exact SWAP-routing of long-range gates — see [benchmark](https://github.com/qayumXD/quantum-virtual-machine/main/docs/reports/benchmark_2026-08-24.md): GHZ-24 in 1.6 ms |

Noise modeling supports depolarizing, amplitude damping, and phase damping channels plus device profiles (`fake_5q`, `fake_7q`, `ideal`). For a candid assessment of scaling limits beyond this range, see [`docs/production_readiness_analysis.md`](https://github.com/qayumXD/quantum-virtual-machine/main/docs/production_readiness_analysis.md).

---

## Testing

```bash
pytest                                        # whole unit + interop suite
pytest tests/test_interop_roundtrip.py -v     # interop guarantees (triple-engine equivalence)
python -m benchmarks.run_audit --all          # 20-algorithm audit corpus (QASM/Qiskit/Cirq/VQE/QAOA)
```

## Tutorials & Practical Use Cases

QVM includes comprehensive, executable tutorials available as both CI-verified Jupyter notebooks and step-by-step markdown guides:

| Tutorial | Focus & Capabilities | Notebook | Markdown Guide |
|---|---|---|---|
| **1. Quantum Circuit Basics** | Qubits, superposition, gates ($X, H, R_y$), projective measurement, and REST API calls. | — | [`docs/tutorials/01_quantum_circuit_basics.md`](docs/tutorials/01_quantum_circuit_basics.md) |
| **2. Quantum Entanglement** | Bell state $|\Phi^+\rangle$, CNOT correlations, exact state evolution, and Qiskit/Cirq export. | [`tutorials/01_hello_bell.ipynb`](tutorials/01_hello_bell.ipynb) | [`docs/tutorials/02_quantum_entanglement.md`](docs/tutorials/02_quantum_entanglement.md) |
| **3. Grover's Search Algorithm** | 3-qubit unstructured search marking $\|101\rangle$, phase oracle, diffusion operator, and probability amplification. | [`tutorials/03_grover_search.ipynb`](tutorials/03_grover_search.ipynb) | [`docs/tutorials/03_grovers_algorithm.md`](docs/tutorials/03_grovers_algorithm.md) |
| **4. Quantum Teleportation** | Dynamic circuits in OpenQASM 3: 3-qubit protocol, mid-circuit measurement, and classical conditional corrections. | [`tutorials/02_teleportation.ipynb`](tutorials/02_teleportation.ipynb) | [`docs/tutorials/04_quantum_teleportation.md`](docs/tutorials/04_quantum_teleportation.md) |
| **5. Variational Quantum Eigensolver** | $\text{H}_2$ ground-state energy in STO-3G, parameterized ansatz, Pauli Hamiltonian expectation values, and classical optimization. | [`tutorials/04_vqe_in_30_lines.ipynb`](tutorials/04_vqe_in_30_lines.ipynb) | [`docs/tutorials/05_variational_quantum_eigensolver.md`](docs/tutorials/05_variational_quantum_eigensolver.md) |

Every notebook is executed by `tests/test_tutorials.py` on every CI run, ensuring that no tutorial code rots.

---

## API Documentation

QVM exposes a production-ready FastAPI service for headless simulation, containerized deployments, and web interfaces:

*   **Primary Execution Endpoint**: `POST /run` (accepts OpenQASM 2/3 and JSON; returns state probabilities, sampled counts, base64 circuit and histogram plots, and Pauli expectation values).
*   **Documentation Guides**:
    *   [REST API Reference Guide](docs/guides/API_REFERENCE.md)
    *   [Interactive Web Docs (`/docs`)](web/docs-content/810_REST_API_Reference.md)
    *   Swagger UI: `http://localhost:8000/docs`

---

## Troubleshooting & Known Limitations

### Scaling Limits
*   **Statevector Engine (`Simulator`)**: Memory scales as $O(2^N)$ complex amplitudes. Circuits with $N \le 14$ execute in milliseconds; $N \ge 16$ requires substantial memory (~0.5–1 GB). For large 1D low-entanglement systems ($N \ge 20$), select the `engine="mps"` (Matrix Product States) backend.
*   **MPS Simulator**: Requires circuits with moderate bipartite entanglement. Deep circuits with dense all-to-all entangling gates will experience SVD truncation or high bond dimensions.

### Common Errors & Solutions
*   `MissingBackendError: Cirq is not installed`: Install the Cirq extra via `pip install "quantum-virtual-machine[cirq]"`.
*   `MissingBackendError: Qiskit is not installed`: Install the Qiskit extra via `pip install "quantum-virtual-machine[qiskit]"`.
*   `UnsupportedGateError`: QVM strictly enforces physical equivalence. Any gate outside the 22-gate vocabulary will raise this error rather than silently degrading. Pass `transpile_foreign=True` to auto-transpile through Qiskit if available.
*   `QVMParseError`: Ensure your OpenQASM header starts with `OPENQASM 2.0;` or `OPENQASM 3.0;` and uses standard includes (`qelib1.inc` or `stdgates.inc`).

---

## Project layout

```
quantum-virtual-machine/
├── pyproject.toml            # packaging, extras, console script
├── src/qvm/                  # the installable `qvm` package
│   ├── ir.py                 # QuantumCircuit IR + framework converters
│   ├── parser.py             # QASM 2.0 + JSON ingestion
│   ├── qasm3_parser.py       # OpenQASM 3.0 (Lark LALR, module-cached)
│   ├── transpiler.py         # Greedy / SABRE routing
│   ├── decomposer.py         # gate decomposition passes
│   ├── simulator.py          # dense statevector engine
│   ├── mps_simulator.py      # tensor-network engine
│   ├── noise.py              # Kraus channels & noise models
│   ├── observable.py         # Hamiltonians / Pauli expectations
│   ├── vqe.py / qaoa.py / gradient.py / parameter.py
│   ├── cli.py                # `qvm` command
│   ├── exceptions.py         # domain error hierarchy
│   └── util/export.py        # exporters
├── api/app.py                # optional FastAPI service
├── web/                      # optional Next.js dashboard
├── tests/                    # pytest suite (incl. interop + stress)
└── docs/                     # design docs, guides, readiness analysis
```

## License

MIT — see distribution metadata.

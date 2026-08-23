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

### Framework bridge

```python
import cirq, qiskit
from qvm.ir import QuantumCircuit

circuit = cirq.Circuit(cirq.H(cirq.LineQubit(0)), cirq.CNOT.on(cirq.LineQubit(0), cirq.LineQubit(1)))
qk_circuit = QuantumCircuit.cirq_to_qiskit(circuit)   # Cirq → QVM IR → Qiskit
```

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

## Tutorials

Executable notebooks in [`tutorials/`](https://github.com/qayumXD/quantum-virtual-machine/main/tutorials/) — each one is run by CI so it cannot rot:

1. [`01_hello_bell.ipynb`](https://github.com/qayumXD/quantum-virtual-machine/main/tutorials/01_hello_bell.ipynb) — ingest QASM, simulate, export to Qiskit & Cirq, cross-check with Aer
2. [`02_teleportation.ipynb`](https://github.com/qayumXD/quantum-virtual-machine/main/tutorials/02_teleportation.ipynb) — dynamic circuits: mid-circuit measurement + classical feedback
3. [`03_grover_search.ipynb`](https://github.com/qayumXD/quantum-virtual-machine/main/tutorials/03_grover_search.ipynb) — Grover in OpenQASM 3 validated against ideal amplitudes
4. [`04_vqe_in_30_lines.ipynb`](https://github.com/qayumXD/quantum-virtual-machine/main/tutorials/04_vqe_in_30_lines.ipynb) — H₂ ground state via VQE

The interop suite verifies probability agreement across QVM, Qiskit, and Cirq for every gate in the vocabulary, round-trip structural preservation, and that unsupported inputs raise rather than corrupt. The audit corpus runs textbook-to-industry algorithms end-to-end and cross-validates against native simulators — see [`docs/reports/algorithm_audit_2026-08-24.md`](docs/reports/algorithm_audit_2026-08-24.md).

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

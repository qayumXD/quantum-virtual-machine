# Project: Quantum Virtual Machine (QVM) Production Readiness & Stress Suite

## Architecture Overview
The Quantum Virtual Machine (QVM) is an end-to-end software suite for quantum circuit ingestion, compilation, simulation, and noise modeling. Its core architectural layers comprise:
1. **Front-End & Language Ingestion**:
   - OpenQASM 3.0 parser (`src/qvm/qasm3_parser.py`, `src/qvm/qasm3.lark` based on Lark LALR(1)).
   - OpenQASM 2.0 parser (`src/qvm/parser.py` using custom regex string splitting).
   - Intermediate Representation (`src/qvm/ir.py` — `QuantumCircuit`, `QuantumRegister`, `ClassicalRegister`, `GATE_SPEC`).
2. **Compiler & Transpilation**:
   - Hardware architecture mapping & routing (`src/qvm/transpiler.py`, `src/qvm/coupling.py` using Greedy and SABRE heuristics).
   - Gate decomposition & canonical basis translation.
3. **Execution & Simulation Backends**:
   - Dense Statevector Simulator (`src/qvm/simulator.py` supporting exact unitary evolution and measurement sampling).
   - Matrix Product State Simulator (`src/qvm/mps_simulator.py` for 1D tensor network simulation with SVD truncation).
   - Noise Modeling (`src/qvm/noise.py` supporting Kraus operators, depolarizing, amplitude/phase damping).
   - Quantum Hardware Emulation (`src/qvm/device.py` — Fake5Q, Fake7Q, Ideal).
4. **Runtime, CLI & Server Infrastructure**:
   - Command Line Interface (`src/qvm/cli.py`).
   - FastAPI REST Server & WebSocket service (`api/app.py`).
   - Export & Visualization (`src/qvm/export.py`, `src/qvm/visual.py`).

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Architectural Gap Analysis Report | Comprehensive technical gap analysis (`docs/production_readiness_analysis.md`) evaluating parser, simulation, memory, noise, CLI, and runtime for 1000+ line circuits with code citations and production roadmap | M1 | ORIGINAL_REQUEST R1 |
| 2 | Automated Stress Testing Suite | Dedicated pytest stress suite (`tests/test_stress.py`) programmatically generating 1000+ op circuits across multiple topologies (1D rotation chains, scaled QFT, HEA ansatz, QASM 3 streams) with timing, memory profiling, and graceful failure handling | M2 | ORIGINAL_REQUEST R2 |
| 3 | Parser Pipeline Verification | Analysis and stress testing of OpenQASM 2/3 parsers under 1000+ line inputs, loop unrolling limits, parser instantiation latency, and syntax validation | M1 & M2 | Survey 1 |
| 4 | Simulation Scaling & Bottleneck Analysis | Analysis of single-qubit Kronecker $O(4^N)$ memory blowup, permutation gate allocations, noise loop complexity, and hardcoded `max_ops` limits | M1 & M2 | Survey 2 |
| 5 | Runtime UX & Telemetry Analysis | Assessment of CLI flags, JSON output, domain exception hierarchy, logging, and Matplotlib depth blowout | M1 | Survey 3 |
| 6 | E2E Execution & Forensic Audit | Verification of stress suite execution against QVM, collecting benchmark metrics, Reviewer passes, Challenger empirical tests, and Forensic Audit verification | M3 | System Protocol |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Architectural Gap Analysis Report | Draft comprehensive, publication-grade `docs/production_readiness_analysis.md` detailing architecture, code-level bottlenecks (lines & files), mathematical scaling, and step-by-step roadmap | none | DONE |
| 2 | Automated Stress Testing Suite | Implement `tests/test_stress.py` with 4 circuit generator topologies (1000+ operations), pytest execution, metrics collection, and graceful bottleneck capture | none | DONE |
| 3 | E2E Stress Execution, Verification & Forensic Audit | Execute stress suite with pytest, verify test outcomes, run 2 Reviewers, 2 Challengers, and 1 Forensic Auditor for strict integrity verification | M1, M2 | DONE |

---

## Interface Contracts & Deliverables Specification

### Deliverable R1: `docs/production_readiness_analysis.md`
- **Location**: `docs/production_readiness_analysis.md`
- **Required Sections**:
  1. Executive Summary & Production Readiness Verdict (Educational Prototype vs Production Compiler).
  2. Architecture Breakdown (Parser, IR, Transpiler, Simulators, Noise, Runtime).
  3. Scalability Bottlenecks & Inefficiencies (1000+ line / 1000+ gate programs) with precise code references (file & line numbers):
     - Dense Kronecker unitary explosion ($O(4^N)$ memory) in `src/qvm/simulator.py:160-166`.
     - $O(4^N)$ pure-Python nested loops in 2-qubit Kraus noise embedding in `src/qvm/noise.py:112-127`.
     - Permutation gate temporary array heap churn ($33 \cdot 2^N$ bytes/gate) in `src/qvm/simulator.py:168-195`.
     - Hardcoded `max_ops = 10000` execution ceiling in `src/qvm/simulator.py:62, 376`.
     - OpenQASM 3 parser 30ms re-instantiation latency and AST memory footprint during loop unrolling in `src/qvm/qasm3_parser.py`.
     - Control-flow semantic inversions and bounds-checking gaps in parser and IR.
     - CLI deficiencies (missing `--json`, `--engine mps`, telemetry) and lack of domain exception hierarchy.
     - Matplotlib linear depth blowout in `src/qvm/visual.py:84`.
  4. Mathematical & Empirical Scaling Models (FLOPs, peak memory, throughput).
  5. Step-by-Step Production Roadmap (Phase 1: Critical Correctness & Kernel Optimization; Phase 2: Transpilation & Fusion Passes; Phase 3: Runtime Hardening & Telemetry; Phase 4: Advanced Backends).

### Deliverable R2: `tests/test_stress.py`
- **Location**: `tests/test_stress.py`
- **Required Characteristics**:
  1. Pytest compatibility (`pytest tests/test_stress.py -v`).
  2. Four programmatic circuit generation functions:
     - `generate_deep_rotation_circuit(num_qubits, num_gates)`: 1000+ single-qubit rotation gates chaining $R_x, R_y, R_z, H, T$.
     - `generate_qft_circuit(num_qubits)`: Scaled Quantum Fourier Transform circuit with Hadamard and controlled-phase rotations.
     - `generate_hea_ansatz_circuit(num_qubits, layers)`: Hardware-Efficient Ansatz with 1000+ alternating parameterized rotation layers and entangling CNOT/CZ ladders.
     - `generate_qasm3_loop_stream(iterations)`: OpenQASM 3.0 string stream testing parser throughput and unrolling limits.
  3. Metric recording: execution wall-clock time, gate throughput (ops/sec), peak memory / allocation delta.
  4. Graceful failure / bottleneck handling: capturing expected memory/operation limits cleanly with informative diagnostics without unhandled crash.
  5. Parametrized test functions validating both small baselines and 1000+ gate stress workloads on `Simulator` and `MPSSimulator`.

---

## Code Layout
```
quantum-virtual-machine/
├── .agents/                          # Agent coordination metadata (plans, progress, handoffs)
├── api/                              # FastAPI REST & WebSocket server
│   └── app.py
├── docs/                             # Documentation
│   └── production_readiness_analysis.md # [Deliverable R1]
├── src/qvm/                          # Core QVM Python package
│   ├── cli.py                        # CLI entry point
│   ├── coupling.py                   # Hardware coupling maps
│   ├── device.py                     # Mock quantum devices
│   ├── export.py                     # Circuit exporters
│   ├── ir.py                         # Quantum Circuit IR
│   ├── mps_simulator.py              # Matrix Product State simulator
│   ├── noise.py                      # Noise channels & models
│   ├── parser.py                     # QASM 2.0 parser
│   ├── qasm3_parser.py               # QASM 3.0 parser
│   ├── qasm3.lark                    # QASM 3.0 grammar
│   ├── simulator.py                  # Statevector simulator
│   ├── transpiler.py                 # Routing & optimization passes
│   └── visual.py                     # Circuit visualization
└── tests/                            # Pytest test suite
    ├── test_stress.py                # [Deliverable R2]
    └── ... (18 unit test modules)
```

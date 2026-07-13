---
tags: [architecture, system-design, design-patterns, qiskit, cirq]
---
# 🏗️ System Architecture & External SDK Boundaries

The Quantum Virtual Machine (QVM) is structured as a modular, hardware-agnostic compilation and execution environment. To ensure high extensibility, it decouples circuit ingest formats, intermediate representations, architectural constraints, and simulation engines.

---

## 🗺️ Architectural Topology

The system follows a strict **Pipeline Architecture Pattern**. User programs flow through a series of decoupled transformations before execution:

```mermaid
graph TD
    UserCode[User Program: OpenQASM 3.0 / JSON] -->|Parse| FrontEnd[Parser Frontend: OpenQASM3Parser]
    FrontEnd -->|Logical IR| IR[Intermediate Representation: QuantumCircuit]
    IR -->|Compile / Optimize| Decomposer[Gate Decomposer: CCX -> Native]
    Decomposer -->|Native Logical IR| Transpiler[Transpiler: Routing / SWAP Mapping]
    Transpiler -->|Physical Native IR| BackendDispatcher{Backend Dispatcher}
    
    BackendDispatcher -->|Exact State| SV[Statevector Simulator]
    BackendDispatcher -->|Tensor Network| MPS[Matrix Product State Simulator]
    BackendDispatcher -->|External Target| QiskitAer[Qiskit Aer Simulator Wrapper]
    BackendDispatcher -->|External Target| CirqSim[Cirq Simulator Wrapper]
    
    SV -->|Compute Expectation| GroundState[VQE / QAOA Application Layer]
    SV -->|Stochastic Kraus Trajectory| Noise[Kraus Noise Model Engine]
    
    Noise -->|Plotting| Vis[Visualizer: Matplotlib Circuit / Histogram]
    MPS -->|Plotting| Vis
    
    Vis -->|Base64 Output| WebUI[FastAPI Web Dashboard]
    Vis -->|CLI Print / Image| CLI[Argparse CLI Client]
```

---

## 📂 Monorepo Modular Structure

The codebase is organized to maintain a clear boundary between frontend parsing, core intermediate models, execution backends, and user interfaces:

*   **`src/qvm/`**: Core library modules
    *   [ir.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/ir.py): Central data structures. Defines `QuantumCircuit` and hooks for external formats.
    *   [parameter.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/parameter.py): Math structures for symbolic parameters, expressions, and evaluation bindings.
    *   [parser.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/parser.py): Lexer/parsers for JSON payload mapping and OpenQASM 2.0.
    *   [qasm3_parser.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/qasm3_parser.py): Lexer/AST converter for OpenQASM 3.0 via Lark grammar specifications.
    *   [architecture.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/architecture.py): Data structure defining physical connectivity grids and native gates.
    *   [transpiler.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/transpiler.py): Qubit routing algorithms (Greedy and SABRE).
    *   [decomposer.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/decomposer.py): Standard compiler gate decomposer (e.g. Toffoli unrolling).
    *   [simulator.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/simulator.py): Statevector engine, classical registers, expectation logic, and noise mapping.
    *   [mps_simulator.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/mps_simulator.py): Matrix Product State simulator for larger qubit spaces.
    *   [noise.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/noise.py): Kraus noise model structures, thermal damping, and hardware backends.
    *   [observable.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/observable.py): Hamiltonian definitions and Pauli algebraic operators.
    *   [gradient.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/gradient.py): Analytical parameter-shift gradients and finite differences.
    *   [vqe.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/vqe.py) & [qaoa.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/qaoa.py): Variational algorithm solvers.
    *   [visual.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/visual.py): Plotting engines.
    *   [cli.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/cli.py) & [server.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/server.py): Command Line and API servers.
*   **`api/`**: FastAPI routers
    *   [app.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/api/app.py): Exposes HTTP services, wraps run requests, builds custom noise structures, and generates visual plots.
*   **`web/`**: UI dashboard assets
    *   [Next.js Dashboard](https://github.com/qayumXD/quantum-virtual-machine/blob/main/web/src/app/page.tsx): Modern React/Next.js dashboard for interactive circuit editing, transpilation parameter adjusting, execution history logs, and histogram inspection.

---

## 🔌 Interoperability and SDK Boundaries

To support QVM as an educational bridge, the `QuantumCircuit` intermediate representation includes wrappers for bidirectional translation between standard frameworks:

### 1. Qiskit Integration
*   **Logical Conversion**: `QuantumCircuit.to_qiskit()` translates internal operations, parameters, and classical registers into `qiskit.QuantumCircuit` structures. Conversely, `QuantumCircuit.from_qiskit()` extracts gates and properties.
*   **Execution Fallback**: `QuantumCircuit.run_qiskit_simulator()` compiles the local circuit and routes execution directly to Qiskit's `AerSimulator` backend.

### 2. Cirq Integration
*   **Logical Conversion**: `QuantumCircuit.to_cirq()` maps local operations onto `cirq.Circuit` pipelines using `cirq.LineQubit` grids. `QuantumCircuit.from_cirq()` reconstructs circuit objects from Cirq structures.
*   **Execution Fallback**: `QuantumCircuit.run_cirq_simulator()` evaluates the circuit on Cirq's standard simulator and translates the results into measurement counts.

> [!NOTE]
> All external SDK dependencies (Qiskit and Cirq) are imported lazily inside [ir.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/ir.py) using try-catch blocks. If these packages are not installed, the QVM continues to execute successfully using its internal Statevector and MPS engines.

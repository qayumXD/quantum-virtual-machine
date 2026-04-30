# 🚀 Quantum Virtual Machine (QVM) - Complete Usage Guide

**Last Updated:** April 28, 2026  
**Project:** Quantum Virtual Machine (QVM) - Educational Quantum Simulator  
**Status:** All dependencies installed and ready to use

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Running the Application](#running-the-application)
3. [Running Tests](#running-tests)
4. [Transpilation](#transpilation)
5. [Visualization](#visualization)
6. [CLI Commands](#cli-commands)
7. [Web Interface (GUI)](#web-interface-gui)
8. [Code Examples](#code-examples)
9. [Algorithm Examples](#algorithm-examples)

---

## 🎯 Quick Start

### Prerequisites Check
All dependencies are already installed on your laptop. Verify with:

```bash
python --version          # Should be 3.10+
pip list | grep -E "pytest|numpy|matplotlib|fastapi"
```

### Fastest Way to Run

**Option 1: Web Interface (Recommended for beginners)**
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
# Then open: http://127.0.0.1:8000/web
```

**Option 2: CLI (Quick command-line execution)**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2
```

**Option 3: Run Tests**
```bash
python -m pytest tests/ -v
```

---

## 🏃 Running the Application

### 1. Web Interface (GUI) - Interactive Dashboard

#### Start the Server
```bash
# Basic start
python -m src.qvm.server --host 127.0.0.1 --port 8000

# With auto-reload (for development)
python -m src.qvm.server --host 127.0.0.1 --port 8000 --reload

# Custom port
python -m src.qvm.server --host 127.0.0.1 --port 9000
```

#### Access the Dashboard
- Open browser: `http://127.0.0.1:8000/web`
- Or: `http://127.0.0.1:8000` (redirects to /web)

#### API Endpoints
- `GET /health` - Check server status
- `POST /run` - Execute quantum circuit
- `GET /web` - Web dashboard

#### Example API Call (cURL)
```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "cx", "qubits": [0, 1]}
    ],
    "nqubits": 2,
    "shots": 1000
  }'
```

---

### 2. Command Line Interface (CLI)

#### Basic Syntax
```bash
python -m src.qvm.cli <input_file> --nqubits <N> [options]
```

#### Common Options
| Option | Description | Example |
|--------|-------------|---------|
| `--nqubits N` | Number of qubits (required) | `--nqubits 2` |
| `--transpile` | Enable transpilation | `--transpile` |
| `--routing {greedy,sabre}` | Routing strategy | `--routing sabre` |
| `--visualize` | Show plots | `--visualize` |
| `--shots N` | Number of samples | `--shots 1000` |
| `--seed N` | Random seed | `--seed 42` |
| `--noise-depol P` | Depolarizing noise | `--noise-depol 0.01` |
| `--noise-readout P` | Readout noise | `--noise-readout 0.01` |
| `--export PATH` | Save as QASM | `--export output.qasm` |
| `--collapse` | Mid-circuit measurement | `--collapse` |

#### CLI Examples

**Simple Bell State**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2
```

**With Visualization**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

**With Transpilation (SABRE routing)**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre
```

**With Sampling (1000 shots)**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000
```

**With Noise Simulation**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 \
  --noise-depol 0.05 --noise-readout 0.01
```

**QASM File Input**
```bash
python -m src.qvm.cli examples/bell_state.qasm --nqubits 2
```

**Export Transpiled Circuit**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --export output.qasm
```

---

## 🧪 Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_simulator.py -v
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_transpiler.py -v
```

### Run Specific Test
```bash
python -m pytest tests/test_simulator.py::test_bell_state -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Available Test Suites
| Test File | Purpose |
|-----------|---------|
| `test_api.py` | FastAPI endpoints |
| `test_parser.py` | JSON circuit parsing |
| `test_qasm_parser.py` | OpenQASM 2.0 parsing |
| `test_qasm3_extended.py` | OpenQASM 3.0 features |
| `test_qasm3_loops.py` | Control flow (loops) |
| `test_qasm3_shadow.py` | Classical shadowing |
| `test_simulator.py` | Statevector simulator |
| `test_decomposer.py` | Gate decomposition |
| `test_transpiler.py` | Circuit transpilation |
| `test_cirq_parser.py` | Cirq integration |
| `test_visual.py` | Visualization |
| `test_ir.py` | Internal representation |

---

## 🔄 Transpilation

### What is Transpilation?

Transpilation maps a logical quantum circuit to a physical hardware topology. For example, if your circuit has a CNOT between qubits 0 and 2, but your hardware only supports adjacent qubits, the transpiler adds SWAP gates.

### Transpilation Strategies

#### Greedy Routing (Default)
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing greedy
```
- Fast but may use more SWAPs
- Good for quick prototyping

#### SABRE Routing (Recommended)
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre
```
- Uses lookahead heuristic
- Reduces SWAP count
- Better for optimization

### Restore Mapping
By default, the transpiler restores the original qubit mapping:
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --no-restore-mapping
```
- Without `--no-restore-mapping`: Final qubits match logical labels
- With `--no-restore-mapping`: Final qubits follow physical layout

---

## 📊 Visualization

### CLI Visualization
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

This displays:
1. **Circuit Diagram** - Visual representation of gates
2. **Probability Histogram** - Measurement outcome probabilities

### Visualization Output
- Circuit diagram shows all gates and their connections
- Histogram shows probability distribution across basis states
- Windows pop up automatically (requires display)

---

## 💻 CLI Commands Reference

### All Available Commands

```bash
# 1. Basic execution
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# 2. With transpilation
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile

# 3. With SABRE routing
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre

# 4. With visualization
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize

# 5. With sampling (1000 shots)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# 6. With noise
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 \
  --noise-depol 0.05 --noise-readout 0.01

# 7. Export to QASM
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --export output.qasm

# 8. QASM input
python -m src.qvm.cli examples/bell_state.qasm --nqubits 2

# 9. Full example with all options
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre --visualize --shots 1000 \
  --noise-depol 0.01 --noise-readout 0.01 --export output.qasm --seed 42
```

---

## 🌐 Web Interface (GUI)

### Starting the Server
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
```

### Accessing the Dashboard
1. Open browser
2. Navigate to: `http://127.0.0.1:8000/web`
3. You'll see the interactive dashboard

### Dashboard Features

#### Input Section
- **Source Type**: Choose between JSON or QASM
- **Circuit Definition**: Paste JSON or QASM code
- **Number of Qubits**: Specify qubit count
- **Shots**: Number of measurement samples

#### Options
- **Transpile**: Enable circuit transpilation
- **Routing**: Choose greedy or SABRE
- **Noise**: Add depolarizing and readout noise
- **Seed**: Set random seed for reproducibility

#### Output Section
- **Probabilities**: Probability distribution
- **Counts**: Measurement counts (if shots > 0)
- **Transpiled Operations**: List of transpiled gates
- **OpenQASM 2.0**: Generated QASM code

### Example Workflow
1. Keep default Bell State JSON
2. Set shots to 1000
3. Click "Run"
4. View results in output section

---

## 📝 Code Examples

### Example 1: Bell State (Entanglement)

#### JSON Format
```json
[
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]}
]
```

#### OpenQASM 3.0 Format
```qasm
OPENQASM 3.0;
qubit[2] q;
h q[0];
cx q[0], q[1];
```

#### What This Does
- **H gate on qubit 0**: Creates superposition (|0⟩ + |1⟩)/√2
- **CNOT gate**: Entangles qubits 0 and 1
- **Result**: Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
- **Expected Output**: 50% probability for |00⟩, 50% for |11⟩

#### Run It
```bash
# CLI
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# Expected output: ~500 counts for "00", ~500 for "11"
```

---

### Example 2: Bernstein-Vazirani Algorithm

#### JSON Format
```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [3]},
    {"name": "h", "qubits": [3]},
    {"name": "cx", "qubits": [0, 3]},
    {"name": "cx", "qubits": [2, 3]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]}
]
```

#### OpenQASM 3.0 Format
```qasm
OPENQASM 3.0;
qubit[4] q;

// Initialize superposition
h q[0];
h q[1];
h q[2];

// Initialize ancilla
x q[3];
h q[3];

// Oracle for secret "101"
cx q[0], q[3];
cx q[2], q[3];

// Final Hadamard basis
h q[0];
h q[1];
h q[2];
```

#### What This Does
- **Purpose**: Finds a hidden bitstring in one quantum query
- **Secret**: 101 (encoded in the oracle)
- **Input qubits**: 0, 1, 2 (query register)
- **Ancilla qubit**: 3 (phase kickback)
- **Result**: Measures to "101" with high probability
- **Speedup**: Exponential vs classical (1 query vs 2^n queries)

#### Run It
```bash
# CLI
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000

# Expected output: Dominant state is "101*" (ancilla superposed)
```

---

### Example 3: Grover's Search Algorithm

#### JSON Format (Simplified - searching for "101")
```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "toffoli", "qubits": [0, 1, 2]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [1]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [0]},
    {"name": "x", "qubits": [1]},
    {"name": "x", "qubits": [2]},
    {"name": "h", "qubits": [2]},
    {"name": "toffoli", "qubits": [0, 1, 2]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [0]},
    {"name": "x", "qubits": [1]},
    {"name": "x", "qubits": [2]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]}
]
```

#### OpenQASM 3.0 Format
```qasm
OPENQASM 3.0;
qubit[3] q;

// Initialize superposition
h q[0];
h q[1];
h q[2];

// Grover iteration (repeated 2 times for 3 qubits)
// Oracle: marks |101⟩
x q[1];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[1];

// Diffusion operator
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];
```

#### What This Does
- **Purpose**: Searches unsorted database for marked item
- **Target**: State |101⟩
- **Speedup**: √N vs N (quadratic speedup)
- **Iterations**: ~π/4 × √N iterations needed
- **Result**: Measures to "101" with ~94% probability

#### Run It
```bash
# CLI
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --shots 1000

# Expected output: ~940 counts for "101", rest distributed
```

---

## 🧮 Algorithm Examples

### Generate Bernstein-Vazirani Circuit
```bash
python examples/generate_bv.py --secret 101 --output examples/bv_custom.json
python -m src.qvm.cli examples/bv_custom.json --nqubits 4 --shots 1000
```

### Generate Grover Circuit
```bash
python examples/generate_grover.py --target 101 --output examples/grover_custom.json
python -m src.qvm.cli examples/grover_custom.json --nqubits 3 --shots 1000
```

### Cirq Integration
```bash
python examples/cirq_to_ir_demo.py
```

---

## 📊 Output Interpretation

### Probabilities Output
```
Probabilities: [0.5, 0.0, 0.0, 0.5]
```
- Index 0 (|00⟩): 50%
- Index 1 (|01⟩): 0%
- Index 2 (|10⟩): 0%
- Index 3 (|11⟩): 50%

### Counts Output (with shots)
```json
{
  "00": 512,
  "11": 488
}
```
- Out of 1000 shots: 512 measured |00⟩, 488 measured |11⟩

### Transpiled Operations
```json
[
  {"name": "h", "qubits": [0]},
  {"name": "cx", "qubits": [0, 1]}
]
```
- Shows gates after transpilation (may include SWAPs)

---

## 🔧 Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Use different port
python -m src.qvm.server --host 127.0.0.1 --port 9000
```

### Tests Fail
```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Run specific test
python -m pytest tests/test_simulator.py::test_bell_state -v
```

### QASM Parsing Error
```bash
# Verify QASM syntax
python -c "from src.qvm.parser import QASMParser; QASMParser().parse(open('file.qasm').read())"
```

### Visualization Not Showing
```bash
# Ensure matplotlib backend is set
export MPLBACKEND=TkAgg
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

---

## 📚 File Locations

```
quantum-virtual-machine/
├── src/qvm/
│   ├── cli.py              # CLI entry point
│   ├── server.py           # FastAPI server
│   ├── parser.py           # JSON parser
│   ├── qasm_parser.py      # OpenQASM parser
│   ├── simulator.py        # Statevector simulator
│   ├── mps_simulator.py    # MPS simulator
│   ├── transpiler.py       # Circuit transpiler
│   └── ir.py               # Internal representation
├── api/
│   ├── app.py              # FastAPI app
│   └── __init__.py
├── web/
│   └── index.html          # Dashboard UI
├── examples/
│   ├── bell_state.json     # Bell state circuit
│   ├── bell_state.qasm     # Bell state QASM
│   ├── bv_101.json         # Bernstein-Vazirani
│   ├── grover_101.json     # Grover's algorithm
│   ├── generate_bv.py      # BV generator
│   └── generate_grover.py  # Grover generator
├── tests/
│   ├── test_simulator.py
│   ├── test_parser.py
│   ├── test_transpiler.py
│   └── ... (10+ test files)
└── docs/
    ├── guides/
    │   ├── CLI_Usage.md
    │   ├── GUI_Usage.md
    │   └── Examples.md
    └── algorithms/
        ├── Bernstein_Vazirani.md
        └── Grover.md
```

---

## 🎓 Learning Path

1. **Start Here**: Run Bell State example
   ```bash
   python -m src.qvm.cli examples/bell_state.json --nqubits 2
   ```

2. **Try Web UI**: Start server and explore dashboard
   ```bash
   python -m src.qvm.server --host 127.0.0.1 --port 8000
   ```

3. **Run Tests**: Verify everything works
   ```bash
   python -m pytest tests/ -v
   ```

4. **Explore Algorithms**: Try Bernstein-Vazirani and Grover
   ```bash
   python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000
   python -m src.qvm.cli examples/grover_101.json --nqubits 3 --shots 1000
   ```

5. **Transpilation**: Learn about circuit mapping
   ```bash
   python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre
   ```

6. **Noise Simulation**: Add realistic noise
   ```bash
   python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 --noise-depol 0.05
   ```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start Web UI | `python -m src.qvm.server --host 127.0.0.1 --port 8000` |
| Run Bell State | `python -m src.qvm.cli examples/bell_state.json --nqubits 2` |
| Run with Visualization | `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize` |
| Run Tests | `python -m pytest tests/ -v` |
| Run Specific Test | `python -m pytest tests/test_simulator.py -v` |
| Transpile Circuit | `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile` |
| Add Noise | `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --noise-depol 0.05` |
| Export QASM | `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --export output.qasm` |
| Run with Shots | `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000` |

---

**Happy quantum computing! 🎉**


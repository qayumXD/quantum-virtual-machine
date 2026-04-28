# ⚡ QVM Quick Reference - All Commands at a Glance

**Last Updated:** April 28, 2026

---

## 🚀 Start Here (Most Common Commands)

```bash
# 1. Start Web UI (easiest way to get started)
python -m src.qvm.server --host 127.0.0.1 --port 8000
# Then open: http://127.0.0.1:8000/web

# 2. Run Bell State (simplest example)
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# 3. Run Tests (verify everything works)
python -m pytest tests/ -v

# 4. Run with Visualization
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

---

## 🌐 Web Server Commands

```bash
# Start server (default port 8000)
python -m src.qvm.server --host 127.0.0.1 --port 8000

# Start with auto-reload (development)
python -m src.qvm.server --host 127.0.0.1 --port 8000 --reload

# Start on different port
python -m src.qvm.server --host 127.0.0.1 --port 9000

# Check server health
curl http://127.0.0.1:8000/health

# Access dashboard
# Open browser: http://127.0.0.1:8000/web
```

---

## 💻 CLI Commands - Basic

```bash
# Run Bell State
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# Run Bernstein-Vazirani
python -m src.qvm.cli examples/bv_101.json --nqubits 4

# Run Grover's Algorithm
python -m src.qvm.cli examples/grover_101.json --nqubits 3

# Run QASM file
python -m src.qvm.cli examples/bell_state.qasm --nqubits 2
```

---

## 💻 CLI Commands - With Options

```bash
# With visualization
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize

# With sampling (1000 shots)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# With transpilation (greedy)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile

# With transpilation (SABRE - better)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre

# With noise (depolarizing)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --noise-depol 0.05

# With noise (readout)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --noise-readout 0.01

# With both noise types
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 \
  --noise-depol 0.05 --noise-readout 0.01

# Export to QASM
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --export output.qasm

# With random seed (reproducible)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 --seed 42

# Mid-circuit measurement
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --collapse

# Don't restore mapping after transpilation
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --no-restore-mapping
```

---

## 💻 CLI Commands - Combined Options

```bash
# Full example: transpile + visualize + sample + noise
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre --visualize --shots 1000 \
  --noise-depol 0.01 --noise-readout 0.01 --seed 42

# Bernstein-Vazirani with all options
python -m src.qvm.cli examples/bv_101.json --nqubits 4 \
  --transpile --routing sabre --shots 1000 --export bv_output.qasm

# Grover with noise simulation
python -m src.qvm.cli examples/grover_101.json --nqubits 3 \
  --shots 1000 --noise-depol 0.05 --noise-readout 0.02 --seed 123
```

---

## 🧪 Testing Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_simulator.py -v
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_transpiler.py -v
python -m pytest tests/test_api.py -v

# Run specific test
python -m pytest tests/test_simulator.py::test_bell_state -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run with output
python -m pytest tests/ -v -s

# Run tests matching pattern
python -m pytest tests/ -k "bell" -v

# Run tests excluding pattern
python -m pytest tests/ -k "not slow" -v
```

---

## 🔧 Algorithm Generation

```bash
# Generate Bernstein-Vazirani for secret "101"
python examples/generate_bv.py --secret 101 --output examples/bv_101.json

# Generate Bernstein-Vazirani for secret "110"
python examples/generate_bv.py --secret 110 --output examples/bv_110.json

# Generate Grover for target "101"
python examples/generate_grover.py --target 101 --output examples/grover_101.json

# Generate Grover for target "010"
python examples/generate_grover.py --target 010 --output examples/grover_010.json

# Cirq integration demo
python examples/cirq_to_ir_demo.py
```

---

## 📡 API Requests (cURL)

```bash
# Health check
curl http://127.0.0.1:8000/health

# Bell State (JSON)
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}],
    "nqubits": 2,
    "shots": 1000
  }'

# Bell State (QASM)
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "qasm",
    "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; h q[0]; cx q[0],q[1];",
    "shots": 1000
  }'

# With transpilation
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}],
    "nqubits": 2,
    "transpile": true,
    "routing": "sabre",
    "shots": 1000
  }'

# With noise
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}],
    "nqubits": 2,
    "shots": 1000,
    "noise_depol": 0.05,
    "noise_readout": 0.01
  }'
```

---

## 📊 Example Workflows

### Workflow 1: Quick Test
```bash
# 1. Start server
python -m src.qvm.server --host 127.0.0.1 --port 8000

# 2. In another terminal, run Bell State
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# 3. Open browser to http://127.0.0.1:8000/web
```

### Workflow 2: Full Testing
```bash
# 1. Run all tests
python -m pytest tests/ -v

# 2. Run specific algorithm
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000

# 3. Visualize results
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --visualize
```

### Workflow 3: Transpilation Study
```bash
# 1. Run without transpilation
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# 2. Run with greedy routing
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing greedy

# 3. Run with SABRE routing
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre

# 4. Export and compare
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre --export output.qasm
```

### Workflow 4: Noise Analysis
```bash
# 1. Ideal case (no noise)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# 2. With depolarizing noise
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 --noise-depol 0.05

# 3. With readout noise
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 --noise-readout 0.05

# 4. With both
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 \
  --noise-depol 0.05 --noise-readout 0.05
```

---

## 🎯 Common Patterns

### Pattern 1: Run and Visualize
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

### Pattern 2: Run with Sampling
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000
```

### Pattern 3: Transpile and Export
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre --export output.qasm
```

### Pattern 4: Realistic Simulation
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --shots 1000 --noise-depol 0.01 --noise-readout 0.01
```

### Pattern 5: Full Analysis
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre --visualize --shots 1000 \
  --noise-depol 0.01 --noise-readout 0.01 --export output.qasm
```

---

## 📁 File Locations

```
examples/
├── bell_state.json          # Bell state circuit
├── bell_state.qasm          # Bell state QASM
├── bv_101.json              # Bernstein-Vazirani
├── grover_101.json          # Grover's algorithm
├── generate_bv.py           # BV generator
└── generate_grover.py       # Grover generator

tests/
├── test_simulator.py        # Simulator tests
├── test_parser.py           # Parser tests
├── test_transpiler.py       # Transpiler tests
├── test_api.py              # API tests
└── ... (10+ more)

src/qvm/
├── cli.py                   # CLI entry point
├── server.py                # FastAPI server
├── parser.py                # JSON parser
├── qasm_parser.py           # QASM parser
├── simulator.py             # Statevector simulator
├── mps_simulator.py         # MPS simulator
├── transpiler.py            # Transpiler
└── ir.py                    # Internal representation
```

---

## 🔍 Troubleshooting Commands

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "pytest|numpy|matplotlib|fastapi"

# Check if port is in use
lsof -i :8000

# Run tests with verbose output
python -m pytest tests/ -v -s

# Check QASM syntax
python -c "from src.qvm.parser import QASMParser; print('OK')"

# List available examples
ls -la examples/

# View test results
python -m pytest tests/ -v --tb=short
```

---

## 📊 Output Interpretation

### Probabilities
```
[0.5, 0.0, 0.0, 0.5]
↓
|00⟩: 50%, |01⟩: 0%, |10⟩: 0%, |11⟩: 50%
```

### Counts
```json
{"00": 512, "11": 488}
↓
Out of 1000 shots: 512 measured |00⟩, 488 measured |11⟩
```

### Transpiled Operations
```json
[{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}]
↓
Gates after transpilation (may include SWAPs)
```

---

## ⚙️ Configuration

### Server Configuration
```bash
# Default
python -m src.qvm.server --host 127.0.0.1 --port 8000

# Custom host/port
python -m src.qvm.server --host 0.0.0.0 --port 9000

# Development mode
python -m src.qvm.server --host 127.0.0.1 --port 8000 --reload
```

### CLI Configuration
```bash
# Default (no options)
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# All options
python -m src.qvm.cli examples/bell_state.json --nqubits 2 \
  --transpile --routing sabre --visualize --shots 1000 \
  --seed 42 --noise-depol 0.01 --noise-readout 0.01 \
  --export output.qasm --collapse
```

---

## 🎓 Learning Path

1. **Start**: `python -m src.qvm.cli examples/bell_state.json --nqubits 2`
2. **Visualize**: Add `--visualize`
3. **Sample**: Add `--shots 1000`
4. **Transpile**: Add `--transpile --routing sabre`
5. **Add Noise**: Add `--noise-depol 0.01`
6. **Export**: Add `--export output.qasm`
7. **Try Algorithms**: Run BV and Grover examples
8. **Run Tests**: `python -m pytest tests/ -v`
9. **Use Web UI**: `python -m src.qvm.server --host 127.0.0.1 --port 8000`

---

## 💡 Pro Tips

- Use `--seed 42` for reproducible results
- Use `--routing sabre` for better transpilation
- Use `--visualize` to see circuit diagrams
- Use `--shots 1000` for realistic sampling
- Use `--noise-depol 0.01` to simulate real hardware
- Use `--export output.qasm` to save results
- Use `--collapse` for mid-circuit measurements
- Use `--transpile` for non-adjacent qubit gates

---

**Happy quantum computing! 🎉**


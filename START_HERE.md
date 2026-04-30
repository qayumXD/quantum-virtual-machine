# 🚀 START HERE - Quantum Virtual Machine Quick Start

**Welcome!** This is your entry point to the Quantum Virtual Machine (QVM).

---

## ⚡ 5-Minute Quick Start

### Step 1: Start the Web Server
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
```

### Step 2: Open Dashboard
Open your browser and go to: **http://127.0.0.1:8000/web**

### Step 3: Run Bell State
- Keep the default Bell State JSON
- Set shots to 1000
- Click "Run"
- See the results!

**That's it! You've run your first quantum circuit! 🎉**

---

## 📚 Documentation Files

I've created **4 comprehensive guides** for you:

### 1. 📖 **COMPLETE_USAGE_GUIDE.md** (Main Reference)
**What:** Everything you need to know  
**Length:** ~17KB  
**Contains:**
- Quick start instructions
- Web interface guide
- CLI commands with examples
- Testing procedures
- Transpilation explained
- Visualization guide
- Algorithm examples

**👉 Read this when:** You want comprehensive instructions

---

### 2. 🔬 **CODE_EXAMPLES_AND_EXPLANATIONS.md** (Deep Dive)
**What:** Code examples with detailed explanations  
**Length:** ~16KB  
**Contains:**
- Bell State (JSON & OpenQASM 3.0)
- Bernstein-Vazirani Algorithm (JSON & OpenQASM 3.0)
- Grover's Search Algorithm (JSON & OpenQASM 3.0)
- Advanced examples
- API request examples
- Output interpretation

**👉 Read this when:** You want to understand the code and algorithms

---

### 3. ⚡ **QUICK_REFERENCE.md** (Cheat Sheet)
**What:** All commands at a glance  
**Length:** ~12KB  
**Contains:**
- Most common commands
- CLI commands by category
- Testing commands
- API requests
- Example workflows
- Common patterns
- Troubleshooting

**👉 Read this when:** You need quick command reference

---

### 4. 📋 **README_USAGE_SUMMARY.md** (Navigation Guide)
**What:** Overview and navigation  
**Length:** ~12KB  
**Contains:**
- Documentation overview
- Navigation guide
- Quick command reference
- Learning paths
- File structure
- Pro tips

**👉 Read this when:** You're new and need orientation

---

## 🎯 Choose Your Path

### 👶 I'm a Beginner
1. Read: **QUICK_REFERENCE.md** → "Start Here" section (5 min)
2. Run: `python -m src.qvm.server --host 127.0.0.1 --port 8000` (30 sec)
3. Open: http://127.0.0.1:8000/web (10 sec)
4. Try: Run Bell State example (1 min)
5. Read: **CODE_EXAMPLES_AND_EXPLANATIONS.md** → "Bell State" section (10 min)

**Total time: ~30 minutes**

---

### 👨‍💻 I'm Intermediate
1. Read: **COMPLETE_USAGE_GUIDE.md** → "Quick Start" (10 min)
2. Run: Bell State, BV, and Grover examples (10 min)
3. Read: **CODE_EXAMPLES_AND_EXPLANATIONS.md** → All algorithms (20 min)
4. Try: Add `--visualize` and `--shots 1000` (5 min)
5. Run: `python -m pytest tests/ -v` (5 min)

**Total time: ~1 hour**

---

### 🧠 I'm Advanced
1. Read: All 4 documentation files (1 hour)
2. Run: All examples with various options (30 min)
3. Try: Transpilation and noise simulation (30 min)
4. Try: API requests with cURL (20 min)
5. Explore: Source code in `src/qvm/` (1 hour)

**Total time: ~3 hours**

---

## 🚀 Most Common Commands

```bash
# Start Web UI (easiest)
python -m src.qvm.server --host 127.0.0.1 --port 8000

# Run Bell State (simplest)
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# Run with visualization
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize

# Run with sampling (1000 shots)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# Run tests
python -m pytest tests/ -v

# Run Bernstein-Vazirani
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000

# Run Grover's Algorithm
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --shots 1000

# Transpile circuit
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre

# Add noise
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000 --noise-depol 0.05

# Export to QASM
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --export output.qasm
```

---

## 📊 What Can You Do?

### 🌐 Web Interface
- Interactive dashboard
- Compose circuits visually
- Run simulations
- View results in real-time

### 💻 Command Line
- Run quantum circuits
- Transpile for hardware
- Add noise simulation
- Visualize results
- Export to QASM

### 🧪 Testing
- Run full test suite
- Test specific components
- Check coverage
- Verify functionality

### 🔄 Transpilation
- Map circuits to hardware
- Use greedy or SABRE routing
- Reduce SWAP gates
- Restore qubit mapping

### 📊 Visualization
- Circuit diagrams
- Probability histograms
- State vectors
- Measurement results

---

## 📝 Example Circuits

### Bell State (Entanglement)
```json
[
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]}
]
```
**Result:** 50% |00⟩, 50% |11⟩

### Bernstein-Vazirani (Find Secret)
```bash
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000
```
**Result:** Finds hidden bitstring "101"

### Grover's Algorithm (Search)
```bash
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --shots 1000
```
**Result:** Searches for item "101" with ~94% probability

---

## 🎓 Learning Resources

### In the Documentation
- **COMPLETE_USAGE_GUIDE.md** → Algorithm explanations
- **CODE_EXAMPLES_AND_EXPLANATIONS.md** → Detailed code walkthroughs
- **QUICK_REFERENCE.md** → Command examples

### In the Repository
- `docs/algorithms/` → Algorithm documentation
- `docs/guides/` → Usage guides
- `examples/` → Example circuits
- `tests/` → Test examples

---

## 🔧 Troubleshooting

### Server won't start?
```bash
# Check if port is in use
lsof -i :8000

# Use different port
python -m src.qvm.server --host 127.0.0.1 --port 9000
```

### Tests fail?
```bash
# Run with verbose output
python -m pytest tests/ -v -s
```

### Visualization not showing?
```bash
# Set matplotlib backend
export MPLBACKEND=TkAgg
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

---

## 📞 Quick Help

| I want to... | Command | File |
|-------------|---------|------|
| Start the app | `python -m src.qvm.server --host 127.0.0.1 --port 8000` | QUICK_REFERENCE.md |
| Run Bell State | `python -m src.qvm.cli examples/bell_state.json --nqubits 2` | QUICK_REFERENCE.md |
| Understand Bell State | Read "Bell State" section | CODE_EXAMPLES_AND_EXPLANATIONS.md |
| Run tests | `python -m pytest tests/ -v` | QUICK_REFERENCE.md |
| Transpile circuit | Add `--transpile --routing sabre` | COMPLETE_USAGE_GUIDE.md |
| Add noise | Add `--noise-depol 0.05` | QUICK_REFERENCE.md |
| Learn Grover | Read "Grover's Search" section | CODE_EXAMPLES_AND_EXPLANATIONS.md |
| Use API | See cURL examples | CODE_EXAMPLES_AND_EXPLANATIONS.md |

---

## 🎯 Next Steps

### Right Now (5 minutes)
1. Run: `python -m src.qvm.server --host 127.0.0.1 --port 8000`
2. Open: http://127.0.0.1:8000/web
3. Try: Bell State example

### In 30 Minutes
1. Read: QUICK_REFERENCE.md
2. Run: Bell State with `--visualize`
3. Run: Bell State with `--shots 1000`

### In 1 Hour
1. Read: CODE_EXAMPLES_AND_EXPLANATIONS.md
2. Run: Bernstein-Vazirani example
3. Run: Grover's algorithm example
4. Run: `python -m pytest tests/ -v`

### In 3 Hours
1. Read: All documentation files
2. Try: All examples with various options
3. Try: Transpilation and noise
4. Try: API requests

---

## 📚 File Structure

```
quantum-virtual-machine/
├── START_HERE.md                    ← You are here!
├── QUICK_REFERENCE.md               ← Quick commands
├── COMPLETE_USAGE_GUIDE.md          ← Full guide
├── CODE_EXAMPLES_AND_EXPLANATIONS.md ← Code examples
├── README_USAGE_SUMMARY.md          ← Navigation
│
├── src/qvm/                         ← Source code
├── examples/                        ← Example circuits
├── tests/                           ← Test suite
└── docs/                            ← Documentation
```

---

## ✨ You're All Set!

Everything is ready to use. All dependencies are installed.

**Choose your next step:**

- 👶 **Beginner?** → Read QUICK_REFERENCE.md
- 👨‍💻 **Intermediate?** → Read COMPLETE_USAGE_GUIDE.md
- 🧠 **Advanced?** → Read CODE_EXAMPLES_AND_EXPLANATIONS.md
- 🤔 **Need help?** → Read README_USAGE_SUMMARY.md

---

## 🎉 Happy Quantum Computing!

**Let's get started!**

```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
```

Then open: **http://127.0.0.1:8000/web**

---

**Created:** April 28, 2026  
**Status:** Ready to use  
**All dependencies:** Installed ✅


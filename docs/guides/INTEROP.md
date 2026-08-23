# QVM Interoperability Guide

How QVM exchanges circuits with Qiskit, Cirq, OpenQASM, and JSON — and the
guarantees that make those exchanges trustworthy.

## The pivot principle

QVM does not implement pairwise converters. Every format converts to the QVM
IR (`qvm.ir.QuantumCircuit`), and every format converts back out of it:

```
        ──► IR ──►            N source formats + M target formats
Qiskit ─┐         ┌─► Qiskit    require N + M converters,
Cirq  ──┤   IR    ├──► Cirq     not N × M.
JSON  ──┤         ├──► JSON
QASM  ──┘         └─► QASM
```

The cross-framework bridges are compositions of this rule:

```python
from qvm.ir import QuantumCircuit
QuantumCircuit.cirq_to_qiskit(cr)   # from_cirq → to_qiskit
QuantumCircuit.qiskit_to_cirq(qk)   # from_qiskit → to_cirq
```

## The two guarantees

### 1. No silent drops

A conversion has exactly two possible outcomes:

- **Success** — every operation was mapped faithfully.
- **`UnsupportedGateError` / `QVMConversionError`** — raised with the gate
  name and the list of supported gates.

Nothing is ever skipped. If `to_qiskit()` returns a circuit containing 12
instructions, your input had 12 instructions.

### 2. Physical equivalence

Converted circuits reproduce QVM's measurement probability distribution.
This is enforced by tests that run the *same* circuit through the QVM
statevector engine, Qiskit's statevector, and Cirq's simulator and assert
agreement to floating-point tolerance for **every gate in the vocabulary**,
using irregular rotation angles so unitary-convention mistakes cannot hide.

## Supported gate vocabulary

| QVM | Qiskit | Cirq | Notes |
|---|---|---|---|
| `h x y z` | same | same | |
| `s sdg t tdg` | same | `S`, `S†`, `T`, `T†` | Cirq pow-gate fractions keep their names on import |
| `sx sxdg` | same | `X**0.5`, `X**-0.5` | differs from Cirq by global phase only |
| `id` | `id` | `I` | |
| `rx ry rz` | same | `rx ry rz` | phase-exact both directions |
| `p(λ)` | `p(λ)` | `Z**(λ/π)` | up to global phase in Cirq |
| `cx cz swap` | same | `CNOT CZ SWAP` | |
| `rxx(θ) rzz(θ)` | same | `XXPowGate ZZPowGate` | exponent θ/π; phase-exact |
| `cp(λ)` | `cp(λ)` | `CZPowGate(λ/π)` | phase-exact |
| `ccx` | `ccx` | `TOFFOLI` | |
| `measure` | `measure` | `measure` | see key format below |
| `barrier` | `barrier` | identity ops per wire | Cirq has no barrier primitive; identities preserve moment ordering |
| `delay` | `delay(ns)` | `wait(nanos=…)` | whole-nanosecond durations only |

Arbitrary exponents import as continuous rotations with recovered angles:
`XPowGate(e)` → `rx(π·e)`, `ZPowGate(e)` → `rz(π·e)`, etc. Canonical
fractions keep their named gates (`Z**0.25` → `t`).

## What deliberately fails

| Input | Behavior |
|---|---|
| Control flow (`label`, `jump`) export | `UnsupportedGateError` — flatten loops first |
| Classical register arithmetic export | `UnsupportedGateError` |
| Unknown/foreign gate (arbitrary unitaries, `ISWAP`, pulse ops…) | `UnsupportedGateError` naming the gate + supported set |
| Partially-bound symbolic expression export | `QVMConversionError` suggesting `bind_parameters()` |
| Multi-qubit Cirq measurement | `QVMConversionError` (IR maps one qubit → one classical bit per measure) |

**Multi-controlled gates are lowered automatically** during import:
`mcx`, `mcx_gray`, `c3x`, `c4x`, `ccz`/`mcz`, `mcphase`/`mcu1`, `mcry`,
`mcrz`, `mcrx` map onto exact basis-gate constructions (half-angle CX
recursions + projector split; validated against Qiskit's reference
unitaries for up to 5 controls).

For anything else foreign you can transpile onto the basis set yourself:

```python
from qiskit import transpile
basis = ["h", "x", "rx", "rz", "p", "cx", "cz", "swap", "cp", "ccx", "sx"]
qk_ready = transpile(qk_big, basis_gates=basis, optimization_level=0)
qc = QuantumCircuit.from_qiskit(qk_ready)
```

## Parameters

Symbolic parameters survive conversion symbolically:

| Direction | Mapping |
|---|---|
| QVM → Qiskit | `Parameter("theta")` → `qiskit.circuit.Parameter("theta")` |
| QVM → Cirq | `Parameter("theta")` → `sympy.Symbol("theta")` |
| Qiskit → QVM | plain `Parameter` → QVM `Parameter`; numeric expressions → float |
| Cirq → QVM | single-symbol angle → QVM `Parameter`; linear `c·θ+b` → `ParameterExpression` |

Bound expressions (`2*θ+1` with θ bound) export as floats. Partially-bound
expressions raise until resolved — exporting a circuit you cannot execute
would violate guarantee #1 in spirit.

## Measurement keys (Cirq)

Exports use canonical `"register[index]"` keys:

```python
qc.add_operation("measure", [3], target_bit=("m", 7))   # → cirq key "m[7]"
```

Imports additionally accept legacy tuple-strings `"('m', 7)"` and bare
integer keys. `run_cirq_simulator()` orders output bitstrings by parsed
`(register, index)`, not lexicographically.

## Global phase

The IR stores gates, not global phase. Conversions therefore preserve all
*observable* behavior while possibly shifting the global phase of the final
statevector (e.g. `sx`). This matches OpenQASM's own convention and is
invisible to measurement statistics. The equivalence tests compare
probability distributions for exactly this reason.

## Error taxonomy

```text
QVMError
├── QVMParseError                (also ValueError)
├── QVMCompilationError          (also ValueError)
│   ├── UnsupportedGateError
│   └── QVMConversionError
├── MissingBackendError          (also ImportError)
└── QVMRuntimeError              (also RuntimeError)
    └── QVMResourceLimitError
```

Catch `QVMError` for blanket handling; catch the leaves for recovery logic.
The built-in parents mean legacy code using `except ValueError` keeps
working unchanged.

## Recipes

**Cross-validate QVM against Aer:**

```python
from collections import Counter

qc = ...                                        # any QuantumCircuit with measures
mine = Counter(Simulator().sample(qc, shots=4096, seed=1))
theirs = qc.run_qiskit_simulator(shots=4096)    # requires [qiskit] extra
```

**Round-trip integrity check:**

```python
back = QuantumCircuit.from_qiskit(qc.to_qiskit())
assert [ (o["name"], o["qubits"]) for o in back.operations ] == \
       [ (o["name"], o["qubits"]) for o in qc.operations ]
```

**Install-time capability probe:**

```python
try:
    qc.to_qiskit()
except MissingBackendError as e:
    print(e)      # "pip install 'quantum-virtual-machine[qiskit]'"
```

# Comprehensive Technical Analysis: QVM Parser & Front-End Compiler

**Author:** Explorer Specialist (Front-End Compiler & Parser Investigation)  
**Date:** 2026-08-23  
**Target Repository:** `/home/qayum/projects/quantum-virtual-machine`  

---

## Executive Summary

The Quantum Virtual Machine (QVM) front-end compiler pipeline provides multi-format parsing capabilities across OpenQASM 3.0 (via Lark LALR parsing), OpenQASM 2.0 (via manual string splitting), JSON gate lists, and Python framework AST converters (Qiskit and Cirq). While functional for basic educational examples and small benchmarks (< 100 operations), the current front-end compiler exhibits critical architectural bottlenecks, severe syntax validation gaps, semantic discrepancies in control flow execution, memory inefficiencies, and dual-IR fragmentation that prevent it from functioning as a robust, production-grade compiler for 1,000+ to 100,000+ line quantum programs.

Key highlights:
- **Parser Throughput & Latency**: Lark-based OpenQASM 3.0 parser achieves ~8,800 to 9,500 operations/sec throughput (~112 ms for 1,000 operations; 1.14 s for 10,000 operations). However, every API request in `api/app.py` and programmatic call in `ir.py:from_qasm` re-reads the `.lark` file from disk and reconstructs the parser, adding an unnecessary ~30 ms static latency overhead per parse.
- **Dual IR Fragmentation**: The repository contains two incompatible Intermediate Representations: `src/ir.py` (`QuantumGate` dataclass and `QuantumCircuitIR`) used by legacy scripts, and `src/qvm/ir.py` (`QuantumCircuit` using untyped 9-key dictionaries) used by the simulator and CLI.
- **Critical Semantic & Validation Bugs**:
  1. *Classical Register Declaration Order Bug* (`qasm3_parser.py:40-44`): If `bit` declarations precede `qubit` declarations in OpenQASM 3.0, classical registers are silently ignored, causing condition checks to throw runtime errors.
  2. *Qubit Register Bounds Check Bypass* (`qasm3_parser.py:58-60`): Accessing out-of-bounds qubit indices across multiple registers silently aliases onto subsequent registers without error.
  3. *Missing Qubit Arity Validation in IR* (`ir.py:67-98`): `GATE_SPEC` only validates parameter counts, not qubit arity, allowing invalid 1-qubit `cx` or 2-qubit `ccx` operations to pass compilation and crash at simulator runtime.
  4. *Symbolic Parameter Parsing Rejection* (`qasm3_parser.py:53`, `ir.py:91-95`): `OpenQASM3Parser` returns raw string identifiers for gate parameters, which `QuantumCircuit.add_operation` rejects as invalid types, rendering symbolic OpenQASM 3.0 circuits unparseable.
  5. *While-Loop Semantics Mismatch* (`qasm3_parser.py:130-140`): Compiles into `LABEL -> BODY -> JUMP IF cond`, resulting in `do-while` semantics (the body is always executed at least once even if the condition is false initially).
  6. *For-Loop Parse-Time Unrolling & Memory Explosion* (`qasm3_parser.py:121-128`): For-loops ignore iteration variables and are eagerly unrolled at parse time into flat gate lists (a 50,000 iteration loop creates 100,000 dictionary objects and consumes 44.5 MB RAM).
  7. *Fragile OpenQASM 2.0 Lexing* (`parser.py:124-148`): Missing comma separators (e.g. `cx q[0] q[1];`) are silently parsed into single-qubit gates.
- **Error Diagnostics & Streaming**: Error messages lack source file line numbers, column numbers, visual code context, and synchronization tokens for error recovery. The entire compilation pipeline is batch-only with no streaming or chunked parsing support.

---

## 1. Architectural Overview & Component Inventory

### 1.1 Front-End Entry Points and Parsers

The QVM ingestion pipeline consists of five distinct parsing paths:

| Parser Component | File Path | Ingestion Format | Target IR | Primary Use Case |
|---|---|---|---|---|
| **OpenQASM3Parser** | `src/qvm/qasm3_parser.py`<br>`src/qvm/qasm3.lark` | OpenQASM 3.0 Text | `src.qvm.ir.QuantumCircuit` | CLI (`--input_file *.qasm`), API (`/run` with `source_type=qasm`), `QuantumCircuit.from_qasm()` |
| **OpenQASM2Parser** | `src/qvm/parser.py:47-98` | OpenQASM 2.0 Text | `src.qvm.ir.QuantumCircuit` | CLI (fallback for non-QASM3 `.qasm` files), API (`/run`) |
| **QASMParser** | `src/qvm/parser.py:10-45` | JSON List of Dicts | `src.qvm.ir.QuantumCircuit` | CLI (`--input_file *.json`), API (`/run` with `source_type=json`) |
| **Framework Converters** | `src/qvm/ir.py:235-384` | Qiskit / Cirq Python Objects | `src.qvm.ir.QuantumCircuit` | Programmatic backend cross-conversion |
| **Legacy Parsers** | `src/parser.py:31-183` | Qiskit / Cirq Python Objects | `src.ir.QuantumCircuitIR` | `examples_bell_state_parser_demo.py`, `tests/test_cirq_parser.py` |

```
                              ┌────────────────────────┐
                              │ Input Circuit Source   │
                              └───────────┬────────────┘
                                          │
        ┌───────────────────┬─────────────┴───────┬───────────────────┐
        ▼                   ▼                     ▼                   ▼
┌───────────────┐   ┌───────────────┐     ┌───────────────┐   ┌───────────────┐
│ OpenQASM 3.0  │   │ OpenQASM 2.0  │     │   JSON Body   │   │ Qiskit / Cirq │
│  (qasm3.lark) │   │ (parser.py)   │     │  (parser.py)  │   │   (ir.py)     │
└───────┬───────┘   └───────┬───────┘     └───────┬───────┘   └───────┬───────┘
        │                   │                     │                   │
        │ (Lark LALR)       │ (ad-hoc string)     │ (dict validation) │ (object AST)
        ▼                   ▼                     ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       src.qvm.ir.QuantumCircuit                             │
│       - num_qubits: int                                                     │
│       - classical_registers: Dict[str, int]                                 │
│       - operations: List[Dict[str, Any]] (9-key untyped dicts)              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │ src.qvm.decomposer        │             │ src.qvm.transpiler        │
   │ (Gate Decomposition)      │             │ (Greedy / SABRE Routing)  │
   └─────────────┬─────────────┘             └─────────────┬─────────────┘
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ src.qvm.simulator         │
                        │ (Statevector / MPS)       │
                        └───────────────────────────┘
```

---

## 2. Language Grammar & Instruction Format Analysis

### 2.1 OpenQASM 3.0 Grammar (`src/qvm/qasm3.lark`)

The Lark grammar file (`src/qvm/qasm3.lark`) implements a minimal subset of the official OpenQASM 3.0 specification:

```lark
// src/qvm/qasm3.lark (Lines 4-57)
start: "OPENQASM" "3.0" ";" program
program: statement*
?statement: declaration | gate_call | delay_call | measurement | assignment 
          | if_statement | for_loop | while_loop | comment

declaration: "qubit" "[" INT "]" CNAME ";"  -> qubit_decl
           | "bit" "[" INT "]" CNAME ";"    -> bit_decl
           | "bit" CNAME ";"               -> bit_single_decl

gate_call: CNAME ["(" arguments ")"] qubit_list ";"
arguments: expression ("," expression)*
qubit_list: qubit ("," qubit)*
qubit: CNAME "[" INT "]"

delay_call: "delay" "[" duration "]" qubit_list ";"
duration: NUMBER CNAME

measurement: bit_index "=" "measure" qubit ";"
assignment: bit_index "=" boolean_expr ";"
?boolean_expr: bit_index | INT | boolean_expr "&" boolean_expr -> and_expr
             | boolean_expr "|" boolean_expr -> or_expr
             | boolean_expr "^" boolean_expr -> xor_expr
             | "~" boolean_expr              -> not_expr
             | "(" boolean_expr ")"

bit_index: CNAME "[" INT "]" -> bit_idx | CNAME -> bit_name
if_statement: "if" "(" condition ")" "{" program "}"
for_loop: "for" CNAME "in" range "{" program "}"
range: "[" INT ":" INT "]"
while_loop: "while" "(" condition ")" "{" program "}"
condition: CNAME "[" INT "]" "==" INT -> cond_indexed | CNAME "==" INT -> cond_simple
?expression: NUMBER | CNAME
comment: "//" /[^\n]+/
```

#### Major Specification Gaps in `qasm3.lark`:
1. **No Subroutines or Custom Gates**: The grammar lacks `gate name(...) q0, q1 { ... }` and `def subroutine(...) { ... }`.
2. **Missing Gate Modifiers**: `ctrl @`, `negctrl @`, `inv @`, `pow(k) @` modifiers are unsupported.
3. **No Header Includes**: `include "stdgates.inc";` is absent. Any OpenQASM 3.0 file containing standard includes throws a syntax error.
4. **No Primitive Type Declarations or Constants**: Missing `float[64]`, `angle[32]`, `int[32]`, `uint[32]`, `const`, `input`, and `output`.
5. **No Parameter Arithmetic Expressions**: `arguments: expression ("," expression)*` where `?expression: NUMBER | CNAME`. Arithmetic expressions such as `rx(pi/2) q[0];` or `rz(theta + 0.5) q[0];` fail with `UnexpectedToken`.
6. **No Array/Register Slicing or Broad Casts**: Cannot apply gates across entire registers (`h q;`) or slices (`q[0:2]`).
7. **No Loop Variable References in Qubit Indexing**: `qubit: CNAME "[" INT "]"` strictly requires an integer token (`INT`). Dynamic indexing like `for i in [0:4] { x q[i]; }` fails because `i` is a `CNAME`, not `INT`.
8. **No Rich Boolean Predicates**: Conditions only support equality `==` against integer literals (`CNAME "==" INT`). Relational operators (`<`, `>`, `<=`, `>=`, `!=`) and logical connectives (`&&`, `||`, `!`) in condition headers are not permitted.
9. **Missing Circuit Control Directives**: `barrier`, `reset`, `delay` without duration units, `break`, `continue`, `return`, `switch/case`.

### 2.2 OpenQASM 2.0 Parser (`src/qvm/parser.py:47-148`)

The `OpenQASM2Parser` is implemented as an ad-hoc line-by-line string scanner:

```python
# src/qvm/parser.py:61-98
@staticmethod
def parse(text: str) -> QuantumCircuit:
    lines = []
    for raw in text.splitlines():
        stripped = raw.split("//")[0].strip()
        if stripped:
            lines.append(stripped.rstrip(";"))

    if not lines or not lines[0].lower().startswith("openqasm"):
        raise ValueError("Missing OPENQASM header")
    ...
```

#### Defects in `OpenQASM2Parser`:
1. **Limited Hardcoded Gate Set (`parser.py:52`)**:
   ```python
   SUPPORTED_GATES = {"h", "x", "y", "z", "rx", "ry", "rz", "cx", "swap", "id"}
   ```
   Standard OpenQASM 2.0 gates `cz`, `ccx`, `toffoli`, `s`, `sdg`, `t`, `tdg`, `p`, `u1`, `u2`, `u3` are missing and throw `ValueError: Unsupported gate: <name>`.
2. **Classical Registers Ignored (`parser.py:84-86`)**:
   ```python
   if line.lower().startswith("creg"):
       # creg ignored for now
       continue
   ```
   `creg` statements are silently discarded; classical registers are never initialized.
3. **Measurement Target Bits Ignored (`parser.py:87-90`)**:
   ```python
   if line.lower().startswith("measure"):
       q, c = OpenQASM2Parser._parse_measure(line)
       qc.add_operation("measure", [q], [])
       continue
   ```
   While `_parse_measure` extracts classical bit `c`, `qc.add_operation` is called without `target_bit`. The classical destination bit is lost.
4. **Single Parameter Restriction & No Constant Evaluation (`parser.py:124-138`)**:
   Only single parameters in parentheses (`rz(1.57) q[0]`) are parsed via `float(param_str)`. Multiple parameters (`u3(0.1, 0.2, 0.3)`) or constants (`pi/2`) crash with `ValueError`.
5. **Token Separator Fragility (`parser.py:136-138`)**:
   ```python
   qubit_tokens = rest.replace(" ", "").split(",")
   qubits = [OpenQASM2Parser._parse_qubit(tok) for tok in qubit_tokens]
   ```
   If a user writes `cx q[0] q[1];` (missing comma), `rest.replace(" ", "")` merges the string into `q[0]q[1]`. `_parse_qubit` parses `q[0]` and returns `[0]`, silently dropping `q[1]`.

---

## 3. Deep-Dive: Syntax Validation, AST Construction & Semantic Defects

### 3.1 Defect 1: Classical Register Declaration Ordering Bug
- **Location**: `src/qvm/qasm3_parser.py:32-47`
- **Code Reference**:
  ```python
  def _find_declarations(self, node):
      if not isinstance(node, Tree): return
      if node.data == "qubit_decl":
          size, name = int(node.children[0]), str(node.children[1])
          self.qubit_map[name] = (self.next_qubit_idx, size)
          self.next_qubit_idx += size
          if self.qc is None: self.qc = QuantumCircuit(self.next_qubit_idx)
          else: self.qc.num_qubits = self.next_qubit_idx
      elif node.data == "bit_decl":
          if self.qc: self.qc.add_classical_register(str(node.children[1]), int(node.children[0]))
      elif node.data == "bit_single_decl":
          if self.qc: self.qc.add_classical_register(str(node.children[0]), 1)
  ```
- **Mechanism**: If `bit[2] c;` appears in the source file before `qubit[2] q;`, `self.qc` is still `None`. The check `if self.qc:` evaluates to `False`, silently dropping the classical register declaration.
- **Consequence**: When conditional operations or measurements later reference register `c`, `QuantumCircuit.add_operation` throws `ValueError: Unknown classical register in condition: c`.
- **Reproduction**:
  ```qasm
  OPENQASM 3.0;
  bit[2] c;
  qubit[2] q;
  h q[0];
  c[0] = measure q[0];
  if (c[0] == 1) { x q[1]; }
  ```
  Result: `ValueError: Unknown classical register in condition: c`.

### 3.2 Defect 2: Multi-Register Qubit Bounds Check Bypass
- **Location**: `src/qvm/qasm3_parser.py:58-60`
- **Code Reference**:
  ```python
  if node.data == "qubit":
      name, idx = str(node.children[0]), int(node.children[1])
      return self.qubit_map[name][0] + idx
  ```
- **Mechanism**: `self.qubit_map[name]` stores `(offset, size)`. When resolving `q[idx]`, the parser computes `offset + idx` without asserting `0 <= idx < size`.
- **Consequence**: In a multi-register program (`qubit[2] q; qubit[4] r;`), an invalid instruction `h q[5];` computes physical qubit $0 + 5 = 5$. Since the circuit has 6 total qubits, this silently maps to physical qubit 5 (which is actually `r[3]`), corrupting program semantics without throwing any compile-time or parse-time error.

### 3.3 Defect 3: Missing Qubit Arity Validation in IR
- **Location**: `src/qvm/ir.py:67-98`
- **Code Reference**:
  ```python
  GATE_SPEC = {
      "h": 0, "x": 0, "y": 0, "z": 0,
      "cx": 0, "cz": 0, "swap": 0, "ccx": 0, "toffoli": 0,
      "id": 0, "sx": 0, "sxdg": 0, "s": 0, "sdg": 0, "t": 0, "tdg": 0,
      "rx": 1, "ry": 1, "rz": 1, "p": 1,
      "rxx": 1, "rzz": 1, "cp": 1,
      "measure": 0,
  }
  ```
- **Mechanism**: `GATE_SPEC` stores expected *parameter counts* (e.g. `cx: 0` means 0 parameters). It contains no specification for *qubit arity* (e.g. `cx` requires 2 qubits, `ccx` requires 3 qubits, `h` requires 1 qubit).
- **Consequence**: An operation like `qc.add_operation("cx", [0], [])` passes IR construction without error. Validation is deferred until runtime simulation, where the engine crashes with `ValueError: Gate cx must act on two qubits`.

### 3.4 Defect 4: Disconnection with Symbolic Parameter System
- **Location**: `src/qvm/qasm3_parser.py:50-55`, `src/qvm/ir.py:91-95`
- **Code Reference**:
  ```python
  # qasm3_parser.py:50-54
  if isinstance(node, Token):
      if node.type == "INT": return int(node)
      if node.type == "NUMBER": return float(node)
      if node.type == "CNAME": return str(node)
      return node

  # ir.py:91-95
  for p_val in params:
      if not isinstance(p_val, (int, float, Parameter, ParameterExpression)):
          raise ValueError(
              f"Parameter values must be int, float, Parameter, or ParameterExpression. "
              f"Got: {type(p_val)}"
          )
  ```
- **Mechanism**: When a parameterized OpenQASM 3.0 gate `rx(theta) q[0];` is parsed, Lark evaluates `theta` as a `str` (`"theta"`). When passed to `add_operation`, `ir.py` rejects `str`, raising `ValueError: Parameter values must be int, float, Parameter, or ParameterExpression. Got: <class 'str'>`.
- **Consequence**: Despite having a full symbolic parameter system in `src/qvm/parameter.py`, parameterized circuits cannot be loaded via the OpenQASM 3.0 parser.

### 3.5 Defect 5: Semantic Inversion in While-Loop Compilation
- **Location**: `src/qvm/qasm3_parser.py:130-140`
- **Code Reference**:
  ```python
  elif node.data == "while_loop":
      condition = self._evaluate(node.children[0])
      program_block = node.children[1]
      label_id = self._label_counter
      self._label_counter += 1
      start_label = f"while_start_{label_id}"
      self.qc.add_operation("label", [], label=start_label)
      for stmt in program_block.children:
          self._process_node(stmt, current_condition)
      self.qc.add_operation("jump", [], condition=condition, jump_to=start_label)
      return
  ```
- **Mechanism**: The compiler emits a loop label, emits all body operations, and then places a conditional jump back to the start label at the end.
- **Consequence**: This generates `do { body } while (condition)` semantics instead of `while (condition) { body }` semantics. If the condition is false initially (e.g. `while (c[0] == 1)` when `c[0] == 0`), the body is unconditionally executed once in iteration 0.

---

## 4. Algorithmic Complexity, Memory Allocation & Scalability

### 4.1 Benchmark Profile: 100 to 10,000 Line Quantum Programs

To assess scalability on large-scale circuits, benchmarking was performed across OpenQASM 3.0, OpenQASM 2.0, and JSON ingestion paths using Python 3.14 on Linux:

| Program Size (Lines) | QASM 3.0 Parse Time | QASM 3.0 Peak RAM | QASM 2.0 Parse Time | QASM 2.0 Peak RAM | JSON Parse Time | JSON Peak RAM | QASM 3 Throughput |
|---|---|---|---|---|---|---|---|
| **100 ops** | 14.80 ms | 0.21 MB | 2.31 ms | 0.05 MB | 1.38 ms | 0.03 MB | 6,756 ops/sec |
| **500 ops** | 52.87 ms | 0.97 MB | 11.60 ms | 0.25 MB | 6.72 ms | 0.15 MB | 9,457 ops/sec |
| **1,000 ops** | 112.57 ms | 1.97 MB | 23.03 ms | 0.50 MB | 14.65 ms | 0.30 MB | 8,883 ops/sec |
| **2,500 ops** | 264.64 ms | 4.89 MB | 57.22 ms | 1.01 MB | 28.48 ms | 0.60 MB | 9,447 ops/sec |
| **5,000 ops** | 523.63 ms | 9.82 MB | 134.05 ms | 2.55 MB | 78.54 ms | 1.51 MB | 9,549 ops/sec |
| **10,000 ops** | 1,144.72 ms | 19.65 MB | 275.10 ms | 5.12 MB | 162.20 ms | 3.05 MB | 8,736 ops/sec |

```
Time Complexity:   O(N) linear time for single-pass/tree-traversal parsing
Space Complexity:  O(N) linear memory allocation
Peak Memory at 10k lines: ~19.65 MB for AST Tree + IR Dictionaries
```

### 4.2 Re-Instantiation Latency Bottleneck in API & IR
- **Location**: `api/app.py:318`, `src/qvm/ir.py:231`
- **Code Reference**:
  ```python
  # api/app.py:318
  if "OPENQASM 3" in req.qasm.upper():
      parser3 = OpenQASM3Parser()
      return parser3.parse(req.qasm)

  # src/qvm/ir.py:231
  @classmethod
  def from_qasm(cls, qasm_str: str) -> "QuantumCircuit":
      from src.qvm.qasm3_parser import OpenQASM3Parser
      parser = OpenQASM3Parser()
      return parser.parse(qasm_str)
  ```
- **Profiling Measurements**:
  - `OpenQASM3Parser.__init__` time (disk I/O + Lark LALR compilation): **30.60 ms**
  - `OpenQASM3Parser.parse` time for standard 5-qubit circuit: **1.74 ms**
  - **Overhead Factor**: **17.5x latency penalty** on every HTTP request and programmatic parse because the parser object is not cached/reused at the module level.

### 4.3 For-Loop Parse-Time Unrolling & Memory Explosion
- **Location**: `src/qvm/qasm3_parser.py:121-128`
- **Code Reference**:
  ```python
  elif node.data == "for_loop":
      start_val = int(node.children[1].children[0])
      end_val = int(node.children[1].children[1])
      program_block = node.children[2]
      for _ in range(start_val, end_val):
          for stmt in program_block.children:
              self._process_node(stmt, current_condition)
      return
  ```
- **Benchmark of Unrolling Memory Footprint**:

| Loop Iterations | Source Code Lines | Generated IR Operations | Parse Time | Peak Memory |
|---|---|---|---|---|
| **100 iters** | 8 lines | 200 operations | 7.95 ms | 0.11 MB |
| **1,000 iters** | 8 lines | 2,000 operations | 35.76 ms | 0.90 MB |
| **10,000 iters** | 8 lines | 20,000 operations | 352.21 ms | 8.91 MB |
| **50,000 iters** | 8 lines | 100,000 operations | 2,034.17 ms | 44.48 MB |

Because loops are flattened into sequential dictionary lists in memory at parse time rather than represented as control-flow graph blocks or loop instructions, large iteration counts trigger high memory allocations.

### 4.4 IR Operation Object Allocation Overhead
In `src/qvm/ir.py:112-123`, every operation is constructed as an untyped dictionary:
```python
operation = {
    "name": gate_name,
    "qubits": qubits if qubits is not None else [],
    "params": params if params is not None else [],
    "condition": condition,
    "target_bit": target_bit,
    "duration": duration,
    "label": label,
    "jump_to": jump_to,
    "classical_op": classical_op
}
```
- Each Python dictionary with 9 keys allocates 232 bytes, plus 56 bytes per list, plus string memory.
- For a 100,000 operation circuit, storing operations in this form consumes >35 MB of heap memory solely for container dictionaries, before simulation even begins.
- Accessing dictionary keys (`op["name"]`, `op["qubits"]`) incurs dynamic hash-table lookups across all downstream passes (decomposer, transpiler, simulator).

---

## 5. Error Reporting & Recovery Analysis

### 5.1 Diagnostics Gaps
1. **Zero Source Location in `OpenQASM2Parser`**:
   - `ValueError: Unsupported gate: <name>`
   - `ValueError: Invalid qubit token: <token>`
   - `ValueError: Invalid qreg line`
   None of the exceptions in `OpenQASM2Parser` provide line numbers, column numbers, or file names.
2. **Leaked Lark Grammar Internals in `OpenQASM3Parser`**:
   - When a syntax error occurs, Lark raises `UnexpectedToken` containing grammar rule internals:
     ```
     UnexpectedToken: Unexpected token Token('__ANON_3', '/2) q[0];') at line 3, column 6.
     Expected one of: * RPAR * COMMA
     ```
   - No user-friendly diagnostic formatting (e.g. file path, line number, column pointer `^`, actionable suggestions).
3. **No Error Recovery or Multi-Diagnostic Reporting**:
   - Both parsers stop immediately on the first syntax error (fail-fast).
   - In industrial compilers, parsers synchronize at statement boundaries (e.g. `;` or `}`) and continue parsing to report all syntax errors in a single compiler run.

---

## 6. Detailed File References & Code Inventory

| File Path | Lines | Category | Finding Summary |
|---|---|---|---|
| `src/qvm/qasm3.lark` | 4–65 | Grammar | OpenQASM 3.0 grammar definition; lacks subroutines, math expressions, includes, and variables. |
| `src/qvm/qasm3_parser.py` | 8–17 | Initialization | Re-reads grammar from disk on every parser instantiation (`OpenQASM3Parser.__init__`). |
| `src/qvm/qasm3_parser.py` | 32–47 | Declarations | Classical register declaration order bug (`bit` before `qubit` drops registers). |
| `src/qvm/qasm3_parser.py` | 58–60 | AST Eval | Missing register index boundary checks on qubit references. |
| `src/qvm/qasm3_parser.py` | 50–55 | AST Eval | String token evaluation causes rejection of symbolic parameters in `add_operation`. |
| `src/qvm/qasm3_parser.py` | 121–128 | Control Flow | Eager parse-time unrolling of for-loops; iteration variable is ignored. |
| `src/qvm/qasm3_parser.py` | 130–140 | Control Flow | While-loop compilation generates `do-while` semantics (body always executes once). |
| `src/qvm/parser.py` | 52 | Grammar | `OpenQASM2Parser.SUPPORTED_GATES` omits `cz`, `ccx`, `s`, `t`, `p`. |
| `src/qvm/parser.py` | 84–86 | Semantics | `OpenQASM2Parser` ignores `creg` statements. |
| `src/qvm/parser.py` | 87–90 | Semantics | `OpenQASM2Parser` drops target classical bit from measurement operations. |
| `src/qvm/parser.py` | 124–138 | Lexing | `OpenQASM2Parser` splits parameters on single parenthesis and misparses missing commas. |
| `src/qvm/ir.py` | 30–36 | Data Structure | `QuantumCircuit` uses list of 9-key untyped dicts for operations. |
| `src/qvm/ir.py` | 67–98 | Validation | `GATE_SPEC` validates parameter counts but omits qubit arity checks. |
| `src/qvm/ir.py` | 230–233 | API | `QuantumCircuit.from_qasm()` instantiates new parser on every invocation. |
| `api/app.py` | 318 | API | `_parse_request` instantiates `OpenQASM3Parser()` on every incoming request. |
| `src/ir.py` | 12–55 | Architecture | Redundant legacy IR (`QuantumCircuitIR` and `QuantumGate` dataclass). |
| `src/parser.py` | 31–183 | Architecture | Redundant legacy Qiskit/Cirq parsers targeting `src/ir.py`. |

---

## 7. Actionable Roadmap to Production Readiness

### Milestone 1: Front-End Parser Hardening & Bug Fixes
1. **Fix Parser Instantiation & Cache Grammar**:
   - Compile Lark parser once at module load in `src/qvm/qasm3_parser.py` using `lark.Lark(grammar, parser='lalr', cache=True)`.
   - Eliminate re-instantiation in `api/app.py:318` and `ir.py:231`.
2. **Fix Declarations Order & Register Validation**:
   - In `qasm3_parser.py:_find_declarations`, collect all qubit and bit declarations into symbol tables before initializing `QuantumCircuit`.
   - Add bounds checks for register indexing (`0 <= idx < size`) in `_evaluate`.
3. **Correct Control Flow Semantics**:
   - Fix while-loop compilation in `qasm3_parser.py`: emit condition check before body (jump over body to loop end when false).
   - In for-loops, bind loop variable to scope and provide structured loop block representations rather than eager unrolling.
4. **Enforce Qubit Arity in `ir.py:GATE_SPEC`**:
   - Update `GATE_SPEC` to define `(num_params, num_qubits)` tuples (e.g. `"h": (0, 1)`, `"cx": (0, 2)`, `"ccx": (0, 3)`, `"rx": (1, 1)`).

### Milestone 2: Parser Grammar Modernization & Parameter Integration
1. **Extend OpenQASM 3.0 Grammar**:
   - Add arithmetic expressions (`+`, `-`, `*`, `/`, `pi`, `sin`, `cos`) in gate arguments.
   - Add support for `input float[64] theta;` parameter declarations.
   - Connect parsed parameter tokens directly to `src.qvm.parameter.Parameter` and `ParameterExpression`.
2. **Implement Rich Diagnostics**:
   - Create a compiler `Diagnostic` reporter with file name, line, column, and code snippet with caret pointer (`^`).
   - Implement synchronization tokens (`;`, `}`) for multi-error diagnostics.

### Milestone 3: High-Performance Typed IR & Streaming
1. **Migrate from Dict Operations to Typed Instruction Structs**:
   - Replace 9-key dictionaries with lightweight `__slots__`-based `CircuitOperation` dataclass / struct or flat NumPy index arrays.
   - Unify and deprecate legacy `src/ir.py` and `src/parser.py`.
2. **Add Streaming Parser**:
   - Provide a streaming/generator-based parser (`parse_stream(file_stream)`) for million-gate industrial QASM circuits to enable pipelined compilation without loading full files into memory.

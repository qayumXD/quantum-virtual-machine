---
tags: [decomposer, compilation-frontend, toffoli, ccx, basis-gates]
---
# ⚙️ Gate Decomposition

Physical quantum computers only support a limited set of native operations, called **basis gates**. Any high-level quantum gate not natively supported must be decomposed (translated) into equivalent sequences of these basis gates. This is handled by `Decomposer` in [decomposer.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/decomposer.py).

---

## 🎯 Native Gate Sets (Basis Gates)

The default target architecture basis gate set is:
$$ \text{Basis Gates} = \{ \text{id}, \text{rz}(\theta), \text{sx}, \text{x}, \text{cx} \} $$

*   `id`: Identity gate (delay/no-op).
*   `rz`: Parameterized Z-axis rotation.
*   `sx`: Square-root of X ($SX = \sqrt{X}$).
*   `x`: Pauli-X gate (Not).
*   `cx`: Controlled-NOT (CNOT).

These gates form a universal gate set, meaning any multi-qubit unitary transformation can be approximated using only these operations.

---

## 🧮 Toffoli (CCX) Gate Decomposition

The Toffoli (or Controlled-Controlled-NOT) gate is a 3-qubit gate. If both control qubits ($c_1, c_2$) are in the $|1\rangle$ state, the target qubit ($t$) is flipped.

Because physical architectures do not support 3-qubit interactions natively, the Toffoli gate must be decomposed into 1-qubit and 2-qubit gates. The `Decomposer` translates `ccx` or `toffoli` into a sequence of $15$ gates:

```mermaid
qast
q[c1] ───●───────────●────────────────────────●───────────●───[rz(pi/4)]───●────────────
         │           │                        │           │                │
q[c2] ───┼─────●─────┼──────────●─────────────┼─────●─────┼───[rz(pi/4)]───┼─────●──────
         │     │     │          │             │     │     │                │     │
q[t]  ──[H]───[X]──[rz(-pi/4)]─[X]──[rz(pi/4)]─[X]─[rz(-pi/4)]─[X]──[rz(pi/4)]─[H]───┼───
```

### The 15-Gate Sequence:
1.  `H` on target qubit ($t$).
2.  `CX` with control $c_2$ and target $t$.
3.  `Rz(-π/4)` (or $T^\dagger$) on target $t$.
4.  `CX` with control $c_1$ and target $t$.
5.  `Rz(π/4)` (or $T$) on target $t$.
6.  `CX` with control $c_2$ and target $t$.
7.  `Rz(-π/4)` on target $t$.
8.  `CX` with control $c_1$ and target $t$.
9.  `Rz(π/4)` on control $c_2$.
10. `Rz(π/4)` on target $t$.
11. `H` on target $t$.
12. `CX` with control $c_1$ and target $c_2$.
13. `Rz(π/4)` on control $c_1$.
14. `Rz(-π/4)` on control $c_2$.
15. `CX` with control $c_1$ and target $c_2$.

This sequence requires $6$ CNOT gates, $2$ Hadamard gates, and $7$ single-qubit rotations.

---

## 🔒 Preserving Control Flow Metadata

A key feature of the QVM Decomposer is that it preserves control flow metadata. If a high-level gate is conditional, the decomposed gates inherit the same condition.

For example, if the Toffoli gate is conditional:
```qasm
if (c == 1) {
    ccx q[0], q[1], q[2];
}
```

The decomposed sequence is generated with the same condition applied to each gate:
```python
cond = op.get("condition")
decomposition = [
    {"name": "h", "qubits": [t], "params": [], "condition": cond},
    {"name": "cx", "qubits": [c2, t], "params": [], "condition": cond},
    # ... all 15 gates are registered with the condition
]
```
This ensures that the simulator's control-flow engine correctly applies the condition to the entire decomposed sequence.

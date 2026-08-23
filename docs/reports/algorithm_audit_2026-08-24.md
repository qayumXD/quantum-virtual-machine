# Algorithm Audit Report — QVM v0.4 Cross-Framework Stress Test

**Date:** 2026-08-24
**Scope:** 19 quantum algorithms — authored natively in OpenQASM 2/3, JSON,
Qiskit, and Cirq, spanning textbook classics to industry-flavored variational
workloads — pushed through the full QVM pipeline (ingest → IR → bind →
simulate → validate), each cross-checked against its native framework
simulator where applicable.
**Runner:** `python -m benchmarks.run_audit [--all]`
**Final result:** **19 / 19 clean** · unit suite: **167 passed**

---

## 1. Corpus

| ID | Algorithm | Framework | Class | Validates |
|---|---|---|---|---|
| q01 | Bell pair | QASM 2.0 | small | probs vs analytic |
| q02 | GHZ-5 | QASM 3.0 | small | probs vs analytic |
| q03 | **Teleportation** (mid-measure + `if` feedback) | QASM 3.0 | textbook | shot statistics vs theory |
| q04 | Grover-3, 2 iterations | QASM 3.0 | textbook | ideal-amplitude match |
| q05 | GHZ-3 + JSON round-trip | JSON | small | lossless serialization |
| q10 | Bernstein-Vazirani (s=1101) | Qiskit | textbook | secret recovered ≥98% |
| q11 | Deutsch-Jozsa (balanced) | Qiskit | textbook | zero-outcome impossible |
| q12 | W-state-3 | Qiskit | textbook | exact amplitudes ⅓ |
| q13 | QFT + iQFT round trip | Qiskit | textbook | refocus δ > 0.99 |
| q14 | **QPE of T gate** | Qiskit | advanced | deterministic bin 001 > 0.95 |
| q20 | Bell | Cirq | small | probs vs analytic |
| q21 | GHZ-10 | Cirq | scaling | no leakage outside GHZ space |
| q22 | QFT round trip | Cirq | textbook | refocus δ > 0.99 |
| q23 | W-state-3 | Cirq | textbook | exact amplitudes ⅓ |
| q30 | **QAOA MaxCut** (square, p=1) | Qiskit | real-world | ⟨cut⟩ ratio; argmax = perfect bisection |
| q31 | **VQE H₂ (STO-3G)** | QVM-native | real-world | −1.857275 Ha vs exact diag < 5e-3 |
| q32 | **Portfolio QAOA** (K=2 of 3, penalty-QUBO, p=2) | Qiskit | real-world | gap to brute-force ≤ 0.15 |
| q33 | **VQC classifier** (trained on QVM) | QVM-native | real-world | train accuracy ≥ 7/8 (achieved 8/8) |
| n40 | Negative cases: library-gate import, register-measure, mcx ceiling, arity fail-fast | mixed | negative | must fail loudly |

## 2. Defects found in QVM — all fixed in this audit

| # | Severity | Defect | Fix |
|---|---|---|---|
| D1 | **Critical** | `Simulator.sample()` used a single collapsed trajectory for *all* shots → dynamic circuits (mid-circuit measurement, classical feedback) returned statistically impossible results (teleportation P(1)=0.000). | `_is_dynamic()` detection routes such circuits through per-shot `sample_with_collapse()`. (`simulator.py`) |
| D2 | High | OpenQASM 3 parser crashed on `include "stdgates.inc";` — blocked virtually every real-world QASM file. | Pre-parse pass strips include lines; stdgates map onto the built-in registry. (`qasm3_parser.py`) |
| D3 | High | `from_qiskit` rejected symbolic *expressions* (`rzz(-gamma)`, `rx(2*beta)`) — unusable for any variational template import. | Linear single-parameter expressions now import as QVM `ParameterExpression`. |
| D4 | High | Each imported gate created a **new** same-named `Parameter`; identity-based equality meant `bind_parameters()` silently missed occurrences. | Name-keyed parameter cache unifies symbols across the whole import. |
| D5 | Medium | `measure q -> c;` (full-register QASM 2 form) raised instead of expanding; classical registers were ignored entirely. | cregs parsed & declared; register measures expand per-qubit with size checks. (`parser.py`) |
| D6 | Low | `sympify("gamma")` parsed the Euler Γ *function*, corrupting parameter imports named after math functions. | `locals=` pins free parameter names as Symbols. |

## 3. Defects found in the audit corpus itself

Recorded for honesty and as evidence that cross-validation works both ways:

- Grover diffuser had the H-sandwich on a **control** line instead of the CCX target — synthesized a broken two-state flip invisible until framework comparison.
- Initial "forward QFT" was built LSB-first: a bit-reversed transform, self-consistent (round trips passed!) but wrong for phase estimation — caught only by QPE's absolute-bin assertion.
- bell/Grover first drafts assumed `simulate()` returns pre-measurement superpositions; it returns the post-collapse trajectory state (now documented semantics).
- First QAOA assertions expected p=1 to hit the brute-force optimum; theory and measurement agree the *expected* cut plateaus at ~0.75 ratio while the most-likely states are exactly optimal.

## 4. Weaknesses observed (open)

| Weakness | Impact | Candidate remedy |
|---|---|---|
| No gates beyond 3 qubits (`mcx`, multi-controlled rotations) | Real oracle circuits need transpilation before ingest | MCX decomposition pass (Phase-2 roadmap Task 2.x) |
| MPS engine rejects non-nearest-neighbor 2-qubit gates | Long-range entanglement forces dense engine or manual swaps | SWAP-network insertion inside MPSSimulator |
| `simulate()` collapse-at-measure semantics surprise newcomers | Statistical misuse (this audit tripped on it) | Document prominently; add `simulate(final_state=True)` opt-out |
| Dense-statevector memory ceiling (~N≤16–20 practical) | Scaling workloads | Roadmap Phases 1–4 (in-place kernels landed; GPU/stabilizer engines pending) |
| QASM2 parser remains a minimal subset (no custom `gate` defs, no `barrier`, single implicit qreg) | Legacy-file coverage | Tokenizer upgrade or Lark rewrite sharing the QASM3 grammar |
| Performance gap vs Aer/Cirq kernels | Credibility in benchmarks | NumPy→C++/Numba kernel path (roadmap Phase 4) |

## 5. Adoption blockers (ranked)

1. **Not on PyPI** — `pip install quantum-virtual-machine` is the only front door that matters for organic adoption. Package metadata, wheel, and extras are ready; publishing is the missing step.
2. ~~No LICENSE~~ → **fixed**: MIT `LICENSE` added (pyproject already claimed MIT).
3. ~~No CI~~ → **fixed**: GitHub Actions matrix (3.10–3.12) runs the unit suite *and* this audit corpus on every push/PR.
4. **API stability promise** — v0.x semver discipline + CHANGELOG so early adopters know what may move.
5. **Discoverability** — tutorials/notebooks, docs site (even GitHub Pages from `docs/guides`), a comparison table vs Qiskit/Cirq/PennyLane stating QVM's niche honestly: *WORA pipeline + strict interop pivot*, not raw simulation speed.
6. **Community infrastructure** — CONTRIBUTING.md, issue templates, roadmap discussion channel.
7. **Ecosystem depth** — arbitrary-basis transpilation from foreign frameworks (auto-decompose unsupported imports instead of raising), visualization parity.

## 6. Recommended next moves

1. Publish to PyPI (TestPyPI dry-run first) — unlocks everything else.
2. Add MCX/MCXRot decomposition pass → instantly widens importable circuit universe.
3. Notebook tutorial set: *Bell→teleport→Grover→VQE-in-30-lines* mirroring this corpus.
4. MPS SWAP-routing; then benchmark GHZ/QFT families against Aer & cirq simulators publicly.
5. Tag `v0.4.0` release notes around the interop guarantees ("converts or raises").

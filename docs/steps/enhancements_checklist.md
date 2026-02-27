# QVM Enhancement Checklist (2026)

We’ll tackle each item sequentially; check off after implementation & push.

- [x] Transpiler: add SABRE-style lookahead routing (bidirectional, heuristic cost) and toggle in `Transpiler`.
- [ ] Noise & sampling: depolarizing/readout noise in `Simulator`, CLI flags (`--shots`, `--seed`, `--noise`), probability vs noisy sampling comparison.
- [ ] Cirq/Qiskit parity docs: add a Cirq round-trip example in `examples/`, update `docs/guides/CLI_Usage.md` for `--shots/--seed`.
- [ ] Measurement collapse mode: support explicit measurement collapse for single-shot stepping while retaining current probability pipeline.
- [ ] OpenQASM ingestion: parse OpenQASM 2.0 files into IR (lark/pyparsing), add tests and CLI option to accept `.qasm` input.

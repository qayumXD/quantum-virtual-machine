# Status Update — February 27, 2026

## Overview
The QVM now supports advanced routing, noise-aware sampling, mid-circuit collapse, and direct OpenQASM 2.0 ingestion. All automated tests are passing.

## Recent Enhancements
- **Routing:** Added SABRE-inspired lookahead strategy (`--routing sabre`) with optional mapping restoration toggle (`--no-restore-mapping`). Greedy path remains available.
- **Noise & Sampling:** Simulator can sample with depolarizing and readout noise (`--noise-depol`, `--noise-readout`), plus a collapse mode for mid-circuit measurements (`--collapse`).
- **OpenQASM Input:** CLI accepts `.qasm` files via the new OpenQASM 2.0 parser; nqubits auto-detected.
- **Cirq Parity:** Added `examples/cirq_to_ir_demo.py` showing Cirq → IR → JSON path. CLI docs updated for new flags.

## Current Test Status
- Command: `python -m pytest`
- Result: **36 passed, 3 skipped**
- Skips: Cirq parser tests skip if Cirq isn’t installed.

## How to Use (quick)
- JSON input: `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre --shots 2000 --noise-depol 0.05 --noise-readout 0.01`
- OpenQASM input: `python -m src.qvm.cli examples/bell_state.qasm` (qreg size is auto-detected).
- Collapse sampling: add `--collapse` to enforce mid-circuit measurement behavior.

## Next Ideas
- Tune SABRE heuristic weights and add benchmarks on larger circuits.
- Expand OpenQASM coverage (u1/u2/u3, barriers, conditionals).
- Add richer noise models (T1/T2) and a density-matrix backend if needed.

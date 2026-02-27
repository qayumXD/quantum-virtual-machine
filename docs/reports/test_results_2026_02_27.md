# Test Results — February 27, 2026

- Command: `python -m pytest`
- Outcome: **36 passed, 4 skipped**
  - Skips: Cirq parser tests (if Cirq not installed) and API tests (if FastAPI missing) are marked skip when deps unavailable.
- Duration: ~3.7s on local (Python 3.13, Win10).

Key coverage:
- IR, parser, simulator, decomposer, transpiler, visual modules.
- OpenQASM 2.0 parser.
- API `/health` and `/run` (JSON & QASM) plus static client availability.
- Noise and collapse sampling paths.

For reproducibility, ensure deps from `requirements.txt` are installed (fastapi, uvicorn, matplotlib, numpy, pytest, etc.).

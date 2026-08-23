# Worker Remediation Context: Fix Brittle Assertions in tests/test_stress.py
Task:
1. Update `tests/test_stress.py` lines 343, 359, 427 (and any other brittle throughput assertions) to reflect the unoptimized Simulator Kronecker performance (e.g. `assert metrics.gate_throughput_ops_per_sec > 10` or assert positive throughput `> 0` and `wall_clock_time_sec > 0`).
2. Keep high-throughput expectations on `MPSSimulator` where tensor operations are fast.
3. Run `.venv/bin/pytest tests/test_stress.py -v` and ensure all 26 tests pass with 100% success rate.
4. Run `.venv/bin/pytest tests/ -v -k "not test_stress"` to verify 0 regressions across the rest of the test suite.
5. Deliver handoff.md in `/home/qayum/projects/quantum-virtual-machine/.agents/worker_remediation/handoff.md`.

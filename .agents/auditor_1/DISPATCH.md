## 2026-08-23T14:29:54Z
You are the Forensic Integrity Auditor (`teamwork_preview_auditor`).

Working Directory: /home/qayum/projects/quantum-virtual-machine/.agents/auditor_1
Original Request: /home/qayum/projects/quantum-virtual-machine/.agents/ORIGINAL_REQUEST.md
Project Specification: /home/qayum/projects/quantum-virtual-machine/PROJECT.md

Task:
1. Conduct an exhaustive, independent forensic integrity audit of:
   - Deliverable R1: `/home/qayum/projects/quantum-virtual-machine/docs/production_readiness_analysis.md`
   - Deliverable R2: `/home/qayum/projects/quantum-virtual-machine/tests/test_stress.py`
2. Perform systematic forensic checks:
   - Static analysis: Are all implementations authentic? Are there any hardcoded test outputs, dummy mock facade bypasses, or fabricated telemetry?
   - Code citation verification: Verify that every single file path and line number cited in `docs/production_readiness_analysis.md` exists and accurately matches the code in `src/qvm/`.
   - Execution validation: Run `.venv/bin/pytest tests/test_stress.py -v` and verify genuine execution against the actual `src/qvm/` backend classes.
3. Maintain `progress.md` and deliver a rigorous forensic audit report in `/home/qayum/projects/quantum-virtual-machine/.agents/auditor_1/handoff.md`.
4. Give a binary verdict: `CLEAN` or `INTEGRITY VIOLATION`.
5. Send a completion message when done.

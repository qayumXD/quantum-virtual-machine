# Lightweight GUI / API Plan (2026-02-27)

Implement a minimal, cross-platform web UI served by the Python backend. Check items after implementation, tests, and push.

- [ ] API skeleton: add `api/app.py` with FastAPI, `/health` and `/run` endpoints; run via `python -m api.app` or `uvicorn api.app:app`.
- [ ] Wire backend logic: reuse existing parsers/transpiler/simulator; support JSON or QASM input; expose routing/noise/collapse options.
- [ ] CLI flag: add `--api` (or `qvm serve`) to start the API quickly.
- [ ] Static client scaffolding: add minimal `web/` (plain HTML/JS or Svelte) served via FastAPI `StaticFiles`; form for upload/flags; display probabilities/counts and SVG/PNG circuit if provided.
- [ ] API tests: add pytest client tests hitting `/run` with bell_state (JSON + QASM) asserting probabilities/counts; `/health` returns 200.
- [ ] GUI smoke test: automated or documented manual step to fetch the static index and run a sample request.
- [ ] Docs: add `docs/guides/GUI_Usage.md` with start commands, API schema, and client usage.

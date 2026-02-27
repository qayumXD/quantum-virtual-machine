# QVM GUI/API Usage

## Start the API server
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
# or with reload while developing
python -m src.qvm.server --host 127.0.0.1 --port 8000 --reload
```

## API endpoints
- `GET /health` → `{"status":"ok"}`
- `POST /run`
  - Input (JSON):
    ```json
    {
      "source_type": "json",          // or "qasm"
      "circuit": [ {"name":"h","qubits":[0]}, {"name":"cx","qubits":[0,1]} ],
      "nqubits": 2,
      "transpile": true,
      "routing": "sabre",
      "restore_mapping": true,
      "shots": 2000,
      "seed": 1,
      "noise_depol": 0.01,
      "noise_readout": 0.01,
      "collapse": false
    }
    ```
    If `source_type` is `"qasm"`, provide `"qasm": "<OpenQASM 2.0 text>"` and omit `circuit/nqubits`.
  - Output:
    ```json
    {
      "probabilities": [...],
      "counts": { "00": 1000, "11": 1000 },
      "transpiled_operations": [...],
      "nqubits": 2,
      "openqasm2": "OPENQASM 2.0; ..."
    }
    ```

## CLI quick start that mirrors API behavior
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre --shots 2000 --noise-depol 0.01 --noise-readout 0.01
```

## Notes
- Routing: `greedy` (default) or `sabre`.
- Noise: depolarizing + readout available in sampling; `collapse` enables mid-circuit measurement semantics.
- QASM: pass entire OpenQASM 2.0 program in the `qasm` field when using the API.

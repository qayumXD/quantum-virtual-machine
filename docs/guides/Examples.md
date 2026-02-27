# Examples & Expected Outputs

## JSON examples
- `examples/bell_state.json`  
  Run: `python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile`  
  Expected probabilities: `|00> ≈ 0.5`, `|11> ≈ 0.5`.

- `examples/bv_101.json` (Bernstein–Vazirani for secret 101 with ancilla)  
  Run: `python -m src.qvm.cli examples/bv_101.json --nqubits 4 --transpile`  
  Expected dominant states: input bits read as `101*` (ancilla superposed).

- `examples/grover_101.json` (3-qubit Grover)  
  Run: `python -m src.qvm.cli examples/grover_101.json --nqubits 3 --transpile`  
  Expected: target `101` probability ~0.94 after two iterations.

## QASM example
- `examples/bell_state.qasm`  
  CLI: `python -m src.qvm.cli examples/bell_state.qasm --nqubits 2 --transpile` (nqubits auto-detected in API mode).  
  API payload (POST /run):  
  ```json
  {
    "source_type": "qasm",
    "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; h q[0]; cx q[0],q[1];",
    "shots": 0
  }
  ```  
  Expected probabilities: `|00> ≈ 0.5`, `|11> ≈ 0.5`.

## Generated circuits
- `examples/generate_bv.py --secret 101 --output examples/bv_101.json`
- `examples/generate_grover.py --target 101 --output examples/grover_101.json`

## Notes
- Use `--shots N` to obtain counts; with noise flags you can model depolarizing/readout errors.
- `--transpile --routing sabre` reduces swaps on linear connectivity.

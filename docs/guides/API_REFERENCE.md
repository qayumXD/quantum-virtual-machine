# QVM REST API Reference: `/run`

The Quantum Virtual Machine exposes a high-performance FastAPI execution server located in `api/app.py`. The primary execution interface is the **`POST /run`** endpoint.

---

## Endpoint Details

*   **URL**: `http://localhost:8000/run`
*   **Method**: `POST`
*   **Headers**: `Content-Type: application/json`
*   **Interactive Documentation**:
    *   Swagger UI: `http://localhost:8000/docs`
    *   ReDoc: `http://localhost:8000/redoc`

---

## Request Body Schema (`RunRequest`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `source_type` | `string` | `"json"` | `"json"` (gate list) or `"qasm"` (OpenQASM text). |
| `circuit` | `list[dict]` | `null` | Array of gate dictionaries (required if `source_type="json"`). |
| `nqubits` | `int` | `null` | Number of qubits (required if `source_type="json"`). |
| `qasm` | `string` | `null` | OpenQASM 2.0 or 3.0 text (required if `source_type="qasm"`). |
| `transpile` | `bool` | `false` | Enable hardware transpilation and routing pass. |
| `routing` | `string` | `"greedy"` | Pathfinding algorithm: `"greedy"` or `"sabre"`. |
| `restore_mapping` | `bool` | `true` | Restore initial qubit index map after SABRE. |
| `engine` | `string` | `"statevector"` | Simulation backend: `"statevector"` or `"mps"`. |
| `seed` | `int` | `null` | RNG seed for deterministic shot sampling. |
| `shots` | `int` | `0` | Number of measurement samples. If `0`, only state probabilities are computed. |
| `noise_depol` | `float` | `0.0` | Global depolarizing noise probability ($0 \le p \le 1$). |
| `noise_readout` | `float` | `0.0` | Global readout flip error probability ($0 \le p \le 1$). |
| `noise_amp_damp` | `float` | `0.0` | Amplitude damping ($T_1$) rate. |
| `noise_phase_damp` | `float` | `0.0` | Phase damping ($T_2$) rate. |
| `device_backend` | `string` | `null` | Hardware device profile: `"fake_5q"`, `"fake_7q"`, or `"ideal"`. |
| `expectation_pauli` | `dict` | `null` | Pauli string mapping to coefficients (e.g. `{"ZZ": -1.0, "XI": 0.5}`). |

---

## Response Body Schema (`RunResponse`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `probabilities` | `list[float]` | Exact quantum state probabilities for all $2^N$ basis states. |
| `counts` | `dict` | Shot-based measurement outcome counts (when `shots > 0`). |
| `classical_memory` | `dict` | Final values in named classical registers. |
| `transpiled_operations` | `list[dict]` | Final sequence of operations after compilation. |
| `nqubits` | `int` | Number of physical qubits simulated. |
| `circuit_plot` | `string` | Base64-encoded PNG image of the circuit. |
| `histogram_plot` | `string` | Base64-encoded PNG image of the probabilities histogram. |
| `openqasm2` | `string` | Equivalent compiled circuit in OpenQASM 2.0 text. |
| `expectation_value` | `float` | Evaluated Pauli expectation value $\langle H \rangle$. |
| `noise_summary` | `string` | Human-readable summary of active noise channels. |

---

## Minimal Example (curl)

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "nqubits": 2,
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "cx", "qubits": [0, 1]}
    ],
    "shots": 1000,
    "seed": 42
  }'
```

---

## Python Example (`requests`)

```python
import requests

payload = {
    "source_type": "json",
    "nqubits": 2,
    "circuit": [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "measure", "qubits": [0], "register": "c", "cbit": 0},
        {"name": "measure", "qubits": [1], "register": "c", "cbit": 1}
    ],
    "shots": 2000,
    "transpile": True,
    "routing": "sabre"
}

resp = requests.post("http://localhost:8000/run", json=payload)
data = resp.json()
print("Counts:", data["counts"])
print("Probabilities:", data["probabilities"])
```

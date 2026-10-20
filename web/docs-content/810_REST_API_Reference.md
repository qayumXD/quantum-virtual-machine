---
tags: [api-reference, rest-api, run-endpoint, fastapi, curl, python-requests, schemas]
---

# REST API Reference: `/run` Endpoint

The primary computational interface of the Quantum Virtual Machine (QVM) backend is the **`POST /run`** endpoint, implemented in [api/app.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/api/app.py).

This document serves as the complete, authoritative specification for `/run`, derived directly from the application's Pydantic schemas and FastAPI route handlers.

---

## 📌 Endpoint Overview

*   **URL**: `http://localhost:8000/run` (or the deployed service domain)
*   **Method**: `POST`
*   **Request Headers**:
    *   `Content-Type: application/json`
    *   `Accept: application/json`
*   **Authentication**: None required for `/run` (open local/service endpoint).
*   **Interactive OpenAPI Specs**:
    *   Swagger UI: `GET /docs` (FastAPI native interactive docs)
    *   ReDoc: `GET /redoc`
    *   OpenAPI JSON schema: `GET /openapi.json`

---

## 📥 Request Body Schema (`RunRequest`)

The request body must be a JSON object conforming to `RunRequest`:

| Field | Type | Default | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :--- | :--- |
| `source_type` | `string` | `"json"` | No | Input format. Accepted values: `"json"` or `"qasm"`. |
| `circuit` | `array[object]` | `null` | **Yes** if `source_type="json"` | List of quantum gate operations (see [Gate Dictionary](#gate-dictionary-format)). |
| `nqubits` | `integer` | `null` | **Yes** if `source_type="json"` | Number of qubits in the circuit. Must be $\ge 1$. |
| `qasm` | `string` | `null` | **Yes** if `source_type="qasm"` | Raw OpenQASM 2.0 or OpenQASM 3.0 circuit text. |
| `transpile` | `boolean` | `false` | No | If `true`, runs the transpilation pass onto a physical linear architecture. |
| `routing` | `string` | `"greedy"` | No | Pathfinding algorithm for routing two-qubit gates. Accepted: `"greedy"` or `"sabre"`. |
| `restore_mapping` | `boolean` | `true` | No | If `true`, applies uncomputation SWAPs to restore initial qubit labeling after SABRE routing. |
| `engine` | `string` | `"statevector"` | No | Simulation engine. Accepted: `"statevector"` (dense amplitudes) or `"mps"` (Matrix Product States). |
| `seed` | `integer` | `null` | No | Pseudo-random number generator seed for deterministic simulation and sampling. |
| `shots` | `integer` | `0` | No | Number of measurement samples. If `0`, only analytical probabilities are computed; if $> 0$, returns measurement outcome counts. |
| `noise_depol` | `float` | `0.0` | No | Global single-qubit depolarizing error probability ($0.0 \le p \le 1.0$). |
| `noise_readout` | `float` | `0.0` | No | Global bit-flip measurement readout error probability ($0.0 \le p \le 1.0$). |
| `noise_amp_damp` | `float` | `0.0` | No | Amplitude damping ($T_1$ decay) parameter $\gamma \in [0.0, 1.0]$. |
| `noise_phase_damp` | `float` | `0.0` | No | Phase damping ($T_2$ dephasing) parameter $\gamma \in [0.0, 1.0]$. |
| `device_backend` | `string` | `null` | No | Predefined hardware noise profile. Accepted: `"fake_5q"`, `"fake_7q"`, or `"ideal"`. |
| `expectation_pauli` | `object` | `null` | No | Mapping of Pauli strings to scalar coefficients for expectation value calculation (e.g., `{"ZZ": -1.0, "XI": 0.5}`). Requires `engine="statevector"`. |

### Gate Dictionary Format (JSON Circuits)
When `source_type="json"`, each element in `circuit` is a dictionary:
```json
{
  "name": "rx",
  "qubits": [0],
  "params": [1.5707963],
  "register": "c",
  "cbit": 0
}
```
*   `name`: Gate identifier (`h`, `x`, `y`, `z`, `s`, `t`, `rx`, `ry`, `rz`, `p`, `cx`, `cz`, `swap`, `ccx`, `measure`, etc.).
*   `qubits`: List of target qubit indices.
*   `params`: Optional list of float rotation angles in radians.
*   `register` / `cbit`: Required only for `"name": "measure"`.

---

## 📤 Response Body Schema (`RunResponse`)

Upon successful execution, the endpoint returns HTTP `200 OK` with a `RunResponse` JSON payload:

| Field | Type | Nullable? | Description |
| :--- | :--- | :--- | :--- |
| `probabilities` | `array[float]` | No | Analytical state probabilities $P(i) = |\psi_i|^2$ for all $2^N$ computational basis states ($i = 0, \dots, 2^N - 1$). |
| `counts` | `object` | Yes | Frequency dictionary of measurement outcomes (e.g. `{"00": 508, "11": 492}`). Present only when `shots > 0`. |
| `classical_memory` | `object` | Yes | Final state of named classical bit registers (e.g. `{"c": [0, 1]}`). |
| `transpiled_operations` | `array[object]` | No | Sequence of operations after transpilation, basis decomposition, and routing. |
| `nqubits` | `integer` | No | Number of physical qubits allocated for the simulation. |
| `circuit_plot` | `string` | Yes | Base64-encoded PNG image of the routed circuit diagram. |
| `histogram_plot` | `string` | Yes | Base64-encoded PNG image of the state probability histogram. |
| `openqasm2` | `string` | Yes | Equivalent circuit exported to OpenQASM 2.0 text format. |
| `expectation_value` | `float` | Yes | Evaluated Hamiltonian expectation value $\langle H \rangle$ if `expectation_pauli` was specified. |
| `noise_summary` | `string` | Yes | Text summary of active noise channels and damping parameters applied. |

---

## 🚀 Examples

### Example 1: Minimal Valid Request (OpenQASM)
A minimal request creating and measuring a Bell state with 1,000 shots:

#### Request (curl)
```bash
curl -X POST "http://127.0.0.1:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "qasm",
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0], q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];",
    "shots": 1000,
    "seed": 42
  }'
```

#### Response (`200 OK`)
```json
{
  "probabilities": [0.5, 0.0, 0.0, 0.5],
  "classical_memory": {
    "c": [1, 1]
  },
  "transpiled_operations": [
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]},
    {"name": "measure", "qubits": [0], "register": "c", "cbit": 0},
    {"name": "measure", "qubits": [1], "register": "c", "cbit": 1}
  ],
  "nqubits": 2,
  "circuit_plot": "iVBORw0KGgoAAAANSUhEUgAAAYAAAAEACA...",
  "histogram_plot": "iVBORw0KGgoAAAANSUhEUgAAAZAAAAEACA...",
  "counts": {
    "00": 498,
    "11": 502
  },
  "openqasm2": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0], q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n",
  "expectation_value": null,
  "noise_summary": null
}
```

---

### Example 2: Full-Featured Request (Python `requests`)

This example demonstrates hardware SABRE routing, depolarizing & readout noise, shot sampling, and Pauli expectation value calculation:

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
    "transpile": True,
    "routing": "sabre",
    "restore_mapping": True,
    "engine": "statevector",
    "shots": 2000,
    "seed": 1337,
    "noise_depol": 0.02,
    "noise_readout": 0.01,
    "expectation_pauli": {
        "ZZ": 1.0,
        "XX": 1.0
    }
}

response = requests.post("http://127.0.0.1:8000/run", json=payload)
data = response.json()

print("Status Code:", response.status_code)
print("Physical Qubits:", data["nqubits"])
print("Sampled Counts:", data["counts"])
print("Expectation Value <ZZ + XX>:", data["expectation_value"])
print("Noise Summary:", data["noise_summary"])
```

---

## ⚠️ Error Responses and Status Codes

The API returns standard HTTP status codes along with descriptive error payloads in the format `{"detail": "Error description"}`:

### 1. `400 Bad Request` — Parse Error
Occurs when QASM syntax is invalid or required fields for the chosen `source_type` are missing:

*   **Example Trigger**: `source_type="json"` without supplying `circuit` or `nqubits`.
    ```json
    {
      "detail": "Parse error: circuit and nqubits are required for source_type=json"
    }
    ```
*   **Example Trigger**: Syntax error in OpenQASM text:
    ```json
    {
      "detail": "Parse error: Syntax error in QASM: Unexpected token 'foo' at line 3"
    }
    ```

### 2. `400 Bad Request` — Transpilation Error
Occurs if SABRE or Greedy routing encounters an unsupported multi-qubit topology or invalid qubit index:
```json
{
  "detail": "Transpilation error: Qubit index 5 out of range for 2-qubit architecture"
}
```

### 3. `422 Unprocessable Entity` — Schema Validation Failure
FastAPI and Pydantic automatically validate types, non-null requirements, and enum values before execution starts:
*   **Example Trigger**: Passing `engine="quantum_supremacy"` (valid values: `"statevector"`, `"mps"`):
    ```json
    {
      "detail": [
        {
          "type": "literal_error",
          "loc": ["body", "engine"],
          "msg": "Input should be 'statevector' or 'mps'",
          "input": "quantum_supremacy"
        }
      ]
    }
    ```

### 4. `500 Internal Server Error` — Simulation Failure
Raised if an unhandled runtime error occurs during numerical statevector contraction:
```json
{
  "detail": "Simulation error: Memory allocation failure during state evolution"
}
```

---

## 🔒 Limitations & Best Practices

1. **Qubit Scaling Limit**:
   *   `engine="statevector"` allocates $2^N$ complex amplitudes ($2^{N+4}$ bytes for `complex128`). While $N \le 14$ executes in milliseconds, $N > 16$ requires gigabytes of memory and can cause process timeouts.
   *   For $N \ge 16$ with 1D nearest-neighbor topologies, use `engine="mps"`.
2. **Deterministic Reproducibility**:
   *   Always pass the `seed` parameter when benchmarking or testing shot distributions to ensure exact reproducibility across multiple runs.
3. **Pauli Expectation Support**:
   *   `expectation_pauli` currently evaluates against the statevector engine (`engine="statevector"`). It returns `null` if used with `engine="mps"`.

Next: [Web API and Dashboard Architecture](/docs/800_Web_API_and_Dashboard).

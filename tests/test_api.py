import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

try:
    from api.app import app
except Exception as exc:  # pragma: no cover
    pytest.skip(f"API app import failed: {exc}", allow_module_level=True)

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_run_json_bell_state():
    payload = {
        "source_type": "json",
        "circuit": [
            {"name": "h", "qubits": [0]},
            {"name": "cx", "qubits": [0, 1]},
        ],
        "nqubits": 2,
        "transpile": False,
        "shots": 0,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    probs = data["probabilities"]
    assert pytest.approx(probs[0], rel=1e-6) == 0.5
    assert pytest.approx(probs[3], rel=1e-6) == 0.5
    assert data["counts"] is None
    assert data["openqasm2"].startswith("OPENQASM")


def test_run_qasm():
    qasm = """OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0],q[1];
    """
    payload = {
        "source_type": "qasm",
        "qasm": qasm,
        "transpile": False,
        "shots": 0,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    probs = resp.json()["probabilities"]
    assert pytest.approx(probs[0], rel=1e-6) == 0.5
    assert pytest.approx(probs[3], rel=1e-6) == 0.5


def test_run_json_with_shots_and_noise():
    payload = {
        "source_type": "json",
        "circuit": [
            {"name": "h", "qubits": [0]},
            {"name": "cx", "qubits": [0, 1]},
        ],
        "nqubits": 2,
        "transpile": True,
        "routing": "sabre",
        "shots": 200,
        "noise_depol": 0.05,
        "noise_readout": 0.01,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    counts = data["counts"]
    assert counts is not None
    total = sum(counts.values())
    assert total == 200


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert data["version"] == "0.5.1"
    assert "frontend" in data


def test_static_client_served():
    import os
    if not os.path.exists("web/out"):
        pytest.skip("Static web client build (web/out) not present locally")
    resp = client.get("/web/index.html")
    assert resp.status_code == 200


def test_run_with_expectation_pauli():
    payload = {
        "source_type": "json",
        "nqubits": 2,
        "circuit": [
            {"name": "h", "qubits": [0]},
            {"name": "cx", "qubits": [0, 1]},
        ],
        "expectation_pauli": {"ZZ": 1.0, "XX": 1.0},
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["expectation_value"] is not None
    assert pytest.approx(data["expectation_value"], rel=1e-5) == 2.0


def test_run_openqasm3():
    qasm3 = """OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    cx q[0], q[1];
    """
    payload = {
        "source_type": "qasm",
        "qasm": qasm3,
        "shots": 0,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    probs = data["probabilities"]
    assert pytest.approx(probs[0], rel=1e-6) == 0.5
    assert pytest.approx(probs[3], rel=1e-6) == 0.5


def test_run_device_backend():
    payload = {
        "source_type": "json",
        "nqubits": 2,
        "circuit": [
            {"name": "h", "qubits": [0]},
            {"name": "cx", "qubits": [0, 1]},
        ],
        "device_backend": "fake_5q",
        "shots": 100,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["noise_summary"] is not None


def test_run_missing_circuit_raises_400():
    payload = {
        "source_type": "json",
        "circuit": None,
        "nqubits": None,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 400
    assert "Parse error" in resp.json()["detail"]


def test_run_invalid_engine_raises_422():
    payload = {
        "source_type": "json",
        "circuit": [{"name": "h", "qubits": [0]}],
        "nqubits": 1,
        "engine": "invalid_engine",
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 422

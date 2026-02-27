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

import requests
import time

API_URL = "http://127.0.0.1:8000"

print("Submitting Bell State simulation...")
req_data = {
    "source_type": "json",
    "nqubits": 2,
    "circuit": [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "measure", "qubits": [0], "clbits": [0]},
        {"name": "measure", "qubits": [1], "clbits": [1]}
    ],
    "engine": "statevector",
    "shots": 1000,
    "seed": 42
}

try:
    resp = requests.post(f"{API_URL}/run", json=req_data)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Success! Probabilities: {data.get('probabilities')}")
        print(f"Counts: {data.get('counts')}")
        print("Check your Supabase 'simulation_runs' table for the new entry.")
    else:
        print(f"Error {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Connection failed: {e}")

# FastAPI backend for QVM with OpenQASM 3.0, MPS, Noise Models, and VQA

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

from src.qvm.parser import QASMParser, OpenQASM2Parser
from src.qvm.qasm3_parser import OpenQASM3Parser
from src.qvm.transpiler import Transpiler
from src.qvm.simulator import Simulator
from src.qvm.mps_simulator import MPSSimulator
from src.qvm.architecture import get_linear_architecture
from src.qvm.visual import plot_histogram, plot_circuit
from src.qvm.util.export import to_openqasm2
from src.qvm.noise import NoiseChannel, NoiseModel, DeviceBackend
from src.qvm.observable import Hamiltonian


class RunRequest(BaseModel):
    source_type: Literal["json", "qasm"] = Field("json", description="Input format")
    circuit: Optional[List[dict]] = Field(None, description="Gate list when source_type=json")
    qasm: Optional[str] = Field(None, description="OpenQASM text when source_type=qasm")
    nqubits: Optional[int] = Field(None, description="Number of qubits")
    transpile: bool = False
    routing: Literal["greedy", "sabre"] = "greedy"
    restore_mapping: bool = True
    engine: Literal["statevector", "mps"] = "statevector"
    seed: Optional[int] = None
    shots: int = Field(0, description="Number of measurement samples. If 0, only pure state probabilities are calculated.")
    noise_depol: float = Field(0.0, description="Depolarizing noise probability (0 to 1)")
    noise_readout: float = Field(0.0, description="Readout flip probability (0 to 1)")
    noise_amp_damp: float = Field(0.0, description="Amplitude damping gamma (0 to 1)")
    noise_phase_damp: float = Field(0.0, description="Phase damping gamma (0 to 1)")
    device_backend: Optional[str] = Field(None, description="Predefined device: fake_5q, fake_7q, ideal")
    expectation_pauli: Optional[Dict[str, float]] = Field(None, description="Pauli string dict for expectation value, e.g. {'ZZ': -1.0, 'XI': 0.5}")


class RunResponse(BaseModel):
    probabilities: List[float]
    classical_memory: Optional[dict]
    transpiled_operations: List[dict]
    nqubits: int
    circuit_plot: Optional[str] = None # Base64 encoded PNG
    histogram_plot: Optional[str] = None # Base64 encoded PNG
    counts: Optional[dict] = None
    openqasm2: Optional[str] = None
    expectation_value: Optional[float] = None
    noise_summary: Optional[str] = None


app = FastAPI(title="QVM API", version="0.3.0")

# Serve static web client
app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def root():
    return FileResponse("web/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_str


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    try:
        qc = _parse_request(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    # Transpile if requested
    if req.transpile:
        try:
            arch = get_linear_architecture(qc.num_qubits)
            transpiler = Transpiler(arch, strategy=req.routing, restore_mapping=req.restore_mapping)
            qc = transpiler.transpile(qc)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Transpilation error: {e}")

    # Simulation
    try:
        counts = None
        noise_model = _build_noise_model(req, qc.num_qubits)
        noise_summary = noise_model.summary() if noise_model and noise_model.has_noise() else None

        if req.engine == "mps":
            sim = MPSSimulator()
            _, mem = sim.simulate(qc, seed=req.seed)
            probs = np.abs(sim.get_statevector())**2
            if req.shots > 0:
                counts = sim.sample(qc, shots=req.shots, seed=req.seed)
        else:
            sim = Simulator()
            state, mem = sim.simulate(qc, seed=req.seed)
            probs = np.abs(state)**2
            if req.shots > 0:
                if noise_model and noise_model.has_noise():
                    counts = sim.sample(qc, shots=req.shots, seed=req.seed,
                                       noise_model=noise_model)
                else:
                    counts = sim.sample(
                        qc,
                        shots=req.shots,
                        seed=req.seed,
                        depol_prob=req.noise_depol,
                        readout_error=req.noise_readout
                    )

        # Expectation value
        exp_val = None
        if req.expectation_pauli:
            obs = Hamiltonian.from_dict(req.expectation_pauli)
            exp_val = float(sim.expectation_value(qc, obs, seed=req.seed)) if req.engine == "statevector" else None

        # Ensure all numpy types are converted for JSON
        serializable_mem = {}
        for k, v in mem.items():
            if isinstance(v, np.ndarray):
                serializable_mem[k] = v.tolist()
            else:
                serializable_mem[k] = v

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")

    # Generate Visualizations
    circuit_b64 = None
    hist_b64 = None
    try:
        fig_c = plot_circuit(qc, title="Executed Physical Circuit")
        circuit_b64 = fig_to_base64(fig_c)
        
        fig_h = plot_histogram(probs, title="Simulation Probabilities")
        hist_b64 = fig_to_base64(fig_h)
    except Exception as e:
        print(f"Viz error: {e}") # Non-fatal

    return RunResponse(
        probabilities=list(map(float, probs)),
        classical_memory=serializable_mem,
        transpiled_operations=qc.operations,
        nqubits=qc.num_qubits,
        circuit_plot=circuit_b64,
        histogram_plot=hist_b64,
        counts=counts,
        openqasm2=to_openqasm2(qc),
        expectation_value=exp_val,
        noise_summary=noise_summary,
    )


def _build_noise_model(req: RunRequest, num_qubits: int) -> Optional[NoiseModel]:
    """Build a NoiseModel from request parameters."""
    if req.device_backend:
        device_map = {
            "fake_5q": DeviceBackend.fake_5q_device,
            "fake_7q": DeviceBackend.fake_7q_device,
            "ideal": lambda: DeviceBackend.ideal(num_qubits),
        }
        if req.device_backend not in device_map:
            raise ValueError(f"Unknown device: {req.device_backend}")
        return device_map[req.device_backend]().to_noise_model()

    if req.noise_amp_damp > 0 or req.noise_phase_damp > 0:
        model = NoiseModel()
        all_1q = ["h", "x", "y", "z", "rx", "ry", "rz", "p", "sx", "s", "t", "id"]
        if req.noise_amp_damp > 0:
            model.add_all_qubit_quantum_error(
                NoiseChannel.amplitude_damping(req.noise_amp_damp), all_1q)
        if req.noise_phase_damp > 0:
            model.add_all_qubit_quantum_error(
                NoiseChannel.phase_damping(req.noise_phase_damp), all_1q)
        if req.noise_depol > 0:
            model.add_all_qubit_quantum_error(
                NoiseChannel.depolarizing(req.noise_depol), all_1q)
        return model

    return None


def _parse_request(req: RunRequest):
    if req.source_type == "json":
        if req.circuit is None or req.nqubits is None:
            raise ValueError("circuit and nqubits are required for source_type=json")
        return QASMParser.parse(req.circuit, req.nqubits)
    else:
        if not req.qasm:
            raise ValueError("qasm text required for source_type=qasm")
        if "OPENQASM 3" in req.qasm.upper():
            parser3 = OpenQASM3Parser()
            return parser3.parse(req.qasm)
        else:
            return OpenQASM2Parser.parse(req.qasm)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)

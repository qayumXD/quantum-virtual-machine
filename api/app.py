# FastAPI backend for QVM with OpenQASM 3.0, MPS, and Visualizations

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from src.qvm.parser import QASMParser, OpenQASM2Parser
from src.qvm.qasm3_parser import OpenQASM3Parser
from src.qvm.transpiler import Transpiler
from src.qvm.simulator import Simulator
from src.qvm.mps_simulator import MPSSimulator
from src.qvm.architecture import get_linear_architecture
from src.qvm.visual import plot_histogram, plot_circuit


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


class RunResponse(BaseModel):
    probabilities: List[float]
    classical_memory: Optional[dict]
    transpiled_operations: List[dict]
    nqubits: int
    circuit_plot: Optional[str] = None # Base64 encoded PNG
    histogram_plot: Optional[str] = None # Base64 encoded PNG


app = FastAPI(title="QVM API", version="0.2.1")

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
        if req.engine == "mps":
            sim = MPSSimulator()
            _, mem = sim.simulate(qc, seed=req.seed)
            probs = np.abs(sim.get_statevector())**2
        else:
            sim = Simulator()
            state, mem = sim.simulate(qc, seed=req.seed)
            probs = np.abs(state)**2
        
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
        histogram_plot=hist_b64
    )


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

# Minimal FastAPI backend for QVM

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from src.qvm.parser import QASMParser, OpenQASM2Parser
from src.qvm.transpiler import Transpiler
from src.qvm.simulator import Simulator
from src.qvm.architecture import get_linear_architecture
from src.qvm.util.export import to_openqasm2


class RunRequest(BaseModel):
    source_type: Literal["json", "qasm"] = Field("json", description="Input format")
    circuit: Optional[List[dict]] = Field(None, description="Gate list when source_type=json")
    qasm: Optional[str] = Field(None, description="OpenQASM 2.0 text when source_type=qasm")
    nqubits: Optional[int] = Field(None, description="Number of qubits (required for json)")
    transpile: bool = False
    routing: Literal["greedy", "sabre"] = "greedy"
    restore_mapping: bool = True
    shots: int = 0
    seed: Optional[int] = None
    noise_depol: float = 0.0
    noise_readout: float = 0.0
    collapse: bool = False


class RunResponse(BaseModel):
    probabilities: List[float]
    counts: Optional[dict]
    transpiled_operations: List[dict]
    nqubits: int
    openqasm2: Optional[str] = None


app = FastAPI(title="QVM API", version="0.1")

# Serve static web client if available
app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def root():
    return FileResponse("web/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    try:
        qc = _parse_request(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    # Transpile if requested
    if req.transpile:
        arch = get_linear_architecture(qc.num_qubits)
        transpiler = Transpiler(arch, strategy=req.routing, restore_mapping=req.restore_mapping)
        qc = transpiler.transpile(qc)

    sim = Simulator()
    probs = sim.get_probabilities(sim.simulate(qc))

    counts = None
    if req.shots and req.shots > 0:
        if req.collapse:
            counts = sim.sample_with_collapse(qc, shots=req.shots, seed=req.seed)
        else:
            counts = sim.sample(
                qc,
                shots=req.shots,
                seed=req.seed,
                depol_prob=req.noise_depol,
                readout_error=req.noise_readout,
            )

    return RunResponse(
        probabilities=list(map(float, probs)),
        counts=counts,
        transpiled_operations=qc.operations,
        nqubits=qc.num_qubits,
        openqasm2=to_openqasm2(qc),
    )


# Helpers -----------------------------------------------------------------
def _parse_request(req: RunRequest):
    if req.source_type == "json":
        if req.circuit is None or req.nqubits is None:
            raise ValueError("circuit and nqubits are required for source_type=json")
        return QASMParser.parse(req.circuit, req.nqubits)
    else:
        if not req.qasm:
            raise ValueError("qasm text required for source_type=qasm")
        return OpenQASM2Parser.parse(req.qasm)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)

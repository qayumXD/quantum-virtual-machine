"use client";

import { useState, useRef, useEffect } from "react";
import { Play, Upload, Download, TerminalSquare, AlertCircle } from "lucide-react";

export default function Workspace() {
  const [qasm, setQasm] = useState(`OPENQASM 3.0;
qubit[2] q;
bit[2] c;

// Bell State
h q[0];
cx q[0], q[1];

c[0] = measure q[0];
c[1] = measure q[1];`);

  const [engine, setEngine] = useState("statevector");
  const [shots, setShots] = useState(1000);
  const [seed, setSeed] = useState("");
  const [transpile, setTranspile] = useState(true);
  const [routing, setRouting] = useState("sabre");
  const [restoreMapping, setRestoreMapping] = useState(true);

  // Advanced backend features
  const [noiseDepol, setNoiseDepol] = useState(0.0);
  const [noiseReadout, setNoiseReadout] = useState(0.0);
  const [noiseAmpDamp, setNoiseAmpDamp] = useState(0.0);
  const [noisePhaseDamp, setNoisePhaseDamp] = useState(0.0);
  const [deviceBackend, setDeviceBackend] = useState("");
  const [expectationPauli, setExpectationPauli] = useState("");

  const [logs, setLogs] = useState<{ time: string; msg: string; type: "info" | "error" | "success" }[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [results, setResults] = useState<any>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const addLog = (msg: string, type: "info" | "error" | "success" = "info") => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      if (evt.target?.result) {
        setQasm(evt.target.result as string);
        addLog(`Imported file: ${file.name}`, "info");
      }
    };
    reader.onerror = () => addLog("Error reading file", "error");
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleRun = async () => {
    setIsSimulating(true);
    setResults(null);
    addLog("Submitting circuit to QVM Backend (https://quantum-virtual-machine.onrender.com)...");

    let parsedPauli = null;
    if (expectationPauli.trim()) {
      try {
        parsedPauli = JSON.parse(expectationPauli);
      } catch (err) {
        addLog(`JSON Parse Error in Expectation Pauli: ${err}`, "error");
        setIsSimulating(false);
        return;
      }
    }

    try {
      const startTime = performance.now();
      const response = await fetch("https://quantum-virtual-machine.onrender.com/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_type: "qasm",
          qasm,
          engine,
          shots: Number(shots),
          seed: seed ? Number(seed) : null,
          transpile,
          routing,
          restore_mapping: restoreMapping,
          noise_depol: Number(noiseDepol),
          noise_readout: Number(noiseReadout),
          noise_amp_damp: Number(noiseAmpDamp),
          noise_phase_damp: Number(noisePhaseDamp),
          device_backend: deviceBackend || null,
          expectation_pauli: parsedPauli,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Unknown server error");
      }

      const execTime = (performance.now() - startTime).toFixed(1);
      setResults(data);
      addLog(`Simulation completed successfully in ${execTime}ms.`, "success");
      
      if (data.noise_summary) {
        addLog(`Noise Profile Applied: ${data.noise_summary.substring(0, 60)}...`);
      }
      if (data.expectation_value !== null) {
        addLog(`Expectation Value: ${data.expectation_value}`, "success");
      }

    } catch (err: any) {
      addLog(`Failed: ${err.message}`, "error");
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 h-full w-full">
      
      {/* 3-Column Split */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        
        {/* Left: Editor */}
        <div className="w-[30%] border-r border-border-color flex flex-col min-w-0">
          <div className="panel-header justify-between">
            <span>Editor</span>
            <div className="flex gap-2">
              <input type="file" ref={fileInputRef} className="hidden" accept=".qasm,.json" onChange={handleFileUpload} />
              <button className="btn !py-1 !px-2 flex gap-1 items-center" onClick={() => fileInputRef.current?.click()} title="Import .qasm or .json">
                <Upload size={14} /> Import
              </button>
            </div>
          </div>
          <textarea
            value={qasm}
            onChange={(e) => setQasm(e.target.value)}
            className="flex-1 w-full bg-code-bg text-text-main font-mono text-sm p-4 outline-none resize-none"
            spellCheck="false"
          />
        </div>

        {/* Middle: Configuration */}
        <div className="w-[30%] border-r border-border-color bg-bg-base overflow-y-auto min-w-0">
          <div className="panel-header">
            <span>Configuration</span>
          </div>
          
          <div className="p-4 flex flex-col gap-4">
            <div className="card">
              <div className="card-title">Core Engine</div>
              <div className="config-row">
                <label>Engine</label>
                <select className="config-input w-36" value={engine} onChange={(e) => setEngine(e.target.value)}>
                  <option value="statevector">Statevector</option>
                  <option value="density_matrix">Density Matrix</option>
                  <option value="mps">MPS</option>
                </select>
              </div>
              <div className="config-row">
                <label>Shots</label>
                <input type="number" className="config-input w-24" value={shots} onChange={(e) => setShots(Number(e.target.value))} />
              </div>
              <div className="config-row">
                <label>Seed (Opt)</label>
                <input type="number" className="config-input w-24" value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="Random" />
              </div>
            </div>

            <div className="card">
              <div className="card-title">Transpiler</div>
              <div className="flex items-center gap-2 mb-2 text-sm">
                <input type="checkbox" checked={transpile} onChange={(e) => setTranspile(e.target.checked)} />
                <label>Enable Transpilation</label>
              </div>
              <div className="config-row">
                <label>Routing</label>
                <select className="config-input w-36" value={routing} onChange={(e) => setRouting(e.target.value)}>
                  <option value="sabre">SABRE</option>
                  <option value="greedy">Greedy</option>
                </select>
              </div>
            </div>

            <div className="card border-accent/30 bg-accent/5">
              <div className="card-title text-accent">Advanced: Hardware & Noise</div>
              <div className="config-row">
                <label>Mock Device</label>
                <select className="config-input w-36" value={deviceBackend} onChange={(e) => setDeviceBackend(e.target.value)}>
                  <option value="">None (Custom)</option>
                  <option value="ideal">Ideal Profile</option>
                  <option value="fake_5q">IBM Fake 5Q</option>
                  <option value="fake_7q">IBM Fake 7Q</option>
                </select>
              </div>
              
              {!deviceBackend && (
                <>
                  <div className="config-row mt-3">
                    <label>Depolarizing P</label>
                    <input type="number" step="0.01" max="1" min="0" className="config-input w-20" value={noiseDepol} onChange={(e) => setNoiseDepol(Number(e.target.value))} />
                  </div>
                  <div className="config-row">
                    <label>Readout Error</label>
                    <input type="number" step="0.01" max="1" min="0" className="config-input w-20" value={noiseReadout} onChange={(e) => setNoiseReadout(Number(e.target.value))} />
                  </div>
                  <div className="config-row">
                    <label>Amp Damping</label>
                    <input type="number" step="0.01" max="1" min="0" className="config-input w-20" value={noiseAmpDamp} onChange={(e) => setNoiseAmpDamp(Number(e.target.value))} />
                  </div>
                  <div className="config-row">
                    <label>Phase Damping</label>
                    <input type="number" step="0.01" max="1" min="0" className="config-input w-20" value={noisePhaseDamp} onChange={(e) => setNoisePhaseDamp(Number(e.target.value))} />
                  </div>
                </>
              )}
            </div>
            
            <div className="card">
              <div className="card-title">Analysis</div>
              <div className="text-sm mb-1 text-text-muted">Pauli Expectation (JSON)</div>
              <input 
                type="text" 
                className="config-input w-full" 
                value={expectationPauli} 
                onChange={(e) => setExpectationPauli(e.target.value)} 
                placeholder='{"ZZ": -1.0}' 
              />
            </div>
          </div>
        </div>

        {/* Right: Visualizations & Output */}
        <div className="w-[40%] bg-bg-base overflow-y-auto flex flex-col min-w-0">
          <div className="panel-header flex justify-between">
            <span>Inspector</span>
            <button className="btn btn-primary !py-1 !px-4 flex gap-1.5 items-center" onClick={handleRun} disabled={isSimulating}>
              <Play size={14} className={isSimulating ? "animate-pulse" : ""} /> 
              {isSimulating ? "Running..." : "Run"}
            </button>
          </div>
          
          <div className="p-4 flex flex-col gap-4">
            {results ? (
              <>
                {results.circuit_plot && (
                  <div className="card">
                    <div className="card-title">Circuit Topology</div>
                    <div className="bg-bg-panel border border-border-color p-2 rounded flex justify-center overflow-auto dark:invert dark:hue-rotate-180">
                      <img src={`data:image/png;base64,${results.circuit_plot}`} alt="Circuit Diagram" className="max-w-full" />
                    </div>
                  </div>
                )}
                
                {results.histogram_plot && (
                  <div className="card">
                    <div className="card-title">Probabilities</div>
                    <div className="bg-bg-panel border border-border-color p-2 rounded flex justify-center overflow-auto dark:invert dark:hue-rotate-180">
                      <img src={`data:image/png;base64,${results.histogram_plot}`} alt="Histogram" className="max-w-full" />
                    </div>
                  </div>
                )}
                
                {results.openqasm2 && (
                  <div className="card">
                    <div className="card-title">OpenQASM 2.0 Export</div>
                    <pre className="text-xs bg-code-bg p-3 rounded border border-border-color overflow-x-auto">
                      {results.openqasm2}
                    </pre>
                  </div>
                )}
                
                <div className="card">
                  <div className="card-title">Classical Memory</div>
                  <pre className="text-xs bg-code-bg p-3 rounded border border-border-color overflow-x-auto">
                    {JSON.stringify(results.classical_memory, null, 2)}
                  </pre>
                </div>
              </>
            ) : (
              <div className="h-48 flex items-center justify-center text-text-muted text-sm border-2 border-dashed border-border-color rounded-md m-2">
                Run a simulation to view results
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Terminal Block */}
      <div className="h-48 bg-code-bg border-t border-border-color flex flex-col shrink-0">
        <div className="h-8 bg-bg-panel border-b border-border-color flex items-center px-3 gap-2">
          <TerminalSquare size={14} className="text-text-muted" />
          <span className="text-xs font-semibold text-text-muted">TERMINAL OUTPUT</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 font-mono text-xs">
          {logs.length === 0 && <span className="text-text-muted opacity-50">No execution logs...</span>}
          {logs.map((log, i) => (
            <div key={i} className="mb-1 flex gap-3">
              <span className="text-text-muted shrink-0">[{log.time}]</span>
              <span className={
                log.type === "error" ? "text-[#f85149]" : 
                log.type === "success" ? "text-[#3fb950]" : "text-[#c9d1d9]"
              }>
                {log.msg}
              </span>
            </div>
          ))}
          <div ref={terminalEndRef} />
        </div>
      </div>

    </div>
  );
}

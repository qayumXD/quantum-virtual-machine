"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Activity, Clock, Zap } from "lucide-react";

type RunHistory = {
  id: string;
  created_at: string;
  engine: string;
  num_qubits: number;
  num_gates: number;
  shots: number;
  execution_time_ms: number;
};

export default function HistoryPage() {
  const [history, setHistory] = useState<RunHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("https://quantum-virtual-machine.onrender.com/history?limit=50")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data.history)) {
          setHistory(data.history);
        } else {
          console.error("Backend returned invalid history format:", data);
        }
      })
      .catch((err) => console.error("Failed to load history", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-full w-full">
      <div className="h-12 border-b border-border-color bg-bg-panel flex items-center justify-between px-4 shrink-0">
        <Link href="/" className="text-text-muted hover:text-text-main flex items-center gap-1 text-sm font-medium transition-colors">
          <ArrowLeft size={16} /> Back to Workspace
        </Link>
        <div className="flex items-center gap-2 text-accent text-sm font-semibold">
          <Activity size={16} />
          Execution Logs
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full">
        <h1 className="text-3xl font-bold mb-2 text-text-main">Simulation History</h1>
        <p className="text-text-muted mb-8">A comprehensive log of all quantum executions routed through the QVM Backend.</p>

        {loading ? (
          <div className="text-text-muted animate-pulse">Fetching records from Supabase...</div>
        ) : history.length === 0 ? (
          <div className="text-text-muted p-8 border border-dashed border-border-color rounded text-center">
            No execution data found. Run a simulation first!
          </div>
        ) : (
          <div className="border border-border-color rounded-md bg-bg-panel overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-bg-base border-b border-border-color text-text-muted">
                <tr>
                  <th className="px-4 py-3 font-medium">Timestamp</th>
                  <th className="px-4 py-3 font-medium">Engine</th>
                  <th className="px-4 py-3 font-medium">Qubits</th>
                  <th className="px-4 py-3 font-medium">Gates</th>
                  <th className="px-4 py-3 font-medium">Shots</th>
                  <th className="px-4 py-3 font-medium text-right">Execution Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-color">
                {history.map((run) => (
                  <tr key={run.id} className="hover:bg-border-color/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted whitespace-nowrap">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-accent/20 text-accent px-2 py-0.5 rounded text-xs uppercase tracking-wider font-semibold">
                        {run.engine}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">{run.num_qubits}</td>
                    <td className="px-4 py-3 font-mono">{run.num_gates}</td>
                    <td className="px-4 py-3 font-mono text-text-muted">{run.shots.toLocaleString()}</td>
                    <td className="px-4 py-3 font-mono text-right flex items-center justify-end gap-1.5">
                      <Clock size={12} className="text-text-muted" />
                      {run.execution_time_ms.toFixed(1)}ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

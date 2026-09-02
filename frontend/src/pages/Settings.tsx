import React, { useState } from "react";
import { Settings as SettingsIcon, Sliders, ShieldCheck } from "lucide-react";

export function Settings() {
  const [threshold, setThreshold] = useState(0.80);
  const [actor, setActor] = useState("administrator");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Auditor System Settings</h1>
        <p className="text-xs text-slate-400">
          Configure vector similarity thresholds, default frameworks, and human approval preferences
        </p>
      </div>

      <div className="glass-panel p-6 max-w-2xl space-y-6">
        <div className="space-y-4 border-b border-slate-800 pb-5">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Sliders className="h-4 w-4 text-cyan-400" /> Embedding Similarity Classification Threshold
          </h3>
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-2">
              <span>Automatic Classification Threshold:</span>
              <strong className="text-purple-400 font-mono">{Math.round(threshold * 100)}%</strong>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
            <p className="text-[11px] text-slate-500 mt-2">
              Commands with cosine similarity ≥ {Math.round(threshold * 100)}% are auto-classified. Commands below threshold are routed to the Interactive Training Center.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Compliance Framework Strategy
          </h3>
          <div className="space-y-2 text-xs">
            <div className="p-3 bg-slate-950 rounded border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-200">CIS Benchmark Controls v1.0</p>
                <p className="text-slate-500 text-[11px]">Primary active rule set (20 controls + absence-aware rules)</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                ACTIVE
              </span>
            </div>

            <div className="p-3 bg-slate-950 rounded border border-slate-800 flex items-center justify-between opacity-60">
              <div>
                <p className="font-bold text-slate-300">NIST SP 800-53 / DISA STIG</p>
                <p className="text-slate-500 text-[11px]">Extensible framework specification (Post-MVP)</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                EXTENSIBLE
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

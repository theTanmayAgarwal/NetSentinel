import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Server, ShieldCheck, ArrowLeft, Terminal, AlertTriangle } from "lucide-react";
import { getDeviceDetail } from "../services/api";

export function DeviceDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    if (id) {
      getDeviceDetail(Number(id)).then(setData).catch(console.error);
    }
  }, [id]);

  if (!data) {
    return (
      <div className="p-6 text-slate-400 text-xs flex items-center gap-2">
        <span className="h-4 w-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
        Loading device details...
      </div>
    );
  }

  const { device, latest_audit } = data;

  return (
    <div className="space-y-6">
      <Link to="/devices" className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Devices Inventory
      </Link>

      <div className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-cyan-500">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 rounded-xl text-cyan-400 border border-cyan-500/30">
            <Server className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">{device.hostname || "router-01"}</h1>
            <p className="text-xs text-slate-400 uppercase font-mono">Vendor: {device.vendor}</p>
          </div>
        </div>

        {latest_audit && (
          <div className="flex items-center gap-4 text-right">
            <div>
              <p className="text-xs text-slate-400">Latest Compliance Score</p>
              <p className="text-2xl font-bold text-cyan-400">{latest_audit.summary?.score}%</p>
            </div>
          </div>
        )}
      </div>

      {latest_audit && (
        <div className="glass-panel p-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-200">Latest Audit Findings ({latest_audit.findings?.length || 0})</h3>
          <div className="space-y-3">
            {latest_audit.findings?.map((f: any, idx: number) => (
              <div key={idx} className="p-4 rounded bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-400">{f.control_id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      f.status === "PASS"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {f.status}
                  </span>
                  <span className="text-xs font-semibold text-slate-200">{f.title}</span>
                </div>
                <p className="text-xs text-slate-400">{f.explanation}</p>
                {f.evidence && f.evidence[0] && (
                  <p className="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded inline-block">
                    Exact Line {f.evidence[0].line_number || "N/A"}: {f.evidence[0].source_line}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { AlertTriangle, Filter, Terminal } from "lucide-react";
import { getFindings, type Finding } from "../services/api";

export function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [vendorFilter, setVendorFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    getFindings({
      severity: severityFilter || undefined,
      vendor: vendorFilter || undefined,
      status: statusFilter || undefined,
    })
      .then(setFindings)
      .catch(console.error);
  }, [severityFilter, vendorFilter, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Security Control Findings</h1>
          <p className="text-xs text-slate-400">
            Cross-vendor compliance findings with exact line evidence and deterministic solutions
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={vendorFilter}
            onChange={(e) => setVendorFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">All Vendors</option>
            <option value="cisco">Cisco</option>
            <option value="juniper">Juniper</option>
            <option value="fortinet">Fortinet</option>
            <option value="aruba">HPE Aruba</option>
            <option value="dell">Dell OS10</option>
            <option value="unknown">Unknown</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="PASS">PASS</option>
            <option value="FAIL">FAIL</option>
            <option value="UNMAPPED">UNMAPPED</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      <div className="glass-panel p-5 space-y-4">
        <div className="space-y-3">
          {findings.map((f, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-400">{f.control_id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      f.severity === "CRITICAL"
                        ? "bg-red-500/20 text-red-400 border border-red-500/40"
                        : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                    }`}
                  >
                    {f.severity}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      f.status === "PASS"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                        : f.status === "UNMAPPED"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        : "bg-red-500/20 text-red-400 border border-red-500/40"
                    }`}
                  >
                    {f.status}
                  </span>
                  <span className="text-xs font-semibold text-slate-200">{f.title}</span>
                </div>

                <span className="text-[10px] font-mono text-slate-400 uppercase">
                  Vendor: {f.vendor || "Cisco"}
                </span>
              </div>

              {/* Multi-Framework Security Benchmark Mappings */}
              <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-cyan-300 border border-cyan-500/30">
                  CIS: {f.control_id}
                </span>
                {f.nist_mapping && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-purple-300 border border-purple-500/30">
                    NIST: {f.nist_mapping}
                  </span>
                )}
                {f.disa_stig_mapping && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-amber-300 border border-amber-500/30">
                    STIG: {f.disa_stig_mapping}
                  </span>
                )}
                {f.iso_mapping && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-emerald-300 border border-emerald-500/30">
                    ISO: {f.iso_mapping}
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{f.explanation}</p>

              <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400 bg-slate-900/90 p-2 rounded border border-slate-800">
                <span>Expected: <strong className="text-emerald-400">{f.expected || "N/A"}</strong></span>
                <span className="text-slate-600">|</span>
                <span>Observed: <strong className={f.status === "PASS" ? "text-emerald-400" : "text-amber-400"}>{f.observed || "N/A"}</strong></span>
              </div>

              {f.evidence && f.evidence[0] && (
                <div className="p-2 bg-slate-900 rounded font-mono text-[11px] text-slate-400 border border-slate-800/80">
                  Exact Evidence: <span className="text-slate-200">{typeof f.evidence[0] === "string" ? f.evidence[0] : f.evidence[0].source_line}</span>
                </div>
              )}

              {/* MANDATORY SOLUTION BLOCK */}
              <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded text-xs space-y-1">
                <p className="font-bold text-emerald-400 flex items-center gap-1 text-[11px]">
                  <Terminal className="h-3 w-3" /> SOLUTION:
                </p>
                <p className="text-emerald-200">
                  {f.remediation?.description || `Configure ${f.title} according to security benchmark criteria.`}
                </p>
                {f.remediation?.commands && (
                  <pre className="font-mono text-emerald-300 text-[11px] mt-1 bg-slate-950 p-2 rounded border border-slate-800">
                    {f.remediation.commands.join("\n")}
                  </pre>
                )}
              </div>
            </div>
          ))}

          {findings.length === 0 && (
            <div className="p-8 text-center text-slate-500 text-xs">
              No findings matched the selected filters. Run a configuration audit or adjust filters above.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


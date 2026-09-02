import React, { useEffect, useState } from "react";
import { FileSpreadsheet, Download, FileText, Code } from "lucide-react";
import { getAudits } from "../services/api";

export function Reports() {
  const [audits, setAudits] = useState<any[]>([]);

  useEffect(() => {
    getAudits().then(setAudits).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Audit Reports & Export Center</h1>
        <p className="text-xs text-slate-400">
          Download executive audit reports in PDF, CSV, or JSON format for internal compliance reviews
        </p>
      </div>

      <div className="glass-panel p-5">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Audit ID</th>
                <th className="p-3">Filename</th>
                <th className="p-3">Vendor</th>
                <th className="p-3">Device Hostname</th>
                <th className="p-3">Compliance Score</th>
                <th className="p-3">Audit Date</th>
                <th className="p-3">Download Exports</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {audits.map((a) => (
                <tr key={a.id} className="hover:bg-slate-800/40">
                  <td className="p-3 text-cyan-400 font-bold">#{a.id}</td>
                  <td className="p-3 font-semibold text-slate-100">{a.filename}</td>
                  <td className="p-3 uppercase text-slate-300 font-sans">{a.vendor}</td>
                  <td className="p-3 font-sans text-slate-200">{a.hostname || "router-01"}</td>
                  <td className="p-3 font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                      {a.score}%
                    </span>
                  </td>
                  <td className="p-3 text-slate-400">{a.created_at?.slice(0, 10) || "Today"}</td>
                  <td className="p-3 font-sans">
                    <div className="flex items-center gap-2">
                      <a
                        href={`/api/reports/pdf/${a.id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-500/40 rounded text-[11px] font-bold flex items-center gap-1"
                      >
                        <FileText className="h-3 w-3" /> PDF
                      </a>
                      <a
                        href={`/api/reports/csv/${a.id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-500/40 rounded text-[11px] font-bold flex items-center gap-1"
                      >
                        <Download className="h-3 w-3" /> CSV
                      </a>
                      <a
                        href={`/api/reports/json/${a.id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 bg-purple-950/60 hover:bg-purple-900/80 text-purple-300 border border-purple-500/40 rounded text-[11px] font-bold flex items-center gap-1"
                      >
                        <Code className="h-3 w-3" /> JSON
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
              {audits.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-4 text-center text-slate-500 font-sans">
                    No completed audit reports found. Run an audit from the Audits page.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

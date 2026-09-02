import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  Server,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  BrainCircuit,
  ArrowRight,
  Upload,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { getAudits, getDevices, getFindings, getTGR } from "../services/api";

export function Dashboard() {
  const [audits, setAudits] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [tgr, setTgr] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getAudits().catch(() => []),
      getDevices().catch(() => []),
      getFindings({ limit: 10 }).catch(() => []),
      getTGR().catch(() => null),
    ]).then(([auditsData, devicesData, findingsData, tgrData]) => {
      setAudits(auditsData);
      setDevices(devicesData);
      setFindings(findingsData);
      setTgr(tgrData);
      setLoading(false);
    });
  }, []);

  const totalAudits = audits.length;
  const avgScore = totalAudits
    ? Math.round(audits.reduce((acc, a) => acc + (a.score || 0), 0) / totalAudits)
    : 78;

  const totalCritical = findings.filter((f) => f.severity === "CRITICAL" || f.status === "CRITICAL").length;
  const totalFailed = findings.filter((f) => f.status === "FAIL").length;
  const totalUnmapped = findings.filter((f) => f.status === "UNMAPPED").length;
  const totalPassed = findings.filter((f) => f.status === "PASS").length;

  const vendorData = [
    { name: "Cisco", score: 65 },
    { name: "Juniper", score: 85 },
    { name: "Fortinet", score: 90 },
    { name: "HPE Aruba", score: 88 },
    { name: "Dell OS10", score: 92 },
  ];

  const severityPieData = [
    { name: "Passed", value: totalPassed || 14, color: "#10b981" },
    { name: "Failed", value: totalFailed || 4, color: "#f59e0b" },
    { name: "Unmapped", value: totalUnmapped || 2, color: "#8b5cf6" },
    { name: "Critical", value: totalCritical || 2, color: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100">SOC Security Operations Center</h1>
          <p className="text-xs text-slate-400">
            Real-time multi-vendor compliance status & adaptive security-semantic memory
          </p>
        </div>

        <Link
          to="/audits"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-semibold shadow-glow transition-all"
        >
          <Upload className="h-4 w-4" /> Run New Audit
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="glass-panel p-4 border-l-4 border-l-cyan-500">
          <p className="text-xs font-medium text-slate-400">Overall Compliance</p>
          <p className="text-2xl font-bold text-cyan-400 mt-1">{avgScore}%</p>
          <p className="text-[10px] text-slate-500 mt-0.5">CIS Benchmark Controls</p>
        </div>

        <div className="glass-panel p-4 border-l-4 border-l-emerald-500">
          <p className="text-xs font-medium text-slate-400">Devices Audited</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{devices.length || totalAudits || 5}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Cisco · Juniper · Fortinet · Aruba · Dell</p>
        </div>

        <div className="glass-panel p-4 border-l-4 border-l-amber-500">
          <p className="text-xs font-medium text-slate-400">Unmapped Controls</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{totalUnmapped}</p>
          <p className="text-[10px] text-amber-300/80 mt-0.5">Requires Verified Mapping</p>
        </div>

        <div className="glass-panel p-4 border-l-4 border-l-red-500">
          <p className="text-xs font-medium text-slate-400">Critical Findings</p>
          <p className="text-2xl font-bold text-red-400 mt-1">{totalCritical}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Requires immediate fix</p>
        </div>

        <div className="glass-panel p-4 border-l-4 border-l-purple-500">
          <p className="text-xs font-medium text-slate-400">Adaptive Memory (TGR)</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">{tgr?.tgr_percentage ?? 100}%</p>
          <p className="text-[10px] text-purple-300 mt-0.5">Active Verified Mappings</p>
        </div>
      </div>

      {/* Hero Interactive Feature Teaser Banner */}
      <div className="mb-6 rounded-xl bg-gradient-to-r from-purple-950/80 via-slate-900 to-cyan-950/80 border border-purple-500/30 p-5 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
              ADAPTIVE MEMORY
            </span>
            <h3 className="text-sm font-semibold text-slate-100">
              Human-in-the-Loop Semantic Learning & Unknown Syntax Resolution
            </h3>
          </div>
          <p className="text-xs text-slate-300 max-w-2xl">
            Encountered unknown vendor syntax? AI proposes its security meaning. Administrator verifies once, and the system remembers the verified mapping for future audits — <strong>zero code redeployment required.</strong>
          </p>
        </div>

        <Link
          to="/training"
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-bold shadow-glow transition-all shrink-0"
        >
          <BrainCircuit className="h-4 w-4" /> Open Training Center <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="glass-panel p-5 col-span-2">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">
            Compliance Score by Preset Vendor (%)
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vendorData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }}
                />
                <Bar dataKey="score" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">
            Findings Breakdown
          </h3>
          <div className="h-56 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {severityPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Findings Table */}
      <div className="glass-panel p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-200">Recent Audit Findings</h3>
          <Link to="/findings" className="text-xs text-cyan-400 hover:underline">
            View All Findings →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Control ID</th>
                <th className="p-3">Title</th>
                <th className="p-3">Vendor / Device</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {findings.slice(0, 5).map((f, i) => (
                <tr key={i} className="hover:bg-slate-800/40">
                  <td className="p-3 font-mono font-medium text-cyan-400">{f.control_id}</td>
                  <td className="p-3 font-medium text-slate-200">{f.title}</td>
                  <td className="p-3 uppercase text-slate-400">{f.vendor || "Cisco"}</td>
                  <td className="p-3 font-sans">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        f.severity === "CRITICAL"
                          ? "bg-red-500/20 text-red-400 border border-red-500/40"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      }`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="p-3 font-sans">
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
                  </td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-slate-500 font-sans">
                    No audits executed yet. Click "Run New Audit" above to analyze configurations.
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


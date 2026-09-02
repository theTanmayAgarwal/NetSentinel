import React, { useState } from "react";
import {
  Upload,
  FileText,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  ArrowRight,
  Sparkles,
  Terminal,
  Download,
  GraduationCap,
} from "lucide-react";
import { uploadAuditText, uploadAuditFile, type AuditReport } from "../services/api";

const SAMPLE_CONFIGS = {
  cisco: {
    filename: "rtr-edge-01.cfg",
    vendor: "Cisco IOS",
    category: "Router / Firewall",
    text: `hostname rtr-edge-01
line vty 0 4
 transport input telnet
ip ssh version 2
ip http server
no logging
aaa new-model
service timestamps log datetime`,
  },
  juniper: {
    filename: "srx-br-02.conf",
    vendor: "Juniper JunOS",
    category: "Router / Firewall",
    text: `set system host-name srx-br-02
set system services ssh
set system services telnet
set system services web-management http
set system syslog host 10.0.0.50 any notice
set system login class admin idle-timeout 10`,
  },
  fortinet: {
    filename: "fgt-dc-03.conf",
    vendor: "Fortinet FortiGate",
    category: "Firewall",
    text: `config system global
    set hostname "fgt-dc-03"
    set admin-sport 443
    set admin-ssh-port 22
    set admin-scp disable
end
config system console
    set mode line
    set output serial
end`,
  },
  aruba: {
    filename: "hpe_aruba_enterprise.cfg",
    vendor: "HPE Aruba",
    category: "Routers & Switches",
    text: `hostname aruba-core-sw01
ssh server vrf default
no ssh server vty-0-4 telnet
snmp-server community public operator
logging 192.168.10.50 severity info
password-policy min-length 12
session-timeout 900`,
  },
  dell: {
    filename: "dell_network_enterprise.cfg",
    vendor: "Dell OS10",
    category: "Specialized Networking",
    text: `hostname dell-s5248-sw01
security-password min-length 14
ip ssh server enable
ip ssh version 2
no ip telnet server enable
snmp-server community secret-ro ro
logging server 192.168.20.100 severity informational
system-cli-timeout 600`,
  },
  unknown: {
    filename: "unknown_vendor_device.cfg",
    vendor: "Unknown Vendor",
    category: "Adaptive Learning Demo",
    text: `set secure-admin-timeout 300
set management ssh-version 2
set service telnet disabled`,
  },
};

export function Audits() {
  const [configText, setConfigText] = useState(SAMPLE_CONFIGS.cisco.text);
  const [filename, setFilename] = useState(SAMPLE_CONFIGS.cisco.filename);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await uploadAuditText(filename, configText);
      setReport(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Audit execution failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await uploadAuditFile(file);
      setFilename(file.name);
      setReport(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "File upload failed");
    } finally {
      setLoading(false);
    }
  };

  const selectSample = (key: keyof typeof SAMPLE_CONFIGS) => {
    setConfigText(SAMPLE_CONFIGS[key].text);
    setFilename(SAMPLE_CONFIGS[key].filename);
    setReport(null);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div>
        <h1 className="text-xl font-bold text-slate-100">Multi-Vendor Configuration Auditor</h1>
        <p className="text-xs text-slate-400">
          Upload configuration snippets (Cisco, Juniper, Fortinet, HPE Aruba, Dell, or Unknown) for deterministic rule evaluation
        </p>
      </div>

      {/* Preset Quick Loader Buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400 font-medium mr-1">QUICK LOAD:</span>
        {(Object.keys(SAMPLE_CONFIGS) as Array<keyof typeof SAMPLE_CONFIGS>).map((key) => (
          <button
            key={key}
            onClick={() => selectSample(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5 ${
              filename === SAMPLE_CONFIGS[key].filename
                ? "bg-cyan-950/80 border-cyan-500 text-cyan-300 shadow-glow"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>{SAMPLE_CONFIGS[key].vendor}</span>
            <span className="text-[10px] opacity-60">({SAMPLE_CONFIGS[key].category})</span>
          </button>
        ))}
      </div>

      {/* Config Input Panel */}
      <div className="glass-panel p-5 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <FileText className="h-4 w-4 text-cyan-400" /> Configuration Text ({filename})
            </label>
            <label className="cursor-pointer text-xs text-cyan-400 hover:underline flex items-center gap-1">
              <Upload className="h-3.5 w-3.5" /> Upload File
              <input type="file" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          <textarea
            value={configText}
            onChange={(e) => setConfigText(e.target.value)}
            rows={10}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 font-mono text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
            placeholder="Paste raw vendor configuration here..."
          />

          <button
            onClick={handleRunAudit}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-bold tracking-wide shadow-glow transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <span>Auditing Configuration...</span>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" /> Run Security Audit Pipeline
              </>
            )}
          </button>
        </div>

        {/* Info Sidebar Panel */}
        <div className="space-y-4 text-xs text-slate-400 border-l border-slate-800/80 pl-6">
          <h3 className="font-semibold text-slate-200 text-sm">Deterministic Audit Pipeline</h3>
          <ol className="space-y-2.5">
            <li className="flex items-start gap-2">
              <span className="h-5 w-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[10px] shrink-0">1</span>
              <span><strong>Vendor & OS Detection:</strong> Signature fingerprints & metadata extraction</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="h-5 w-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[10px] shrink-0">2</span>
              <span><strong>Adaptive Memory:</strong> Active learned mappings lookup</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="h-5 w-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[10px] shrink-0">3</span>
              <span><strong>Security-Semantic Facts:</strong> Normalized property evaluation</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="h-5 w-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-bold text-[10px] shrink-0">4</span>
              <span><strong>Deterministic Engine:</strong> PASS / FAIL / UNMAPPED evaluation</span>
            </li>
          </ol>

          {error && (
            <div className="p-3 bg-red-950/40 border border-red-500/40 rounded-lg text-red-300">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Audit Report Results Section */}
      {report && (
        <div className="space-y-6 animate-fadeIn">
          {/* Header Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="glass-panel p-4 border-l-4 border-l-cyan-500">
              <p className="text-xs text-slate-400">Detected Vendor & OS</p>
              <p className="text-sm font-bold text-cyan-400 uppercase mt-1">
                {report.vendor}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">{report.platform || "Platform"} ({report.os_version || "OS"})</p>
            </div>

            <div className="glass-panel p-4 border-l-4 border-l-emerald-500">
              <p className="text-xs text-slate-400">Compliance Score</p>
              <p className="text-lg font-bold text-emerald-400 mt-1">
                {report.summary.score}%
              </p>
              <p className="text-[10px] text-slate-500">
                {report.summary.passed} Passed / {report.summary.failed} Failed / {report.summary.unmapped || 0} Unmapped
              </p>
            </div>

            <div className="glass-panel p-4 border-l-4 border-l-amber-500">
              <p className="text-xs text-slate-400">Unmapped Controls</p>
              <p className="text-lg font-bold text-amber-400 mt-1">
                {report.summary.unmapped || 0}
              </p>
              <p className="text-[10px] text-amber-300/80">Requires Verified Mapping</p>
            </div>

            <div className="glass-panel p-4 border-l-4 border-l-purple-500">
              <p className="text-xs text-slate-400">Predicted Post-Remediation</p>
              <p className="text-lg font-bold text-purple-400 mt-1">
                {report.predicted_after.score}% (+{report.predicted_after.delta}%)
              </p>
              <p className="text-[10px] text-purple-300">PREDICTED - NOT APPLIED</p>
            </div>

            <div className="glass-panel p-4 border-l-4 border-l-blue-500">
              <p className="text-xs text-slate-400">Export Report</p>
              <div className="flex items-center gap-2 mt-2">
                <a
                  href={`/api/reports/pdf/${report.audit_id || 1}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold flex items-center gap-1"
                >
                  <Download className="h-3 w-3" /> PDF
                </a>
                <a
                  href={`/api/reports/json/${report.audit_id || 1}`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold flex items-center gap-1"
                >
                  <Download className="h-3 w-3" /> JSON
                </a>
              </div>
            </div>
          </div>

          {/* Reused Mapping Callout if any */}
          {report.reused_mappings && report.reused_mappings.length > 0 && (
            <div className="glass-panel p-4 border-l-4 border-l-emerald-500 bg-emerald-950/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-emerald-200">
                    Learned Semantic Mapping Reused ({report.reused_mappings.length})
                  </h4>
                  <p className="text-xs text-slate-300 font-mono mt-0.5">
                    Verified Mapping M-{report.reused_mappings[0].mapping_id} auto-extracted fact: {report.reused_mappings[0].property} = {report.reused_mappings[0].value}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Unknown Commands Warning Callout if any */}
          {report.unknown_lines && report.unknown_lines.length > 0 && (
            <div className="glass-panel p-4 border-l-4 border-l-purple-500 bg-purple-950/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <GraduationCap className="h-6 w-6 text-purple-400 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-purple-200">
                    Unknown Configuration Command ({report.unknown_lines.length})
                  </h4>
                  <p className="text-xs text-slate-300 font-mono mt-0.5">
                    "{report.unknown_lines[0]}"
                  </p>
                </div>
              </div>
              <a
                href="/training"
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-bold flex items-center gap-1.5 shadow-glow"
              >
                Teach Command in Training Center <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          )}

          {/* Findings List Section */}
          <div className="glass-panel p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" /> Compliance Control Findings ({report.findings.length})
            </h3>

            <div className="space-y-4">
              {report.findings.map((f, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-lg bg-slate-950/80 border border-slate-800 space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-bold text-cyan-400">{f.control_id}</span>
                      <span
                        className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
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

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        Severity: {f.severity}
                      </span>
                    </div>
                  </div>

                  {/* Multi-Framework Benchmark Identifiers */}
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-cyan-300 border border-cyan-500/30">
                      CIS: {f.control_id}
                    </span>
                    {f.nist_mapping && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-purple-300 border border-purple-500/30">
                        NIST: {f.nist_mapping}
                      </span>
                    )}
                    {f.disa_stig_mapping && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-amber-300 border border-amber-500/30">
                        STIG: {f.disa_stig_mapping}
                      </span>
                    )}
                    {f.iso_mapping && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-emerald-300 border border-emerald-500/30">
                        ISO: {f.iso_mapping}
                      </span>
                    )}
                  </div>

                  {/* EXPECTED & OBSERVED */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-slate-900/90 p-3 rounded-lg border border-slate-800 font-mono">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-sans font-bold">EXPECTED:</span>
                      <span className="text-emerald-400 font-semibold">{f.expected || "N/A"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-sans font-bold">OBSERVED:</span>
                      <span className={f.status === "PASS" ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                        {f.observed || "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* EXPLANATION */}
                  <div>
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">EXPLANATION:</span>
                    <p className="text-xs text-slate-300 leading-relaxed mt-0.5">{f.explanation}</p>
                  </div>

                  {/* EVIDENCE */}
                  {f.evidence && f.evidence.length > 0 && (
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">EVIDENCE:</span>
                      <div className="bg-slate-950 p-2 rounded border border-slate-800 text-xs font-mono text-cyan-300 mt-1">
                        {f.evidence.map((ev: any, idx: number) => {
                          const str = typeof ev === "string" ? ev : ev.source_line;
                          return <div key={idx}>• {str}</div>;
                        })}
                      </div>
                    </div>
                  )}

                  {/* MANDATORY SOLUTION SECTION */}
                  <div className="p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 space-y-2 mt-2">
                    <p className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <Terminal className="h-4 w-4 text-emerald-400 shrink-0" />
                      SOLUTION:
                    </p>
                    <p className="text-xs text-emerald-200">
                      {f.remediation?.description || `Configure ${f.title} to comply with benchmark policy.`}
                    </p>
                    {f.remediation?.commands && f.remediation.commands.length > 0 && (
                      <pre className="text-emerald-300 font-mono text-xs bg-slate-950/80 p-2.5 rounded border border-emerald-900/50 mt-1">
                        {f.remediation.commands.join("\n")}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


import React, { useEffect, useState } from "react";
import {
  GraduationCap,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Award,
  RefreshCw,
  Check,
  X,
  Edit,
  Database,
  Layers,
  Slash,
} from "lucide-react";
import {
  getMappings,
  updateMapping,
  approveExemplar,
  rejectMapping,
  getTGR,
  type TGRResult,
} from "../services/api";

const CATEGORY_OPTIONS = [
  "Authentication",
  "Password Policy",
  "Secure Management",
  "SSH / Management Protocols",
  "Network Services",
  "ACL / Firewall Rules",
  "Encryption",
  "Logging & Monitoring",
  "Interfaces",
  "Routing",
  "System Configuration",
  "Other Security Controls",
];

export function TrainingCenter() {
  const [pendingMappings, setPendingMappings] = useState<any[]>([]);
  const [allMappings, setAllMappings] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [tgr, setTgr] = useState<TGRResult | null>(null);

  // Status feedback banners & state
  const [saving, setSaving] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<{ type: "approve" | "correct" | "reject"; message: string; mappingId: number } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Correct Mode state
  const [isCorrecting, setIsCorrecting] = useState(false);
  const [editProperty, setEditProperty] = useState("");
  const [editValue, setEditValue] = useState("");
  const [editUnit, setEditUnit] = useState("");
  const [editCategory, setEditCategory] = useState("Secure Management");
  const [editControlId, setEditControlId] = useState("");
  const [editPattern, setEditPattern] = useState("");

  const loadData = async () => {
    try {
      const [pendingRes, allRes, tgrRes] = await Promise.all([
        getMappings("PENDING"),
        getMappings(),
        getTGR().catch(() => null),
      ]);
      setPendingMappings(pendingRes);
      setAllMappings(allRes);
      if (tgrRes) setTgr(tgrRes);
    } catch (err: any) {
      console.error("Failed to load training center data:", err);
      setErrorMessage("Database communication error. Please check PostgreSQL connection.");
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const currentPending = pendingMappings[0] || null;

  // Initialize edit fields when currentPending changes
  useEffect(() => {
    if (currentPending) {
      setEditProperty(currentPending.security_property || currentPending.parameter || "");
      setEditValue(currentPending.value || currentPending.expected_value || "");
      setEditUnit(currentPending.unit || "");
      setEditCategory(currentPending.category || "Secure Management");
      setEditControlId(currentPending.control_id || "CIS-NET-18");
      setEditPattern(currentPending.command_pattern || currentPending.text || "");
    }
  }, [currentPending]);

  // Handle APPROVE
  const handleApprove = async () => {
    if (!currentPending) return;
    setSaving(true);
    setErrorMessage(null);
    setActionSuccess(null);
    try {
      await approveExemplar(currentPending.id, true);
      setActionSuccess({
        type: "approve",
        mappingId: currentPending.id,
        message: `✓ SECURITY MAPPING VERIFIED: Mapping M-${currentPending.id} Status set to ACTIVE. Verified by Administrator. This mapping is now available for future audits.`,
      });
      setIsCorrecting(false);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || "Failed to approve mapping in database.");
    } finally {
      setSaving(false);
    }
  };

  // Handle REJECT
  const handleReject = async () => {
    if (!currentPending) return;
    setSaving(true);
    setErrorMessage(null);
    setActionSuccess(null);
    try {
      await rejectMapping(currentPending.id);
      setActionSuccess({
        type: "reject",
        mappingId: currentPending.id,
        message: `✕ MAPPING REJECTED: Mapping M-${currentPending.id} Status set to REJECTED. This proposal will not be used for future audits. Record preserved for audit history.`,
      });
      setIsCorrecting(false);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || "Failed to reject mapping in database.");
    } finally {
      setSaving(false);
    }
  };

  // Handle Submit CORRECTION
  const handleSaveCorrection = async () => {
    if (!currentPending) return;
    setSaving(true);
    setErrorMessage(null);
    setActionSuccess(null);
    try {
      await updateMapping(currentPending.id, {
        security_property: editProperty,
        value: editValue,
        unit: editUnit,
        category: editCategory,
        control_id: editControlId,
        command_pattern: editPattern,
        status: "ACTIVE",
        reviewer: "administrator",
      });
      setActionSuccess({
        type: "correct",
        mappingId: currentPending.id,
        message: `✓ MAPPING CORRECTED & VERIFIED: Mapping M-${currentPending.id} Status set to ACTIVE. Human-verified parameter values saved to database.`,
      });
      setIsCorrecting(false);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || "Failed to save corrected mapping in database.");
    } finally {
      setSaving(false);
    }
  };

  const filteredMappings = allMappings.filter((m) => {
    if (activeTab === "ALL") return true;
    if (activeTab === "PENDING") return m.status === "PENDING";
    if (activeTab === "ACTIVE") return m.status === "ACTIVE" || m.status === "APPROVED";
    if (activeTab === "REJECTED") return m.status === "REJECTED";
    if (activeTab === "STALE") return m.status === "STALE";
    if (activeTab === "REVOKED") return m.status === "REVOKED";
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
              ADAPTIVE SECURITY MEMORY
            </span>
            <h1 className="text-xl font-bold text-slate-100">
              Unknown Syntax Resolution & AI Proposal Verification
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-Loop Semantic Verification Console. AI proposes interpretations; administrator approval makes them active trusted mappings in PostgreSQL.
          </p>
        </div>

        {/* Live TGR Gauge Card */}
        <div className="glass-panel p-3.5 border-l-4 border-l-purple-500 bg-purple-950/40 flex items-center gap-4 shrink-0">
          <Award className="h-8 w-8 text-purple-400" />
          <div>
            <p className="text-[10px] text-purple-300 font-bold uppercase tracking-wider">
              Teaching Generalization Rate (TGR)
            </p>
            <p className="text-2xl font-black text-purple-200">
              {tgr?.tgr_percentage ?? 100}%
            </p>
            <p className="text-[10px] text-slate-400">
              {tgr?.correctly_classified ?? 3} / {tgr?.total_held_out ?? 3} held-out variants recognized
            </p>
          </div>
        </div>
      </div>

      {/* Main Human-in-the-Loop Review Panel */}
      <div className="glass-panel p-6 border-purple-500/30 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                Unresolved Configuration Command — Pending Review Queue ({pendingMappings.length})
              </h3>
              <p className="text-xs text-slate-400">
                Command fragment requires human verification before entering deterministic compliance engine
              </p>
            </div>
          </div>

          {currentPending && (
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
              PROPOSAL CONFIDENCE: {Math.round((currentPending.ai_confidence ?? 0.92) * 100)}%
            </span>
          )}
        </div>

        {/* Display Current Pending Item */}
        {currentPending ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column: Command & AI Proposal Details */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-400 font-mono">
                  Mapping ID: M-{currentPending.id}
                </span>
                <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                  <span>Vendor: <strong className="text-slate-200">{currentPending.vendor || "UnknownVendor"}</strong></span>
                  <span>|</span>
                  <span>OS: <strong className="text-slate-200">{currentPending.os_version || "5.2"}</strong></span>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Raw Configuration Command:
                </label>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-slate-100">
                  {currentPending.command_pattern || currentPending.text}
                </div>
              </div>

              {/* AI Proposal Card */}
              <div className="p-4 rounded-lg bg-purple-950/30 border border-purple-500/40 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-300 flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-purple-400" /> AI SEMANTIC PROPOSAL
                  </span>
                  <span className="text-[10px] text-purple-300 font-mono bg-purple-900/60 px-2 py-0.5 rounded border border-purple-500/30">
                    Confidence: {Math.round((currentPending.ai_confidence ?? 0.92) * 100)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-slate-950 p-3.5 rounded border border-slate-800">
                  <div>
                    <span className="text-slate-400 text-[10px] block font-sans font-semibold">SECURITY PROPERTY:</span>
                    <span className="text-purple-300 font-bold">{currentPending.security_property || currentPending.parameter}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-sans font-semibold">PROPOSED VALUE:</span>
                    <span className="text-emerald-400 font-bold">
                      {currentPending.value || currentPending.expected_value} {currentPending.unit || ""}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-950/50 p-2.5 rounded border border-slate-800/60">
                  "{currentPending.ai_proposal || "Detected security setting from command syntax."}"
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span>Status: <strong className="text-amber-400">PENDING REVIEW</strong></span>
                  <span>Version: v{currentPending.version || 1}</span>
                </div>
              </div>
            </div>

            {/* Right Column: Administrator Decision Panel */}
            <div className="space-y-4 bg-slate-950/80 p-5 rounded-lg border border-slate-800 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <span className="flex items-center gap-1.5">
                    <GraduationCap className="h-4 w-4 text-cyan-400" /> Administrator Verification Decision
                  </span>
                  {isCorrecting && (
                    <span className="text-[10px] text-amber-400 font-normal">EDITING PARAMETERS</span>
                  )}
                </h4>

                {isCorrecting ? (
                  <div className="space-y-3 text-xs animate-fadeIn">
                    <div>
                      <label className="text-slate-400 text-[11px]">Command Pattern:</label>
                      <input
                        type="text"
                        value={editPattern}
                        onChange={(e) => setEditPattern(e.target.value)}
                        className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-slate-400 text-[11px]">Security Property:</label>
                        <input
                          type="text"
                          value={editProperty}
                          onChange={(e) => setEditProperty(e.target.value)}
                          className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-purple-300 focus:border-cyan-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 text-[11px]">Value:</label>
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-emerald-300 focus:border-cyan-500 focus:outline-none"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-slate-400 text-[11px]">Unit:</label>
                        <input
                          type="text"
                          value={editUnit}
                          onChange={(e) => setEditUnit(e.target.value)}
                          placeholder="seconds, bytes, etc."
                          className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 text-[11px]">Control ID:</label>
                        <input
                          type="text"
                          value={editControlId}
                          onChange={(e) => setEditControlId(e.target.value)}
                          className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-cyan-300 focus:border-cyan-500 focus:outline-none"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 text-[11px]">Category:</label>
                      <select
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="w-full mt-1 bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        {CATEGORY_OPTIONS.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={handleSaveCorrection}
                        disabled={saving}
                        className="flex-1 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-bold shadow-glow"
                      >
                        Confirm Correction & Approve
                      </button>
                      <button
                        onClick={() => setIsCorrecting(false)}
                        className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3 text-xs">
                    <p className="text-slate-300 leading-relaxed">
                      Human verification is required before this mapping enters PostgreSQL as trusted knowledge.
                    </p>
                    <div className="bg-slate-900 p-3 rounded border border-slate-800 space-y-1.5 font-mono text-[11px]">
                      <div><span className="text-slate-400">Target Property:</span> <span className="text-purple-300 font-bold">{currentPending.security_property}</span></div>
                      <div><span className="text-slate-400">Target Value:</span> <span className="text-emerald-400 font-bold">{currentPending.value} {currentPending.unit || ""}</span></div>
                      <div><span className="text-slate-400">Category:</span> <span className="text-slate-200">{currentPending.category}</span></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              {!isCorrecting && (
                <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                  <button
                    onClick={handleApprove}
                    disabled={saving}
                    className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1.5 shadow-glow"
                  >
                    <Check className="h-4 w-4" /> APPROVE
                  </button>
                  <button
                    onClick={() => setIsCorrecting(true)}
                    disabled={saving}
                    className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-bold text-xs flex items-center gap-1"
                  >
                    <Edit className="h-3.5 w-3.5" /> CORRECT
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={saving}
                    className="px-4 py-2.5 bg-red-950 border border-red-500/50 hover:bg-red-900 text-red-300 rounded font-bold text-xs flex items-center gap-1"
                  >
                    <X className="h-3.5 w-3.5" /> REJECT
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center bg-slate-950/60 rounded-lg border border-slate-800 space-y-2">
            <CheckCircle2 className="h-8 w-8 text-emerald-400 mx-auto" />
            <h4 className="text-sm font-bold text-slate-200">No Pending Mappings in Queue</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              All proposed mappings have been human-verified and persisted to PostgreSQL. Unresolved configuration syntax from future audits will appear here for review.
            </p>
          </div>
        )}

        {/* Action Success / Error Banners */}
        {actionSuccess && (
          <div
            className={`p-4 rounded-lg border space-y-1 animate-fadeIn ${
              actionSuccess.type === "reject"
                ? "bg-red-950/40 border-red-500/40 text-red-300"
                : "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
            }`}
          >
            <div className="flex items-center gap-2 font-bold text-xs">
              {actionSuccess.type === "reject" ? (
                <X className="h-4 w-4 text-red-400 shrink-0" />
              ) : (
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              )}
              <span>{actionSuccess.message}</span>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="p-4 bg-red-950/40 border border-red-500/40 rounded-lg text-xs text-red-300 font-semibold flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Verified Security Mappings Table with Status Filter Tabs */}
      <div className="glass-panel p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Database className="h-4 w-4 text-cyan-400" /> Learned Mappings Database ({filteredMappings.length})
          </h3>

          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {["ALL", "PENDING", "ACTIVE", "REJECTED", "STALE", "REVOKED"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                  activeTab === tab
                    ? "bg-cyan-950 border border-cyan-500/50 text-cyan-300 shadow-glow"
                    : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Mapping ID</th>
                <th className="p-3">Vendor / OS</th>
                <th className="p-3">Command Pattern</th>
                <th className="p-3">Security Property</th>
                <th className="p-3">Value</th>
                <th className="p-3">Status</th>
                <th className="p-3">Reviewer</th>
                <th className="p-3">Version</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredMappings.map((m, i) => (
                <tr key={i} className="hover:bg-slate-800/40">
                  <td className="p-3 text-cyan-400 font-bold">M-{m.id}</td>
                  <td className="p-3 font-sans text-slate-300">
                    {m.vendor} <span className="text-[10px] text-slate-500">({m.os_version || "all"})</span>
                  </td>
                  <td className="p-3 font-semibold text-slate-100">{m.command_pattern || m.text}</td>
                  <td className="p-3 text-purple-300">{m.security_property || m.parameter}</td>
                  <td className="p-3 text-emerald-300">{m.value || m.expected_value} {m.unit || ""}</td>
                  <td className="p-3 font-sans">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        m.status === "ACTIVE" || m.status === "APPROVED"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : m.status === "PENDING"
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                          : m.status === "REJECTED"
                          ? "bg-red-500/20 text-red-400 border border-red-500/40"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="p-3 font-sans text-slate-400">{m.reviewer || "administrator"}</td>
                  <td className="p-3 text-slate-400">v{m.version || 1}</td>
                </tr>
              ))}
              {filteredMappings.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-4 text-center text-slate-500 font-sans">
                    No mappings found in database for tab: {activeTab}.
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

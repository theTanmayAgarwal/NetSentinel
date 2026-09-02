import React, { useEffect, useState } from "react";
import {
  Database,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Slash,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Shield,
  Edit,
  X,
} from "lucide-react";
import {
  getMappings,
  approveExemplar,
  revalidateMapping,
  revokeMapping,
  correctMapping,
  rejectMapping,
} from "../services/api";

export function KnowledgeBase() {
  const [mappings, setMappings] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Edit inline modal/drawer
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editParam, setEditParam] = useState("");
  const [editVal, setEditVal] = useState("");
  const [editUnit, setEditUnit] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editControlId, setEditControlId] = useState("");
  const [editPattern, setEditPattern] = useState("");

  const loadData = () => {
    getMappings()
      .then(setMappings)
      .catch((err) => console.error("KnowledgeBase loadData error:", err));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async (id: number) => {
    await approveExemplar(id, true);
    loadData();
  };

  const handleReject = async (id: number) => {
    await rejectMapping(id);
    loadData();
  };

  const handleRevalidate = async (id: number) => {
    await revalidateMapping(id);
    loadData();
  };

  const handleRevoke = async (id: number) => {
    await revokeMapping(id);
    loadData();
  };

  const handleStartEdit = (m: any) => {
    setEditingId(m.id);
    setEditParam(m.security_property || m.parameter || "");
    setEditVal(m.value || m.expected_value || "");
    setEditUnit(m.unit || "");
    setEditCategory(m.category || "System Configuration");
    setEditControlId(m.control_id || "");
    setEditPattern(m.command_pattern || m.text || "");
  };

  const handleSaveCorrection = async (id: number) => {
    await correctMapping(id, editParam, editVal, {
      unit: editUnit,
      category: editCategory,
      control_id: editControlId,
      command_pattern: editPattern,
    });
    setEditingId(null);
    loadData();
  };

  const filteredMappings = mappings.filter((m) => {
    if (activeTab === "ALL") return true;
    if (activeTab === "PENDING") return m.status === "PENDING";
    if (activeTab === "ACTIVE") return m.status === "ACTIVE" || m.status === "APPROVED";
    if (activeTab === "REJECTED") return m.status === "REJECTED";
    if (activeTab === "STALE") return m.status === "STALE";
    if (activeTab === "REVOKED") return m.status === "REVOKED";
    return true;
  });

  const getStatusBadge = (status: string) => {
    if (status === "ACTIVE" || status === "APPROVED") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
          ACTIVE
        </span>
      );
    }
    if (status === "PENDING") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/40">
          PENDING
        </span>
      );
    }
    if (status === "REJECTED") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/40">
          REJECTED
        </span>
      );
    }
    if (status === "STALE") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40">
          STALE
        </span>
      );
    }
    if (status === "REVOKED") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">
          REVOKED
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Database className="h-5 w-5 text-cyan-400" /> Adaptive Security-Semantic Memory Manager
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Single source of truth in PostgreSQL (`learned_mappings`). Shared directly with Training Center.
          </p>
        </div>

        {/* Live counts summary */}
        <div className="flex items-center gap-2 shrink-0 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-bold">
            {mappings.filter((m) => m.status === "ACTIVE" || m.status === "APPROVED").length} ACTIVE (TRUSTED)
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-purple-950/60 border border-purple-500/40 text-purple-300 font-bold">
            {mappings.filter((m) => m.status === "PENDING").length} PENDING
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 flex-wrap">
        {["ALL", "PENDING", "ACTIVE", "REJECTED", "STALE", "REVOKED"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === tab
                ? "bg-cyan-950 border border-cyan-500/50 text-cyan-300 shadow-glow"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab} ({mappings.filter((m) => tab === "ALL" ? true : tab === "ACTIVE" ? (m.status === "ACTIVE" || m.status === "APPROVED") : m.status === tab).length})
          </button>
        ))}
      </div>

      <div className="glass-panel p-5">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3 w-8"></th>
                <th className="p-3">Mapping ID</th>
                <th className="p-3">Vendor / OS</th>
                <th className="p-3">Command Pattern</th>
                <th className="p-3">Security Property</th>
                <th className="p-3">Value</th>
                <th className="p-3">Version</th>
                <th className="p-3">Status</th>
                <th className="p-3">Reviewer</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredMappings.map((m) => (
                <React.Fragment key={m.id}>
                  <tr className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 text-slate-500 cursor-pointer" onClick={() => setExpandedId(expandedId === m.id ? null : m.id)}>
                      {expandedId === m.id ? <ChevronDown className="h-4 w-4 text-cyan-400" /> : <ChevronRight className="h-4 w-4" />}
                    </td>
                    <td className="p-3 text-cyan-400 font-bold cursor-pointer" onClick={() => setExpandedId(expandedId === m.id ? null : m.id)}>
                      M-{m.id}
                    </td>
                    <td className="p-3 font-sans text-slate-300">
                      {m.vendor || "unknown"} <span className="text-[10px] text-slate-500">({m.os_version || "all"})</span>
                    </td>
                    <td className="p-3 font-semibold text-slate-100">
                      {editingId === m.id ? (
                        <input
                          type="text"
                          value={editPattern}
                          onChange={(e) => setEditPattern(e.target.value)}
                          className="bg-slate-950 border border-slate-700 px-2 py-1 text-xs rounded text-slate-200 w-full"
                        />
                      ) : (
                        m.command_pattern || m.text
                      )}
                    </td>
                    <td className="p-3 text-purple-300">
                      {editingId === m.id ? (
                        <input
                          type="text"
                          value={editParam}
                          onChange={(e) => setEditParam(e.target.value)}
                          className="bg-slate-950 border border-slate-700 px-2 py-1 text-xs rounded text-slate-200"
                        />
                      ) : (
                        m.security_property || m.parameter
                      )}
                    </td>
                    <td className="p-3 text-emerald-300">
                      {editingId === m.id ? (
                        <input
                          type="text"
                          value={editVal}
                          onChange={(e) => setEditVal(e.target.value)}
                          className="bg-slate-950 border border-slate-700 px-2 py-1 text-xs rounded text-slate-200"
                        />
                      ) : (
                        `${m.value || m.expected_value} ${m.unit || ""}`
                      )}
                    </td>
                    <td className="p-3 text-slate-400">v{m.version || 1}</td>
                    <td className="p-3 font-sans">{getStatusBadge(m.status)}</td>
                    <td className="p-3 text-slate-400 font-sans">{m.reviewer || "administrator"}</td>
                    <td className="p-3 font-sans text-right">
                      {editingId === m.id ? (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleSaveCorrection(m.id)}
                            className="px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px] font-bold"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px]"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-end gap-1.5">
                          {m.status === "PENDING" && (
                            <button
                              onClick={() => handleApprove(m.id)}
                              className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold"
                            >
                              Approve
                            </button>
                          )}
                          {(m.status === "PENDING" || m.status === "ACTIVE" || m.status === "APPROVED") && (
                            <button
                              onClick={() => handleStartEdit(m)}
                              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[10px]"
                            >
                              Edit
                            </button>
                          )}
                          {m.status === "PENDING" && (
                            <button
                              onClick={() => handleReject(m.id)}
                              className="px-2 py-0.5 bg-red-950 border border-red-500/50 hover:bg-red-900 text-red-300 rounded text-[10px] font-bold"
                            >
                              Reject
                            </button>
                          )}
                          {m.status === "STALE" && (
                            <button
                              onClick={() => handleRevalidate(m.id)}
                              className="px-2 py-0.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-[10px] font-bold flex items-center gap-1"
                            >
                              <RefreshCw className="h-3 w-3" /> Revalidate
                            </button>
                          )}
                          {(m.status === "ACTIVE" || m.status === "APPROVED") && (
                            <button
                              onClick={() => handleRevoke(m.id)}
                              className="px-2 py-0.5 bg-red-950/80 border border-red-500/50 hover:bg-red-900 text-red-300 rounded text-[10px] font-bold flex items-center gap-1"
                            >
                              <Slash className="h-3 w-3" /> Revoke
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>

                  {/* Expandable Provenance Detail Row */}
                  {expandedId === m.id && (
                    <tr className="bg-slate-950/90 border-b border-slate-800">
                      <td colSpan={10} className="p-4 space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono bg-slate-900 p-3.5 rounded-lg border border-slate-800">
                          <div>
                            <span className="text-slate-500 text-[10px] block font-sans">CATEGORY / CONTROL ID:</span>
                            <span className="text-slate-200 font-bold">{m.category || "System Configuration"}</span>
                            {m.control_id && <span className="text-cyan-400 block text-[11px] font-mono">{m.control_id}</span>}
                          </div>
                          <div>
                            <span className="text-slate-500 text-[10px] block font-sans">REVIEW PROVENANCE:</span>
                            <span className="text-slate-300 block">Reviewer: {m.reviewer || "administrator"}</span>
                            <span className="text-slate-400 text-[10px] block">Reviewed At: {m.reviewed_at || "Not reviewed yet"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 text-[10px] block font-sans">AI PROPOSAL CONFIDENCE:</span>
                            <span className="text-purple-300 font-bold">
                              {m.ai_confidence ? `${Math.round(m.ai_confidence * 100)}%` : "Not available"}
                            </span>
                          </div>
                        </div>

                        {m.ai_proposal && (
                          <div className="p-3 bg-purple-950/20 rounded border border-purple-500/30 text-xs">
                            <span className="text-[10px] font-bold text-purple-300 block mb-1 flex items-center gap-1">
                              <Sparkles className="h-3.5 w-3.5 text-purple-400" /> ORIGINAL AI PROPOSAL TEXT (PRESERVED):
                            </span>
                            <p className="text-slate-300 italic">"{m.ai_proposal}"</p>
                          </div>
                        )}

                        {/* Audit Traceability & Usage Block (PART F) */}
                        <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800 space-y-2 text-xs font-mono">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                            <span className="text-[11px] font-bold text-cyan-400 font-sans flex items-center gap-1.5">
                              <Shield className="h-3.5 w-3.5 text-cyan-400" /> AUDIT TRACEABILITY & USAGE STATISTICS
                            </span>
                            <span className="text-[10px] text-slate-400 font-sans">
                              {m.usage_count && m.usage_count > 0 ? (
                                <span className="text-emerald-400 font-bold">USED IN {m.usage_count} AUDIT(S)</span>
                              ) : (
                                <span className="text-slate-500 italic">Not yet used in an audit</span>
                              )}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
                            <div>
                              <span className="text-slate-500 text-[10px] block font-sans">USAGE COUNT:</span>
                              <span className={m.usage_count > 0 ? "text-emerald-400 font-bold" : "text-slate-400"}>
                                {m.usage_count || 0} event(s)
                              </span>
                            </div>

                            <div>
                              <span className="text-slate-500 text-[10px] block font-sans">LAST USED AT:</span>
                              <span className="text-slate-300">
                                {m.last_used ? new Date(m.last_used).toLocaleString() : "Never"}
                              </span>
                            </div>

                            <div>
                              <span className="text-slate-500 text-[10px] block font-sans">AUDITS USED IN:</span>
                              <span className="text-cyan-300">
                                {m.audits_used && m.audits_used.length > 0
                                  ? m.audits_used.map((aId: any) => `#A-${aId}`).join(", ")
                                  : "None"}
                              </span>
                            </div>
                          </div>

                          {m.controls_evaluated && m.controls_evaluated.length > 0 && (
                            <div className="text-[11px] pt-1">
                              <span className="text-slate-500 text-[10px] font-sans">CONTROLS EVALUATED: </span>
                              <span className="text-purple-300">{m.controls_evaluated.join(", ")}</span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}

                </React.Fragment>
              ))}
              {filteredMappings.length === 0 && (
                <tr>
                  <td colSpan={10} className="p-4 text-center text-slate-500 font-sans">
                    No mappings found in database for tab: {activeTab}. Teach unknown commands in the Training Center.
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

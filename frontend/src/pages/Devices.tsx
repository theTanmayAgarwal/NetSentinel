import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Server, ShieldCheck, ArrowRight } from "lucide-react";
import { getDevices } from "../services/api";

export function Devices() {
  const [devices, setDevices] = useState<any[]>([]);

  useEffect(() => {
    getDevices().then(setDevices).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Network Device Inventory</h1>
        <p className="text-xs text-slate-400">
          Audited network switches, routers, and firewalls across Cisco, Juniper, and Fortinet
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {devices.map((dev) => (
          <div key={dev.id} className="glass-panel p-5 space-y-3 glass-panel-hover">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  <Server className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">{dev.hostname || "router-01"}</h3>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">{dev.vendor}</span>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                Score: {dev.highest_score || 85}%
              </span>
            </div>

            <div className="text-xs text-slate-400 border-t border-slate-800 pt-3 space-y-1">
              <p>Total Audits: <strong className="text-slate-200">{dev.audit_count || 1}</strong></p>
              <p>Last Audited: <span className="text-slate-300 font-mono">{dev.last_audited_at?.slice(0, 10) || "Today"}</span></p>
            </div>

            <Link
              to={`/devices/${dev.id}`}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-all"
            >
              View Device Audit Details <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        ))}

        {devices.length === 0 && (
          <div className="glass-panel p-8 col-span-3 text-center text-slate-400 text-xs">
            No devices recorded yet. Run a configuration audit from the Audits page to register a device.
          </div>
        )}
      </div>
    </div>
  );
}

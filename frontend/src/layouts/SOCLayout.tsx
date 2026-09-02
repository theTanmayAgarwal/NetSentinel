import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  ShieldCheck,
  LayoutDashboard,
  FileCheck2,
  Server,
  AlertTriangle,
  GraduationCap,
  Database,
  FileSpreadsheet,
  Settings,
  Activity,
  Cpu,
} from "lucide-react";
import { getHealth, type HealthResponse } from "../services/api";

interface SOCLayoutProps {
  children: React.ReactNode;
}

export function SOCLayout({ children }: SOCLayoutProps) {
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const navItems = [
    { path: "/", label: "Dashboard", icon: LayoutDashboard },
    { path: "/audits", label: "Audits & Upload", icon: FileCheck2 },
    { path: "/devices", label: "Devices", icon: Server },
    { path: "/findings", label: "Findings", icon: AlertTriangle },
    {
      path: "/training",
      label: "Training Center",
      icon: GraduationCap,
      badge: "HERO FEATURE",
      highlight: true,
    },
    { path: "/knowledge-base", label: "Knowledge Base", icon: Database },
    { path: "/reports", label: "Reports", icon: FileSpreadsheet },
  ];

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/90 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo Header */}
          <div className="p-5 border-b border-slate-800 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-100 tracking-wide">
                NETAUDIT <span className="text-cyan-400">AI</span>
              </h1>
              <p className="text-[10px] text-slate-400 tracking-tight">
                SIH26155 Compliance Auditor
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? item.highlight
                        ? "bg-gradient-to-r from-purple-900/60 to-cyan-900/60 border border-purple-500/40 text-purple-200 shadow-glow"
                        : "bg-cyan-950/60 border border-cyan-500/30 text-cyan-300"
                      : item.highlight
                      ? "text-purple-300 hover:bg-purple-950/30 border border-purple-900/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-4 w-4 ${isActive ? (item.highlight ? "text-purple-400" : "text-cyan-400") : "text-slate-500"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-slate-400 font-mono text-[11px]">Backend API</span>
            </div>
            {health ? (
              <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-semibold">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                ONLINE
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                CHECKING
              </span>
            )}
          </div>
          <p className="mt-2 text-[10px] text-slate-500">
            Engine: Deterministic CIS + Few-Shot Embedding Learning
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-950">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-slate-800 bg-slate-900/60 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
              Target Framework: <strong className="text-cyan-400">CIS Controls v1.0</strong>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-xs text-slate-400">
              Vendors: <strong className="text-slate-200">Cisco, Juniper, Fortinet</strong>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              <span>Embedding Engine: <strong className="text-slate-200">MiniLM / Hashing Vectorizer</strong></span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}

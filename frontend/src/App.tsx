import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "./services/api";
import { ShieldCheck, ServerCog, AlertTriangle } from "lucide-react";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e) => setError(e?.message ?? "unreachable"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center gap-3 border-b border-slate-800 px-6 py-4">
        <ShieldCheck className="h-6 w-6 text-brand-400" />
        <div>
          <h1 className="text-lg font-semibold leading-tight">
            Multi-Vendor Network Security Compliance Auditor
          </h1>
          <p className="text-xs text-slate-400">
            Understand once. Normalize once. Audit every vendor.
          </p>
        </div>
      </header>

      <main className="p-6">
        <div className="max-w-md rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <ServerCog className="h-4 w-4" /> Backend connectivity
          </div>

          {health && (
            <div className="mt-3 space-y-1 text-sm">
              <p className="font-medium text-brand-400">● {health.status.toUpperCase()}</p>
              <p className="text-slate-400">
                v{health.version} · {health.env}
              </p>
            </div>
          )}

          {error && (
            <div className="mt-3 flex items-start gap-2 text-sm text-amber-400">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                Backend unreachable ({error}). Start it with{" "}
                <code className="rounded bg-slate-800 px-1">make backend</code>.
              </span>
            </div>
          )}

          {!health && !error && <p className="mt-3 text-sm text-slate-500">Checking…</p>}
        </div>

        <p className="mt-6 max-w-md text-xs leading-relaxed text-slate-500">
          Scaffold placeholder. The SOC-style dashboard, findings views, and the
          interactive Training Center are built in later milestones.
        </p>
      </main>
    </div>
  );
}

# Architecture

**Tagline:** *Understand once. Normalize once. Audit every vendor.*

## Pipeline

```
Upload config (untrusted text)
      ↓
Vendor detection            (deterministic signatures — no LLM)
      ↓
Vendor parser               (Cisco / Juniper / Fortinet — regex, no LLM)
      ↓
Vendor-neutral normalization  → common security model (typed facts)
      ↓
Deterministic compliance engine  (JSON/YAML CIS-style rules)  → PASS/FAIL/WARNING/CRITICAL
      ↓
Risk analysis + templated explanation   (deterministic templates; AI never sets Pass/Fail)
      ↓
Device-specific remediation   ((vendor, control) templates → syntax-validated)
      ↓
Predicted before/after compliance   (re-run engine on the remediated model)
      ↓
Human approval gate   (never auto-applied to any device)
      ↓
Report   (PDF / CSV / JSON)
```

## The differentiator — interactive semantic learning loop

```
Unknown command detected
      ↓
Embed the line (sentence-transformers, or offline fallback embedder)
      ↓
Nearest-neighbour search over learned exemplars (cosine similarity)
      ↓
Confidence ≥ threshold?  ── yes ──▶  auto-classify to control/parameter
      │ no
      ▼
Interactive Training UI (structured dropdowns: Category / Parameter / Expected / Control)
      ↓
Store a new versioned exemplar (created_by, created_at, version, status)
      ↓
Immediately available for classification — no retrain, no code change, no redeploy
```

Generalization is measured, not assumed, via the **Teaching Generalization Rate (TGR)**:
after teaching from a set of exemplars, what fraction of *held-out, previously unseen*
command variants does the system classify correctly?

## Design principles

- **Deterministic core.** Vendor detection, parsing, and Pass/Fail are rule-based and
  reproducible. AI assists only with explanation and unknown-command classification.
- **Untrusted input.** Configuration text is treated as data, never as instructions
  (prompt-injection safe): deterministic extraction → typed fields → optional AI over
  typed fields only.
- **Human in the loop.** Remediation is generated and validated but never auto-applied;
  an administrator approves every change and every learned mapping.
- **Testable everywhere.** The core engine depends only on the standard library + numpy,
  so it runs and is verified offline. FastAPI and React are thin layers on top.

## Layering

| Layer            | Tech                              | Notes                                             |
|------------------|-----------------------------------|---------------------------------------------------|
| Core engine      | Python stdlib + numpy             | parsers, normalization, compliance, remediation, embeddings, TGR — no web/DB deps |
| Persistence      | SQLite                            | DB-agnostic repository interface                  |
| API              | FastAPI + Uvicorn                 | thin routers over the core services               |
| Learning         | sentence-transformers (optional) + numpy vector store | offline fallback embedder when the model is absent |
| Reporting        | ReportLab (PDF), CSV, JSON        | —                                                 |
| Frontend         | Vite + React + TS + Tailwind + Recharts | SOC-style dashboard, findings, Training Center |

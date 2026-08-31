# AI-Driven Multi-Vendor Network Security Compliance Auditor

> **Understand once. Normalize once. Audit every vendor.**

An AI-augmented, **vendor-agnostic** platform that ingests network-device configurations
(Cisco, Juniper, Fortinet), understands each vendor's syntax, converts it into a common
security model, evaluates it against CIS-style compliance controls with a **deterministic**
engine, and produces explainable, device-specific remediation — all under human oversight.

Its differentiator is an **interactive semantic learning loop**: when the auditor meets a
configuration command it has never seen, it embeds the line, finds the nearest learned
examples by similarity, and either auto-classifies it (high confidence) or asks an
administrator to map it once. That mapping is stored as a versioned example and is
**immediately** usable for future audits — no model retraining, no code change, no redeploy.
Generalization is *measured*, not assumed, via the **Teaching Generalization Rate (TGR)**.

---

## What the AI does — and does not do

- **Deterministic, always:** vendor detection, parsing, and every Pass/Fail/Warning/Critical
  decision. These are rule-based and reproducible. **AI never decides compliance.**
- **AI-assisted:** natural-language explanation of findings, and classification of *unknown*
  commands via embeddings + similarity search.
- **Never automated:** remediation is generated, syntax-validated, and shown with a predicted
  before/after compliance delta — but an administrator must approve it. Nothing is ever pushed
  to a real device.
- **Untrusted input:** configuration text is treated as data, never as instructions.

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline.

---

## Repository layout

```
backend/
  app/
    api/            FastAPI routers (added per milestone)
    core/           config, health, shared utilities (dependency-free)
    models/         persistence entities
    schemas/        API request/response models
    parsers/        cisco/ juniper/ fortinet/ (deterministic, regex-based)
    normalization/  vendor syntax -> common security model
    compliance/     deterministic rule engine  (rules/ = JSON/YAML controls)
    embeddings/     embedder + vector store (offline fallback + optional MiniLM)
    training/       unknown-command learning loop, exemplars, TGR
    remediation/    (vendor, control) templates + validation + before/after
    reporting/      ReportLab PDF, CSV, JSON
    services/       pipeline orchestration
  tests/            runnable with stdlib unittest OR pytest
  requirements.txt        base runtime (lightweight)
  requirements-ml.txt     optional: sentence-transformers / faiss
frontend/           Vite + React + TypeScript + Tailwind + Recharts
sample_configs/     sanitized demo configs (cisco/ juniper/ fortinet/ unknown/)
data/               app.db (SQLite), reports/, audit_logs/, exemplars/
docs/               architecture, API, demo script
```

---

## Quick start (macOS / Linux)

**Prerequisites:** Python 3.10+ and Node 18+.

```bash
# 1. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
#   API docs:   http://localhost:8000/docs
#   Health:     http://localhost:8000/api/health

# 2. Frontend (in a second terminal)
cd frontend
npm install
npm run dev
#   App:        http://localhost:5173
```

Or use the shortcuts: `make setup`, then `make backend` and `make frontend`.

### Optional: full semantic AI

The learning loop works out of the box with a built-in offline embedder. For the richest
generalization, install the optional model stack (first run downloads ~90 MB once):

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-ml.txt        # sentence-transformers (all-MiniLM-L6-v2)
```

---

## Testing

```bash
# No third-party dependencies required (standard library only):
make test-core        # cd backend && python3 -m unittest discover -s tests -v

# Full suite on an installed environment:
make test             # cd backend && pytest -q
```

The core engine depends only on the standard library + numpy, so it is verified offline;
FastAPI and the React app are thin layers that run on your machine.

---

## Status

Prototype under active development for the SIH internal evaluation. Built milestone by
milestone with real, non-fabricated verification. This is a **demo** system: it does not
connect to, or modify, any production device.

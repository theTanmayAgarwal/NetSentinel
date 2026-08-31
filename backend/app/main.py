"""FastAPI application entrypoint.

A thin HTTP layer over the framework-agnostic core services (parsers,
normalization, compliance engine, remediation, learning loop) which live under
app/ and are independently unit-tested. Feature routers are mounted here as the
build progresses.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.health import health_payload

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Vendor-agnostic network configuration security compliance auditor. "
        "A deterministic compliance engine paired with a human-in-the-loop "
        "semantic learning loop for previously unseen configuration commands. "
        "AI assists with explanation and classification; it never decides "
        "Pass/Fail and never applies changes."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
def root() -> dict:
    return {"name": settings.app_name, "version": settings.version, "docs": "/docs"}


@app.get("/api/health", tags=["system"])
def health() -> dict:
    """Liveness probe the frontend uses to confirm end-to-end connectivity."""
    return health_payload()


# Feature routers (upload, audits, devices, findings, training, reports)
# are included in later milestones, e.g.:
#   from app.api import audits
#   app.include_router(audits.router, prefix="/api")

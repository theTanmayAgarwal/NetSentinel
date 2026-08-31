"""Framework-agnostic health payload.

Kept separate from the FastAPI route so it can be unit-tested without a running
web server (the route in app.main is a thin wrapper around this function).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings


def health_payload() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "env": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

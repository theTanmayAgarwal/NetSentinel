"""FastAPI router for querying and filtering security findings."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_repo
from app.persistence.repository import Repository

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=List[Dict[str, Any]])
def list_findings(
    vendor: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    repo: Repository = Depends(get_repo),
) -> List[Dict[str, Any]]:
    """List compliance findings across all audits with optional filtering."""
    query = """
        SELECT f.*, a.vendor, a.hostname, a.filename, a.created_at as audit_date
        FROM findings f
        JOIN audits a ON a.id = f.audit_id
        WHERE 1=1
    """
    params = []

    if vendor:
        query += " AND LOWER(a.vendor) = LOWER(?)"
        params.append(vendor)
    if severity:
        query += " AND LOWER(f.severity) = LOWER(?)"
        params.append(severity)
    if status:
        query += " AND LOWER(f.status) = LOWER(?)"
        params.append(status)

    query += " ORDER BY f.id DESC LIMIT ?"
    params.append(limit)

    cur = repo._execute(query, tuple(params))
    rows = cur.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["evidence"] = json.loads(d.pop("evidence_json") or "[]")
        d["remediation"] = json.loads(d.pop("remediation_json") or "null")
        results.append(d)

    return results

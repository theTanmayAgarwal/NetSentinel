"""FastAPI router for device inventory and device detail views."""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_repo
from app.persistence.repository import Repository

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=List[Dict[str, Any]])
def list_devices(repo: Repository = Depends(get_repo)) -> List[Dict[str, Any]]:
    """List unique audited network devices."""
    cur = repo._execute(
        """SELECT d.id, d.hostname, d.vendor, d.created_at,
                  COUNT(a.id) as audit_count,
                  MAX(a.score) as highest_score,
                  MIN(a.score) as lowest_score,
                  MAX(a.created_at) as last_audited_at
           FROM devices d
           LEFT JOIN audits a ON a.device_id = d.id
           GROUP BY d.id, d.hostname, d.vendor, d.created_at ORDER BY d.id DESC"""
    )
    return [dict(r) for r in cur.fetchall()]


@router.get("/{device_id}", response_model=Dict[str, Any])
def get_device_detail(device_id: int, repo: Repository = Depends(get_repo)) -> Dict[str, Any]:
    """Retrieve detailed information and audit history for a specific device."""
    cur = repo._execute(
        "SELECT * FROM devices WHERE id = ?", (device_id,)
    )
    dev_row = cur.fetchone()
    if not dev_row:
        raise HTTPException(status_code=404, detail=f"Device #{device_id} not found.")

    device = dict(dev_row)
    audits_cur = repo._execute(
        "SELECT id, filename, vendor, hostname, score, passed, failed, warnings, critical, created_at "
        "FROM audits WHERE device_id = ? ORDER BY id DESC",
        (device_id,),
    )
    audits = [dict(a) for a in audits_cur.fetchall()]


    latest_audit = repo.get_audit(audits[0]["id"]) if audits else None

    return {
        "device": device,
        "audits": audits,
        "latest_audit": latest_audit,
    }

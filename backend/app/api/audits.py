"""FastAPI router for configuration upload and security audit execution."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.deps import get_repo
from app.persistence.repository import Repository
from app.services.audit_service import run_audit

router = APIRouter(prefix="/audits", tags=["audits"])


class UploadTextRequest(BaseModel):
    filename: str = "config.cfg"
    config_text: str
    actor: str = "administrator"


@router.post("/upload", response_model=Dict[str, Any])
async def upload_and_audit(
    file: Optional[UploadFile] = File(None),
    config_text: Optional[str] = Form(None),
    filename: Optional[str] = Form("config.cfg"),
    actor: Optional[str] = Form("administrator"),
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Upload a network configuration (via file or raw text) and execute compliance audit."""
    text_content = ""
    target_filename = filename or "config.cfg"

    if file is not None:
        target_filename = file.filename or target_filename
        raw_bytes = await file.read()
        text_content = raw_bytes.decode("utf-8", errors="replace")
    elif config_text:
        text_content = config_text
    else:
        raise HTTPException(status_code=400, detail="Either file upload or config_text is required.")

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Configuration content cannot be empty.")

    report = run_audit(
        filename=target_filename,
        config_text=text_content,
        actor=actor or "administrator",
        repo=repo,
    )
    return report


@router.post("/text", response_model=Dict[str, Any])
def audit_config_text(
    payload: UploadTextRequest,
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Audit JSON payload containing configuration text."""
    if not payload.config_text.strip():
        raise HTTPException(status_code=400, detail="config_text cannot be empty.")

    return run_audit(
        filename=payload.filename,
        config_text=payload.config_text,
        actor=payload.actor,
        repo=repo,
    )


@router.get("", response_model=List[Dict[str, Any]])
def list_audits(repo: Repository = Depends(get_repo)) -> List[Dict[str, Any]]:
    """List historical audit runs."""
    return repo.list_audits()


@router.get("/{audit_id}", response_model=Dict[str, Any])
def get_audit(audit_id: int, repo: Repository = Depends(get_repo)) -> Dict[str, Any]:
    """Retrieve full audit details including findings, evidence, and predictions."""
    audit = repo.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit #{audit_id} not found.")
    return audit

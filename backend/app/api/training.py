"""FastAPI router for Interactive Semantic Learning, Exemplars, and TGR."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_training_service
from app.training.service import TrainingService
from app.training.tgr import evaluate_tgr

router = APIRouter(prefix="/training", tags=["training"])


class ClassifyRequest(BaseModel):
    line: str = Field(..., example="set xyz secure-admin-timeout 300")
    vendor: Optional[str] = Field(None, example="juniper")


class TeachExemplarRequest(BaseModel):
    raw_text: str = Field(..., example="set xyz secure-admin-timeout 300")
    category: str = Field(..., example="authentication")
    parameter: str = Field(..., example="admin_session_timeout")
    expected_value: str = Field(..., example="300")
    control_id: Optional[str] = Field(None, example="CIS-NET-18")
    vendor: Optional[str] = Field(None, example="unknown")
    actor: str = Field("administrator", example="administrator")


class ApproveExemplarRequest(BaseModel):
    approved: bool = True
    actor: str = Field("administrator", example="administrator")


class AIProposeRequest(BaseModel):
    line: str = Field(..., example="set secure-admin-timeout 300")
    context: Optional[str] = Field(None, example="management configuration")
    vendor: Optional[str] = Field(None, example="unknown")
    platform: Optional[str] = Field(None, example="Unknown")
    os_version: Optional[str] = Field(None, example="1.0")


class CorrectMappingRequest(BaseModel):
    parameter: Optional[str] = None
    expected_value: Optional[str] = None
    category: Optional[str] = None
    actor: str = Field("administrator", example="administrator")


class ActionRequest(BaseModel):
    actor: str = Field("administrator", example="administrator")


@router.post("/classify", response_model=Dict[str, Any])
def classify_unknown_line(
    payload: ClassifyRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Classify an unknown configuration line using vector similarity against exemplars."""
    if not payload.line.strip():
        raise HTTPException(status_code=400, detail="Line cannot be empty.")
    return ts.classify_unknown_line(payload.line, vendor=payload.vendor)


@router.post("/ai-propose", response_model=Dict[str, Any])
def ai_propose_mapping(
    payload: AIProposeRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Generate a structured AI interpretation proposal for an unknown command fragment."""
    if not payload.line.strip():
        raise HTTPException(status_code=400, detail="Line cannot be empty.")
    return ts.ai_propose(
        line=payload.line,
        context=payload.context,
        vendor=payload.vendor,
        platform=payload.platform,
        os_version=payload.os_version,
    )


@router.post("/exemplars", response_model=Dict[str, Any])
@router.post("/mappings", response_model=Dict[str, Any])
def teach_exemplar(
    payload: TeachExemplarRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Save an administrator-approved exemplar mapping for future classification."""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text cannot be empty.")
    
    return ts.teach_exemplar(
        raw_text=payload.raw_text,
        category=payload.category,
        parameter=payload.parameter,
        expected_value=payload.expected_value,
        control_id=payload.control_id,
        vendor=payload.vendor,
        actor=payload.actor,
    )


@router.get("/exemplars", response_model=List[Dict[str, Any]])
@router.get("/mappings", response_model=List[Dict[str, Any]])
def list_exemplars(
    status: Optional[str] = None,
    ts: TrainingService = Depends(get_training_service),
) -> List[Dict[str, Any]]:
    """List learned exemplars / mappings in the knowledge base."""
    return ts.list_exemplars(status=status)


@router.post("/exemplars/{exemplar_id}/approve", response_model=Dict[str, Any])
@router.post("/mappings/{exemplar_id}/approve", response_model=Dict[str, Any])
def approve_exemplar(
    exemplar_id: int,
    payload: ApproveExemplarRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Approve or reject a learned exemplar mapping."""
    ts.approve_exemplar(exemplar_id, approved=payload.approved, actor=payload.actor)
    return {
        "exemplar_id": exemplar_id,
        "status": "ACTIVE" if payload.approved else "REJECTED",
        "approved": payload.approved,
    }


@router.post("/mappings/{exemplar_id}/correct", response_model=Dict[str, Any])
def correct_mapping(
    exemplar_id: int,
    payload: CorrectMappingRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Correct an existing mapping's security parameter or value."""
    updates = {}
    if payload.parameter:
        updates["parameter"] = payload.parameter
        updates["security_property"] = payload.parameter
    if payload.expected_value:
        updates["expected_value"] = payload.expected_value
        updates["value"] = payload.expected_value
    if payload.category:
        updates["category"] = payload.category

    ts.correct_mapping(exemplar_id, updates, actor=payload.actor)
    return {"exemplar_id": exemplar_id, "status": "ACTIVE", "updates": updates}


@router.post("/mappings/{exemplar_id}/revalidate", response_model=Dict[str, Any])
def revalidate_mapping(
    exemplar_id: int,
    payload: ActionRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Revalidate a stale mapping to ACTIVE state and bump version."""
    ts.revalidate_mapping(exemplar_id, actor=payload.actor)
    return {"exemplar_id": exemplar_id, "status": "ACTIVE", "revalidated": True}


@router.post("/mappings/{exemplar_id}/revoke", response_model=Dict[str, Any])
def revoke_mapping(
    exemplar_id: int,
    payload: ActionRequest,
    ts: TrainingService = Depends(get_training_service),
) -> Dict[str, Any]:
    """Revoke an active or stale mapping so it is no longer auto-applied."""
    ts.revoke_mapping(exemplar_id, actor=payload.actor)
    return {"exemplar_id": exemplar_id, "status": "REVOKED", "revoked": True}


@router.get("/tgr", response_model=Dict[str, Any])
def get_tgr(ts: TrainingService = Depends(get_training_service)) -> Dict[str, Any]:
    """Calculate and return the Teaching Generalization Rate (TGR) score on held-out evaluation dataset."""
    return evaluate_tgr(ts)


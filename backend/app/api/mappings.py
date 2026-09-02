"""FastAPI router for Learned Mappings management (PART A)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_repo
from app.persistence.repository import Repository

router = APIRouter(prefix="/mappings", tags=["mappings"])

VALID_STATUSES = {"PENDING", "ACTIVE", "STALE", "REVOKED", "REJECTED"}


class MappingCreateRequest(BaseModel):
    vendor: Optional[str] = Field("unknown", example="juniper")
    os_version: Optional[str] = Field("all", example="21.4")
    command_pattern: str = Field(..., example="set xyz secure-admin-timeout <value>")
    security_property: str = Field(..., example="admin_session_timeout")
    value: Optional[str] = Field(None, example="300")
    unit: Optional[str] = Field(None, example="seconds")
    category: Optional[str] = Field("Secure Management", example="Secure Management")
    control_id: Optional[str] = Field(None, example="CIS-NET-18")
    ai_confidence: Optional[float] = Field(1.0, example=0.95)
    ai_proposal: Optional[str] = Field(None, example="Administrative session timeout setting")
    status: Optional[str] = Field("PENDING", example="ACTIVE")
    version: Optional[int] = Field(1, example=1)
    reviewer: Optional[str] = Field("administrator", example="administrator")


class MappingUpdateRequest(BaseModel):
    vendor: Optional[str] = None
    os_version: Optional[str] = None
    command_pattern: Optional[str] = None
    security_property: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    control_id: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_proposal: Optional[str] = None
    status: Optional[str] = None
    version: Optional[int] = None
    reviewer: Optional[str] = "administrator"


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_mappings(
    status_filter: Optional[str] = Query(None, alias="status"),
    vendor: Optional[str] = Query(None),
    repo: Repository = Depends(get_repo),
) -> List[Dict[str, Any]]:
    """List learned mappings from the persistent database."""
    if status_filter and status_filter.upper() not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status_filter}'. Must be one of {sorted(VALID_STATUSES)}",
        )
    return repo.list_mappings(status=status_filter, vendor=vendor)


@router.get("/{mapping_id}", response_model=Dict[str, Any])
def get_mapping_by_id(
    mapping_id: int,
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Retrieve a single learned mapping by ID."""
    mapping = repo.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=404,
            detail=f"Mapping M-{mapping_id} not found.",
        )
    return mapping


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)

def create_mapping(
    payload: MappingCreateRequest,
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Create a new persistent learned mapping."""
    if not payload.command_pattern.strip():
        raise HTTPException(status_code=400, detail="command_pattern cannot be empty.")
    if not payload.security_property.strip():
        raise HTTPException(status_code=400, detail="security_property cannot be empty.")

    stat = (payload.status or "PENDING").upper()
    if stat not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{stat}'. Must be one of {sorted(VALID_STATUSES)}",
        )

    mapping_data = {
        "vendor": payload.vendor or "unknown",
        "os_version": payload.os_version or "all",
        "command_pattern": payload.command_pattern.strip(),
        "security_property": payload.security_property.strip(),
        "value": payload.value,
        "unit": payload.unit,
        "category": payload.category or "System Configuration",
        "control_id": payload.control_id,
        "ai_confidence": payload.ai_confidence if payload.ai_confidence is not None else 1.0,
        "ai_proposal": payload.ai_proposal,
        "status": stat,
        "version": payload.version or 1,
        "reviewer": payload.reviewer or "administrator",
    }

    try:
        created = repo.create_mapping(mapping_data)
        return created
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Database error creating mapping: {str(err)}")


@router.patch("/{mapping_id}", response_model=Dict[str, Any])
def update_mapping(
    mapping_id: int,
    payload: MappingUpdateRequest,
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Update fields or status of an existing learned mapping."""
    existing = repo.get_mapping(mapping_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Mapping M-{mapping_id} not found.")

    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        return existing

    if "status" in updates and updates["status"]:
        stat = updates["status"].upper()
        if stat not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{stat}'. Must be one of {sorted(VALID_STATUSES)}",
            )
        updates["status"] = stat

    try:
        updated = repo.update_mapping(mapping_id, updates, reviewer=payload.reviewer or "administrator")
        if not updated:
            raise HTTPException(status_code=404, detail=f"Mapping M-{mapping_id} not found.")
        return updated
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Database transaction failure: {str(err)}")


@router.get("/{mapping_id}/usage", response_model=Dict[str, Any])
def get_mapping_usage(
    mapping_id: int,
    repo: Repository = Depends(get_repo),
) -> Dict[str, Any]:
    """Retrieve usage events and statistics for a learned mapping."""
    mapping = repo.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=404,
            detail=f"Mapping M-{mapping_id} not found.",
        )
    return repo.get_mapping_usage_summary(mapping_id)


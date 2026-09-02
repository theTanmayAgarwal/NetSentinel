"""FastAPI router for report generation (PDF, CSV, JSON)."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import Response

from app.api.deps import get_repo
from app.persistence.repository import Repository
from app.reporting.exporter import export_csv_report, export_json_report
from app.reporting.pdf import generate_pdf_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/pdf/{audit_id}")
def download_pdf_report(audit_id: int, repo: Repository = Depends(get_repo)) -> Response:
    """Download ReportLab compiled PDF audit compliance report."""
    audit = repo.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit #{audit_id} not found.")

    try:
        pdf_bytes = generate_pdf_report(audit)
    except Exception as exc:
        logger.exception("Failed to generate PDF report for audit #%s: %s", audit_id, str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed for audit #{audit_id}. Please retry the export.",
        )

    filename = f"audit_{audit_id}_{audit.get('hostname', 'device')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@router.get("/csv/{audit_id}")
def download_csv_report(audit_id: int, repo: Repository = Depends(get_repo)) -> Response:
    """Export audit findings as a CSV spreadsheet."""
    audit = repo.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit #{audit_id} not found.")

    csv_text = export_csv_report(audit)
    filename = f"audit_{audit_id}_{audit.get('hostname', 'device')}.csv"

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/json/{audit_id}")
def download_json_report(audit_id: int, repo: Repository = Depends(get_repo)) -> Response:
    """Export complete audit report as formatted JSON."""
    audit = repo.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit #{audit_id} not found.")

    json_text = export_json_report(audit)
    filename = f"audit_{audit_id}_{audit.get('hostname', 'device')}.json"

    return Response(
        content=json_text,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

"""ReportLab PDF report generator for network security audits."""
from __future__ import annotations

import html
import logging
from io import BytesIO
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def _esc(val: Any) -> str:
    """Safely convert value to HTML-escaped string for ReportLab Paragraphs."""
    if val is None:
        return ""
    return html.escape(str(val))


def generate_pdf_report(audit_report: Dict[str, Any]) -> bytes:
    """Generate a PDF binary document for an audit report."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
        )
        h2_style = ParagraphStyle(
            "DocH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )
        code_style = ParagraphStyle(
            "DocCode",
            parent=styles["Code"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
            backColor=colors.HexColor("#f1f5f9"),
        )
        sol_style = ParagraphStyle(
            "DocSol",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#15803d"),
            fontName="Helvetica-Bold",
        )

        # Title Banner
        story.append(Paragraph("Network Security Compliance Audit Report", title_style))
        vendor_text = _esc(str(audit_report.get("vendor", "Unknown")).upper())
        platform_text = _esc(str(audit_report.get("platform", "Unknown")))
        os_ver_text = _esc(str(audit_report.get("os_version", "Unknown")))
        host_text = _esc(str(audit_report.get("hostname", "router-01")))
        file_text = _esc(str(audit_report.get("filename", "config.cfg")))

        story.append(
            Paragraph(
                f"<b>Vendor:</b> {vendor_text} | <b>Platform:</b> {platform_text} (OS {os_ver_text})<br/>"
                f"<b>Device Hostname:</b> {host_text} | <b>File:</b> {file_text}",
                body_style,
            )
        )
        story.append(Spacer(1, 10))

        # Executive Summary Table
        summary = audit_report.get("summary") or {}
        predicted = audit_report.get("predicted_after") or {}
        summary_data = [
            ["Compliance Score", f"{summary.get('score', 0)}%"],
            ["Passed Controls", str(summary.get("passed", 0))],
            ["Failed Controls", str(summary.get("failed", 0))],
            ["Unmapped Controls", str(summary.get("unmapped", 0))],
            ["Warnings", str(summary.get("warnings", 0))],
            ["Critical Findings", str(summary.get("critical", 0))],
            ["Predicted Post-Remediation Score", f"{predicted.get('score', 0)}% (+{predicted.get('delta', 0)}%)"],
        ]

        t_summary = Table(summary_data, colWidths=[200, 340])
        t_summary.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(t_summary)
        story.append(Spacer(1, 12))

        # Findings Summary Table
        story.append(Paragraph("Security Control Findings Summary", h2_style))
        findings = audit_report.get("findings") or []

        if not findings:
            story.append(Paragraph("No security findings recorded.", body_style))
        else:
            table_data = [["Control ID", "Severity", "Status", "Title", "Observed Line"]]
            for f in findings:
                status = _esc(f.get("status", "FAIL"))
                severity = _esc(f.get("severity", "MEDIUM"))
                evidence = f.get("evidence") or []
                
                # Handle string evidence or dict evidence safely
                evidence_line = ""
                if evidence:
                    first = evidence[0]
                    if isinstance(first, dict):
                        evidence_line = first.get("source_line", "") or first.get("line", "")
                    else:
                        evidence_line = str(first)

                table_data.append(
                    [
                        Paragraph(_esc(f.get("control_id", "N/A")), body_style),
                        Paragraph(severity, body_style),
                        Paragraph(status, body_style),
                        Paragraph(_esc(f.get("title", "")), body_style),
                        Paragraph(_esc(evidence_line[:40]), code_style),
                    ]
                )

            t_findings = Table(table_data, colWidths=[75, 65, 60, 170, 170])
            t_findings.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("PADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(t_findings)

        story.append(Spacer(1, 14))

        # Detailed Findings with Mandatory SOLUTION: section
        story.append(Paragraph("Detailed Control Findings & Solutions", h2_style))
        for f in findings:
            cid = _esc(f.get("control_id", "N/A"))
            title = _esc(f.get("title", ""))
            status = _esc(f.get("status", "FAIL"))
            severity = _esc(f.get("severity", "MEDIUM"))
            expected = _esc(f.get("expected", "N/A"))
            observed = _esc(f.get("observed", "N/A"))
            explanation = _esc(f.get("explanation", ""))
            
            # Extract remediation commands for solution block
            remediation = f.get("remediation") or {}
            cmds = remediation.get("commands") or []
            rem_desc = remediation.get("description") or f"Configure {title} compliance setting."

            story.append(Paragraph(f"<b>[{status}] {cid}: {title}</b> (Severity: {severity})", body_style))
            story.append(Paragraph(f"<b>EXPECTED:</b> {expected}", body_style))
            story.append(Paragraph(f"<b>OBSERVED:</b> {observed}", body_style))
            story.append(Paragraph(f"<b>EXPLANATION:</b> {explanation}", body_style))
            
            evidence_list = f.get("evidence") or []
            if evidence_list:
                story.append(Paragraph("<b>EVIDENCE:</b>", body_style))
                for ev in evidence_list[:3]:
                    ev_str = ev.get("source_line", "") if isinstance(ev, dict) else str(ev)
                    story.append(Paragraph(f"  • {_esc(ev_str)}", code_style))

            # Mandatory SOLUTION block on its own line
            story.append(Paragraph(f"<b>SOLUTION:</b> {_esc(rem_desc)}", sol_style))
            if cmds:
                for cmd in cmds:
                    story.append(Paragraph(f"  CLI > {_esc(cmd)}", code_style))

            story.append(Spacer(1, 8))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        logger.exception("Error generating PDF report: %s", str(e))
        raise e

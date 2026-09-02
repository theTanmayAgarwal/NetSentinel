"""JSON and CSV Exporters for Audit Reports."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict


def export_json_report(audit_report: Dict[str, Any]) -> str:
    """Return pretty-printed JSON string representation of audit report."""
    return json.dumps(audit_report, indent=2)


def export_csv_report(audit_report: Dict[str, Any]) -> str:
    """Return CSV formatted string of audit findings."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Audit ID",
            "Filename",
            "Vendor",
            "Hostname",
            "Control ID",
            "Title",
            "Category",
            "Framework",
            "Severity",
            "Status",
            "Observed State",
            "Expected State",
            "Remediation Commands",
        ]
    )

    audit_id = str(audit_report.get("audit_id", ""))
    filename = audit_report.get("filename", "")
    vendor = audit_report.get("vendor", "")
    hostname = audit_report.get("hostname", "")

    for f in audit_report.get("findings", []):
        rem = f.get("remediation") or {}
        cmds = "; ".join(rem.get("commands", [])) if rem else ""
        writer.writerow(
            [
                audit_id,
                filename,
                vendor,
                hostname,
                f.get("control_id", ""),
                f.get("title", ""),
                f.get("category", ""),
                f.get("framework", ""),
                f.get("severity", ""),
                f.get("status", ""),
                f.get("observed", ""),
                f.get("expected", ""),
                cmds,
            ]
        )

    return output.getvalue()

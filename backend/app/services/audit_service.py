"""Upload -> audit pipeline service.

Ties the deterministic stages together in order:
  detect -> parse -> normalize -> evaluate (final authority) ->
  attach remediations -> simulate predicted-after -> (optional) persist + log.

Returns a plain-dict report suitable for JSON APIs, reports, and the UI.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.compliance.engine import evaluate_model
from app.compliance.rules_loader import Rule, load_rules
from app.normalization.normalizer import normalize
from app.parsers.detect import detect_vendor
from app.parsers.registry import parse_config
from app.remediation.remediator import apply_effects, attach_remediations


def run_audit(
    filename: str,
    config_text: str,
    actor: str = "system",
    repo: Optional[Any] = None,
    rules: Optional[List[Rule]] = None,
) -> Dict[str, Any]:
    rules = rules if rules is not None else load_rules()

    vendor = detect_vendor(config_text)
    parse_result = parse_config(config_text, vendor)
    model = normalize(parse_result)

    findings, summary = evaluate_model(model, rules)

    remediated = attach_remediations(model.vendor, findings)
    after_model = apply_effects(model, model.vendor, remediated)
    _, after_summary = evaluate_model(after_model, rules)

    report: Dict[str, Any] = {
        "filename": filename,
        "vendor": model.vendor,
        "hostname": model.hostname,
        "summary": summary.to_dict(),
        "predicted_after": {
            "score": after_summary.score,
            "passed": after_summary.passed,
            "failed": after_summary.failed,
            "warnings": after_summary.warnings,
            "critical": after_summary.critical,
            "remediated_controls": remediated,
            "delta": round(after_summary.score - summary.score, 1),
        },
        "findings": [f.to_dict() for f in findings],
        "model": model.to_dict(),
        "unknown_lines": list(parse_result.unknown_lines),
    }

    if repo is not None:
        audit_id = repo.save_audit(report)
        report["audit_id"] = audit_id
        repo.append_log(
            actor=actor,
            action="run_audit",
            entity="audit",
            entity_id=str(audit_id),
            detail={
                "vendor": model.vendor,
                "hostname": model.hostname,
                "score": summary.score,
                "critical": summary.critical,
            },
        )

    return report

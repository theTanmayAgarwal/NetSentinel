"""Upload -> audit pipeline service.

Ties the deterministic stages together in order:
  detect -> parse -> adaptive memory lookup -> normalize -> evaluate (final authority) ->
  attach remediations -> simulate predicted-after -> (optional) persist + log.

Returns a plain-dict report suitable for JSON APIs, reports, and the UI.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.compliance.engine import evaluate_model
from app.compliance.rules_loader import Rule, load_rules
from app.normalization.normalizer import normalize
from app.parsers.detect import detect_vendor, detect_vendor_metadata
from app.parsers.registry import parse_config
from app.remediation.remediator import apply_effects, attach_remediations


def _apply_active_mapping(model: Any, param: str, raw_val: Any, line: str, mapping_id: int) -> Optional[str]:
    """Map a trusted ACTIVE learned mapping onto SecurityModel fields."""
    p_clean = (param or "").strip().lower()

    alias_map = {
        "admin_session_timeout": "idle_timeout_minutes",
        "session_timeout": "idle_timeout_minutes",
        "idle_timeout": "idle_timeout_minutes",
        "idle_timeout_minutes": "idle_timeout_minutes",
        "telnet": "telnet_enabled",
        "telnet_enabled": "telnet_enabled",
        "ssh": "ssh_enabled",
        "ssh_enabled": "ssh_enabled",
        "ssh_version": "ssh_version",
        "http": "http_mgmt_enabled",
        "http_mgmt_enabled": "http_mgmt_enabled",
        "https": "https_mgmt_enabled",
        "https_mgmt_enabled": "https_mgmt_enabled",
        "aaa": "aaa_enabled",
        "aaa_enabled": "aaa_enabled",
        "enable_secret": "enable_secret_set",
        "enable_secret_set": "enable_secret_set",
        "password_encryption": "password_encryption_enabled",
        "password_encryption_enabled": "password_encryption_enabled",
        "weak_credentials": "weak_plaintext_credentials",
        "weak_plaintext_credentials": "weak_plaintext_credentials",
        "password_min_length": "password_min_length",
        "min_password_length": "password_min_length",
        "banner": "login_banner_set",
        "login_banner_set": "login_banner_set",
        "snmp_community": "snmp_default_community",
        "snmp_default_community": "snmp_default_community",
        "logging": "logging_enabled",
        "logging_enabled": "logging_enabled",
        "ntp": "ntp_configured",
        "ntp_configured": "ntp_configured",
    }

    target_field = alias_map.get(p_clean, p_clean if hasattr(model, p_clean) else None)
    if not target_field or not hasattr(model, target_field):
        return None

    str_val = str(raw_val).strip().lower() if raw_val is not None else ""

    if target_field in (
        "telnet_enabled",
        "ssh_enabled",
        "http_mgmt_enabled",
        "https_mgmt_enabled",
        "aaa_enabled",
        "enable_secret_set",
        "password_encryption_enabled",
        "weak_plaintext_credentials",
        "login_banner_set",
        "snmp_default_community",
        "logging_enabled",
        "ntp_configured",
    ):
        typed_val: Any = True if str_val in ["true", "1", "enabled", "yes", "on", "enable"] else False
        setattr(model, target_field, typed_val)
    elif target_field == "idle_timeout_minutes":
        m_num = re.search(r"(\d+)", str_val)
        val_int = int(m_num.group(1)) if m_num else (int(raw_val) if isinstance(raw_val, int) else 5)
        minutes = (val_int // 60) if val_int > 60 else val_int
        setattr(model, target_field, minutes)
    elif target_field in ("ssh_version", "password_min_length"):
        m_num = re.search(r"(\d+)", str_val)
        val_int = int(m_num.group(1)) if m_num else (int(raw_val) if isinstance(raw_val, int) else 2)
        setattr(model, target_field, val_int)

    # Attach evidence for traceability
    evidence_line = f"{line} (Learned Mapping M-{mapping_id})"
    model.evidence.setdefault(target_field, [])
    if evidence_line not in model.evidence[target_field]:
        model.evidence[target_field].append(evidence_line)

    return target_field


def run_audit(
    filename: str,
    config_text: str,
    actor: str = "system",
    repo: Optional[Any] = None,
    rules: Optional[List[Rule]] = None,
) -> Dict[str, Any]:
    rules = rules if rules is not None else load_rules()

    vendor_meta = detect_vendor_metadata(config_text)
    vendor = detect_vendor(config_text)
    parse_result = parse_config(config_text, vendor)
    model = normalize(parse_result)

    # Adaptive Security Memory lookup and proposal generation for unknown lines (PART D & E)
    reused_mappings = []
    pending_proposals = []
    if repo is not None and parse_result.unknown_lines:
        from app.training.service import TrainingService
        ts = TrainingService(repo=repo)

        for line in parse_result.unknown_lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # 1. Check if an existing mapping (ACTIVE, PENDING, or REJECTED) matches the pattern
            existing = repo.find_mapping_by_pattern(line_clean, vendor=model.vendor)

            if existing:
                stat = (existing.get("status") or "").upper()
                if stat in ("ACTIVE", "APPROVED"):
                    pattern = (existing.get("command_pattern") or existing.get("text") or "").strip().lower()
                    param = existing.get("security_property") or existing.get("parameter")
                    exp_val = existing.get("value") or existing.get("expected_value")

                    applied_field = _apply_active_mapping(
                        model=model,
                        param=param,
                        raw_val=exp_val,
                        line=line_clean,
                        mapping_id=existing.get("id"),
                    )

                    reused_mappings.append({
                        "mapping_id": existing.get("id"),
                        "pattern": pattern,
                        "property": param,
                        "applied_field": applied_field,
                        "value": exp_val,
                        "line": line_clean,
                        "status": "ACTIVE",
                    })
                elif stat == "PENDING":
                    # Reuse existing PENDING proposal (no duplicate row created, not trusted for compliance PASS)
                    pending_proposals.append({
                        "mapping_id": existing.get("id"),
                        "pattern": existing.get("command_pattern"),
                        "property": existing.get("security_property"),
                        "value": existing.get("value"),
                        "line": line_clean,
                        "status": "PENDING",
                    })
                elif stat in ("REJECTED", "STALE", "REVOKED"):
                    # REJECTED/STALE/REVOKED is NOT trusted -> remains UNMAPPED/UNKNOWN
                    pass
            else:

                # 2. NO mapping exists -> Ask AI for structured proposal & create PENDING record
                try:
                    proposal = ts.ai_propose(
                        line=line_clean,
                        vendor=model.vendor,
                        platform=vendor_meta.get("platform", "Unknown"),
                        os_version=vendor_meta.get("os_version", "all"),
                    )
                except Exception as ai_err:
                    proposal = {
                        "property": "custom_security_setting",
                        "value": line_clean,
                        "unit": None,
                        "confidence": 0.50,
                        "reason": f"AI proposal generation fallback: {str(ai_err)}",
                    }

                # Insert PENDING learned_mapping record
                new_mapping = repo.create_mapping({
                    "vendor": model.vendor or "UnknownVendor",
                    "os_version": vendor_meta.get("os_version", "all") or "5.2",
                    "command_pattern": line_clean,
                    "security_property": proposal.get("property", "unknown_property"),
                    "value": str(proposal.get("value", "")),
                    "unit": proposal.get("unit"),
                    "category": "Secure Management",
                    "control_id": "CIS-NET-18",
                    "ai_confidence": proposal.get("confidence", 0.90),
                    "ai_proposal": proposal.get("reason", "Detected unknown syntax fragment."),
                    "status": "PENDING",
                    "version": 1,
                    "reviewer": "administrator",
                })

                pending_proposals.append({
                    "mapping_id": new_mapping["id"],
                    "pattern": new_mapping["command_pattern"],
                    "property": new_mapping["security_property"],
                    "value": new_mapping["value"],
                    "line": line_clean,
                    "status": "PENDING",
                })


    findings, summary = evaluate_model(model, rules)

    remediated = attach_remediations(model.vendor, findings)
    after_model = apply_effects(model, model.vendor, remediated)
    _, after_summary = evaluate_model(after_model, rules)

    report: Dict[str, Any] = {
        "filename": filename,
        "vendor": model.vendor,
        "platform": vendor_meta.get("platform", "Unknown"),
        "os_version": vendor_meta.get("os_version", "Unknown"),
        "confidence": vendor_meta.get("confidence", 0.0),
        "hostname": model.hostname or "router-01",
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
        "reused_mappings": reused_mappings,
        "pending_proposals": pending_proposals,
    }


    if repo is not None:
        audit_id = repo.save_audit(report)
        report["audit_id"] = audit_id

        # Record mapping usage events for each applied ACTIVE mapping (PART F)
        for rm in reused_mappings:
            if rm.get("status") == "ACTIVE":
                ctrl_id = None
                finding_id = None
                app_field = rm.get("applied_field") or rm.get("property")
                for f in findings:
                    if f.normalized_field == app_field:
                        ctrl_id = f.control_id
                        break
                repo.record_mapping_usage(
                    mapping_id=rm["mapping_id"],
                    audit_id=audit_id,
                    configuration_fragment=rm.get("line"),
                    security_property=rm.get("property"),
                    observed_value=rm.get("value"),
                    control_id=ctrl_id,
                    finding_id=finding_id,
                )

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
                "reused_mappings_count": len(reused_mappings),
            },
        )


    return report


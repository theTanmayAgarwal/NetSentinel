"""Remediation builder + predicted-compliance simulation.

Builds a syntax-validated ``Remediation`` for a given (vendor, control), and
simulates the PREDICTED post-remediation state by applying each template's
declared ``effect`` to a *copy* of the normalized model. The prediction is a
deterministic re-run of the compliance engine on the modified copy — the real
device is never touched (no auto-remediation; human approval is required).
"""
from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from app.core.types import Finding, Remediation
from app.normalization.model import SecurityModel
from app.remediation.templates import get_template
from app.remediation.validator import validate_commands


def build_remediation(vendor: str, control_id: str) -> Optional[Remediation]:
    tpl = get_template(vendor, control_id)
    if not tpl:
        return None
    ok, notes = validate_commands(vendor, tpl["commands"])
    return Remediation(
        control_id=control_id,
        vendor=vendor,
        description=tpl["description"],
        commands=list(tpl["commands"]),
        validated=ok,
        validation_notes=notes,
    )


def attach_remediations(vendor: str, findings: List[Finding]) -> List[str]:
    """Attach a remediation to each open finding that has a template.

    Returns the list of control ids that received a remediation.
    """
    remediated: List[str] = []
    for f in findings:
        if not f.is_open:
            continue
        rem = build_remediation(vendor, f.control_id)
        if rem:
            f.remediation = rem
            remediated.append(f.control_id)
    return remediated


def apply_effects(
    model: SecurityModel, vendor: str, control_ids: List[str]
) -> SecurityModel:
    """Return a COPY of ``model`` with each remediation's effect applied."""
    updated = deepcopy(model)
    for cid in control_ids:
        tpl = get_template(vendor, cid)
        if not tpl:
            continue
        for field_name, value in tpl.get("effect", {}).items():
            setattr(updated, field_name, value)
    return updated

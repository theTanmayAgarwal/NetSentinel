"""Shared test helpers (not collected as tests; filename does not match test*)."""
from __future__ import annotations

from app.compliance.engine import evaluate_model
from app.compliance.rules_loader import load_rules
from app.core.config import SAMPLE_CONFIGS_DIR
from app.normalization.normalizer import normalize
from app.parsers.registry import parse_config

_PATHS = {
    "cisco": SAMPLE_CONFIGS_DIR / "cisco" / "rtr-edge-01.cfg",
    "juniper": SAMPLE_CONFIGS_DIR / "juniper" / "srx-br-02.conf",
    "fortinet": SAMPLE_CONFIGS_DIR / "fortinet" / "fgt-dc-03.conf",
    "unknown": SAMPLE_CONFIGS_DIR / "unknown" / "other-device-01.cfg",
}


def read_sample(name: str) -> str:
    return _PATHS[name].read_text(encoding="utf-8")


def model_for(name: str):
    return normalize(parse_config(read_sample(name)))


def audit_for(name: str):
    rules = load_rules()
    model = model_for(name)
    findings, summary = evaluate_model(model, rules)
    return model, findings, summary


def finding_by(findings, control_id):
    return next(f for f in findings if f.control_id == control_id)

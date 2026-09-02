"""Load and validate compliance rules from YAML into typed ``Rule`` objects."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import yaml

from app.compliance.operators import VALID_OPERATORS
from app.core.types import Severity, Status

RULES_DIR = Path(__file__).resolve().parent / "rules"
DEFAULT_RULESET = RULES_DIR / "cis_network_v1.yaml"

_OPS_NEEDING_VALUE = {"equals", "not_equals", "min", "max", "range"}


@dataclass
class Rule:
    id: str
    title: str
    category: str
    framework: str
    field: str
    op: str
    severity: Severity
    on_missing: Status
    rationale: str = ""
    value: Any = None
    nist_mapping: Optional[str] = None
    disa_stig_mapping: Optional[str] = None
    iso_mapping: Optional[str] = None


def _coerce_rule(raw: dict, framework: str) -> Rule:
    missing = [k for k in ("id", "title", "field", "op") if not raw.get(k)]
    if missing:
        raise ValueError(f"Rule missing required keys {missing}: {raw!r}")

    op = raw["op"]
    if op not in VALID_OPERATORS:
        raise ValueError(f"Rule {raw['id']} uses unknown operator {op!r}")
    if op in _OPS_NEEDING_VALUE and "value" not in raw:
        raise ValueError(f"Rule {raw['id']} operator {op!r} requires a 'value'")

    return Rule(
        id=raw["id"],
        title=raw["title"],
        category=raw.get("category", "General"),
        framework=framework,
        field=raw["field"],
        op=op,
        value=raw.get("value"),
        severity=Severity(str(raw.get("severity", "MEDIUM")).upper()),
        on_missing=Status(str(raw.get("on_missing", "WARNING")).upper()),
        rationale=raw.get("rationale", ""),
        nist_mapping=raw.get("nist_mapping"),
        disa_stig_mapping=raw.get("disa_stig_mapping"),
        iso_mapping=raw.get("iso_mapping"),
    )


def load_rules(path: Optional[Path] = None) -> List[Rule]:
    path = Path(path) if path else DEFAULT_RULESET
    with open(path, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    framework = doc.get("framework", "CIS")
    controls = doc.get("controls", [])
    if not controls:
        raise ValueError(f"No controls found in ruleset {path}")

    rules = [_coerce_rule(item, framework) for item in controls]

    ids = [r.id for r in rules]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"Duplicate control ids in ruleset: {sorted(dupes)}")

    return rules

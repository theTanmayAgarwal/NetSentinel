"""Deterministic vendor detection (no LLM).

Scores the configuration text against a set of vendor-specific signatures and
returns the best match. Requires a minimum score so that an unfamiliar vendor
falls through to ``UNKNOWN`` (which routes every line to the learning loop)
rather than being misclassified on a single incidental match.
"""
from __future__ import annotations

import re
from typing import Dict

from app.core.types import Vendor

_MIN_SCORE = 2

_SIGNATURES: Dict[Vendor, list[str]] = {
    Vendor.CISCO: [
        r"^\s*interface (gigabitethernet|fastethernet|ethernet|loopback|vlan)",
        r"^\s*line (vty|con|aux)",
        r"transport input",
        r"service password-encryption",
        r"^\s*ip http server",
        r"enable secret",
        r"snmp-server community",
        r"^\s*aaa new-model",
    ],
    Vendor.JUNIPER: [
        r"^\s*set system ",
        r"^\s*set interfaces ",
        r"protocol-version",
        r"authorization read-only",
        r"system host-name",
        r"plain-text-password",
    ],
    Vendor.FORTINET: [
        r"^\s*config system ",
        r"^\s*set allowaccess",
        r"^\s*edit ",
        r"^\s*next\s*$",
        r"admintimeout",
        r"^\s*config log ",
        r"accprofile",
    ],
}


def score_vendors(config_text: str) -> Dict[Vendor, int]:
    text = config_text.lower()
    scores: Dict[Vendor, int] = {}
    for vendor, patterns in _SIGNATURES.items():
        scores[vendor] = sum(
            1 for pat in patterns if re.search(pat, text, re.MULTILINE)
        )
    return scores


def detect_vendor(config_text: str) -> Vendor:
    scores = score_vendors(config_text)
    best = max(scores, key=lambda v: scores[v])
    return best if scores[best] >= _MIN_SCORE else Vendor.UNKNOWN

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
    Vendor.ARUBA: [
        r"^\s*ssh server vrf",
        r"arubaos-cx",
        r"^\s*password-policy min-length",
        r"^\s*user \w+ group administrators",
        r"^\s*session-timeout ",
    ],
    Vendor.DELL: [
        r"dell networking",
        r"os10",
        r"^\s*ip ssh server enable",
        r"^\s*system-cli-timeout",
        r"^\s*security-password min-length",
        r"^\s*no ip telnet server enable",
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


def detect_vendor_metadata(config_text: str) -> dict:
    scores = score_vendors(config_text)
    best = max(scores, key=lambda v: scores[v])
    score = scores[best]
    
    if score < _MIN_SCORE:
        return {
            "vendor": Vendor.UNKNOWN.value,
            "platform": "Unknown",
            "os_version": "Unknown",
            "confidence": 0.0,
        }

    total_patterns = len(_SIGNATURES[best])
    confidence = min(round(score / total_patterns, 2) + 0.5, 0.98)

    platforms = {
        Vendor.CISCO: ("Cisco IOS / IOS-XE", "17.x"),
        Vendor.JUNIPER: ("Junos OS", "21.x"),
        Vendor.FORTINET: ("FortiOS", "7.x"),
        Vendor.ARUBA: ("ArubaOS-CX", "10.x"),
        Vendor.DELL: ("Dell OS10", "10.5.x"),
        Vendor.UNKNOWN: ("Unknown", "Unknown"),
    }
    platform, os_ver = platforms.get(best, ("Unknown", "Unknown"))

    return {
        "vendor": best.value,
        "platform": platform,
        "os_version": os_ver,
        "confidence": confidence,
    }


"""Shared domain types for the compliance engine.

Pure standard library so the entire core runs and is tested offline. Enums
subclass ``str`` so they serialize cleanly to JSON and compare to plain strings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Vendor(str, Enum):
    CISCO = "cisco"
    JUNIPER = "juniper"
    FORTINET = "fortinet"
    UNKNOWN = "unknown"


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def rank(self) -> int:
        return {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}[self.value]


@dataclass
class Remediation:
    """A device-specific, syntax-validated remediation. Never auto-applied."""

    control_id: str
    vendor: str
    description: str
    commands: List[str] = field(default_factory=list)
    validated: bool = False
    validation_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "vendor": self.vendor,
            "description": self.description,
            "commands": list(self.commands),
            "validated": self.validated,
            "validation_notes": self.validation_notes,
        }


@dataclass
class Finding:
    """A single control evaluation against one device's normalized model."""

    control_id: str
    title: str
    category: str
    framework: str
    status: Status
    severity: Severity
    rationale: str = ""
    explanation: str = ""
    evidence: List[str] = field(default_factory=list)
    normalized_field: Optional[str] = None
    expected: Optional[str] = None
    observed: Optional[str] = None
    remediation: Optional[Remediation] = None

    @property
    def is_open(self) -> bool:
        return self.status in (Status.FAIL, Status.WARNING)

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "title": self.title,
            "category": self.category,
            "framework": self.framework,
            "status": self.status.value,
            "severity": self.severity.value,
            "rationale": self.rationale,
            "explanation": self.explanation,
            "evidence": list(self.evidence),
            "normalized_field": self.normalized_field,
            "expected": self.expected,
            "observed": self.observed,
            "remediation": self.remediation.to_dict() if self.remediation else None,
        }

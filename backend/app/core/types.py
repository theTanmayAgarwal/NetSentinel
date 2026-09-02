"""Shared domain types for the compliance engine.

Pure standard library so the entire core runs and is tested offline. Enums
subclass ``str`` so they serialize cleanly to JSON and compare to plain strings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Vendor(str, Enum):
    CISCO = "cisco"
    JUNIPER = "juniper"
    FORTINET = "fortinet"
    ARUBA = "aruba"
    DELL = "dell"
    UNKNOWN = "unknown"


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNMAPPED = "UNMAPPED"
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
class SecurityFact:
    """Structured security-semantic fact extracted from config or verified memory."""

    property: str
    value: Any
    unit: Optional[str] = None
    source: str = "known_parser"  # known_parser | verified_mapping | human_corrected_mapping | unknown
    confidence: float = 1.0
    source_line: Optional[int] = None
    evidence_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "property": self.property,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "confidence": self.confidence,
            "source_line": self.source_line,
            "evidence_text": self.evidence_text,
        }


@dataclass
class ConfigurationFragment:
    """Logical fragment of configuration with line range and context preservation."""

    fragment_id: str
    source_file: str
    line_start: int
    line_end: int
    text: str
    context: str = "general"
    vendor: Optional[str] = None
    platform: Optional[str] = None
    os_version: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "fragment_id": self.fragment_id,
            "source_file": self.source_file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "text": self.text,
            "context": self.context,
            "vendor": self.vendor,
            "platform": self.platform,
            "os_version": self.os_version,
        }


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
    nist_mapping: Optional[str] = None
    disa_stig_mapping: Optional[str] = None
    iso_mapping: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.status in (Status.FAIL, Status.WARNING, Status.UNMAPPED)

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
            "nist_mapping": self.nist_mapping,
            "disa_stig_mapping": self.disa_stig_mapping,
            "iso_mapping": self.iso_mapping,
        }


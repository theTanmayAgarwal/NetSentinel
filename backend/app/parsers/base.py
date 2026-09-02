"""Parser base types and shared helpers.

A parser turns raw vendor configuration text into a ``ParseResult``: standardized
semantic keys (already vendor-neutral in *naming*), the raw config lines that
produced each key (evidence), and any security-relevant lines it did not
recognize (``unknown_lines``) — the fuel for the interactive learning loop.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.redaction import redact_line

# A line is "security-relevant" if it mentions any of these tokens. Used to decide
# whether an UNRECOGNIZED line is worth surfacing for training (vs. benign noise
# like interface descriptions or IP addressing).
_SECURITY_HINT = re.compile(
    r"\b("
    r"telnet|ssh|snmp|password|passwd|secret|aaa|login|logging|syslog|transport|"
    r"https?|ntp|timeout|banner|community|auth|admin|management|allowaccess|"
    r"service|user(name)?|access-class|privilege|crypto|tls|radius|tacacs|"
    r"firewall|rule|security|disable|deny|permit|port"
    r")\b",
    re.IGNORECASE,
)



def is_security_line(line: str) -> bool:
    return bool(_SECURITY_HINT.search(line))


@dataclass
class ParseResult:
    vendor: str
    hostname: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    unknown_lines: List[str] = field(default_factory=list)

    def record(self, key: str, value: Any, line: Optional[str] = None) -> None:
        """Record a semantic fact and (optionally) the raw line that set it."""
        self.raw[key] = value
        if line:
            self.add_evidence(key, line)

    def add_evidence(self, key: str, line: str) -> None:
        safe = redact_line(line)
        bucket = self.evidence.setdefault(key, [])
        if safe not in bucket:
            bucket.append(safe)

    def flag_unknown(self, line: str) -> None:
        line = line.strip()
        if line and is_security_line(line):
            safe = redact_line(line)
            if safe not in self.unknown_lines:
                self.unknown_lines.append(safe)

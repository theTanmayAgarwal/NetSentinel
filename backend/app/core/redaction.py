"""Secret redaction for evidence lines, logs, and reports.

Applied at evidence-capture time so every downstream consumer (API responses,
PDF/CSV/JSON reports, UI) shows redacted configuration. Redaction is precise:
it targets credential *values* while preserving the tokens a finding depends on
(e.g. the SNMP community name 'public', protocol names like 'telnet'/'http',
and directives like 'password minimum-length 6').
"""
from __future__ import annotations

import re

REDACTED = "***REDACTED***"

# Juniper quoted secrets: plain-text-password-value "X" / encrypted-password "X".
_P_QUOTED = re.compile(
    r'((?:plain-text-password(?:-value)?|encrypted-password|secret)\s+")[^"]*(")',
    re.IGNORECASE,
)

# Cisco-style trailing secret: "... secret|password [type] <value>" at end of line.
# Requires the credential to be the final token, so "password minimum-length 6"
# (two trailing tokens) is left intact.
_P_TRAILING = re.compile(
    r'\b(secret|password)\s+(\d\s+)?(\S+)\s*$',
    re.IGNORECASE,
)

# FortiOS encoded secret: "... ENC <hash>".
_P_ENC = re.compile(r'\b(ENC)\s+(\S+)', re.IGNORECASE)

# Non-default SNMP community strings are secrets; 'public'/'private' are the
# very thing the finding reports, so they are preserved.
_P_COMMUNITY = re.compile(
    r'\b(community)\s+(?!"?public"?|"?private"?)("?[^"\s]+"?)',
    re.IGNORECASE,
)


def redact_line(line: str) -> str:
    if not line:
        return line
    out = _P_QUOTED.sub(rf"\1{REDACTED}\2", line)
    out = _P_ENC.sub(rf"\1 {REDACTED}", out)
    out = _P_COMMUNITY.sub(rf"\1 {REDACTED}", out)
    out = _P_TRAILING.sub(
        lambda m: f"{m.group(1)} {m.group(2) or ''}{REDACTED}".replace("  ", " "),
        out,
    )
    return out

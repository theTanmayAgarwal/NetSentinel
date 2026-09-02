"""Deterministic parser for HPE ArubaOS-CX configurations."""
from __future__ import annotations

import re
from app.core.types import Vendor
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    res = ParseResult(vendor=Vendor.ARUBA.value)

    # Defaults
    res.record("telnet_enabled", True)  # default until disabled explicitly
    res.record("ssh_enabled", False)
    res.record("ssh_version", 2)
    res.record("password_min_length", 8)
    res.record("snmp_default_community", False)
    res.record("logging_enabled", False)
    res.record("session_timeout", 300)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue

        # Hostname
        m_host = re.match(r"^hostname\s+(\S+)", line, re.IGNORECASE)
        if m_host:
            res.hostname = m_host.group(1)
            res.record("hostname", m_host.group(1), line)
            continue

        # SSH server
        if re.search(r"^ssh\s+server\s+vrf", line, re.IGNORECASE):
            res.record("ssh_enabled", True, line)
            res.record("ssh_version", 2, line)
            continue

        # Telnet disabled
        if re.search(r"^no\s+ssh\s+server\s+vty.*telnet", line, re.IGNORECASE) or re.search(r"^no\s+telnet\s+server", line, re.IGNORECASE):
            res.record("telnet_enabled", False, line)
            continue

        # Password Policy
        m_pwd = re.search(r"password-policy\s+min-length\s+(\d+)", line, re.IGNORECASE)
        if m_pwd:
            res.record("password_min_length", int(m_pwd.group(1)), line)
            continue

        # Session Timeout
        m_tout = re.search(r"session-timeout\s+(\d+)", line, re.IGNORECASE)
        if m_tout:
            res.record("session_timeout", int(m_tout.group(1)), line)
            continue

        # SNMP
        if re.search(r"snmp-server\s+community\s+public", line, re.IGNORECASE):
            res.record("snmp_default_community", True, line)
            continue

        # Logging
        if re.search(r"^logging\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line, re.IGNORECASE):
            res.record("logging_enabled", True, line)
            continue

        res.flag_unknown(line)

    return res

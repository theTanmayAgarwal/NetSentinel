"""Deterministic parser for Dell OS10 configurations."""
from __future__ import annotations

import re
from app.core.types import Vendor
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    res = ParseResult(vendor=Vendor.DELL.value)

    # Defaults
    res.record("telnet_enabled", True)
    res.record("ssh_enabled", False)
    res.record("ssh_version", 1)
    res.record("password_min_length", 8)
    res.record("snmp_default_community", False)
    res.record("logging_enabled", False)
    res.record("session_timeout", 300)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!") or line.startswith("#"):
            continue

        # Hostname
        m_host = re.match(r"^hostname\s+(\S+)", line, re.IGNORECASE)
        if m_host:
            res.hostname = m_host.group(1)
            res.record("hostname", m_host.group(1), line)
            continue

        # SSH server enable
        if re.search(r"^ip\s+ssh\s+server\s+enable", line, re.IGNORECASE):
            res.record("ssh_enabled", True, line)
            continue

        # SSH version
        m_ssh_ver = re.search(r"^ip\s+ssh\s+version\s+(\d+)", line, re.IGNORECASE)
        if m_ssh_ver:
            res.record("ssh_version", int(m_ssh_ver.group(1)), line)
            continue

        # Telnet disabled
        if re.search(r"^no\s+ip\s+telnet\s+server\s+enable", line, re.IGNORECASE):
            res.record("telnet_enabled", False, line)
            continue

        # Security password min length
        m_pwd = re.search(r"security-password\s+min-length\s+(\d+)", line, re.IGNORECASE)
        if m_pwd:
            res.record("password_min_length", int(m_pwd.group(1)), line)
            continue

        # CLI timeout
        m_tout = re.search(r"system-cli-timeout\s+(\d+)", line, re.IGNORECASE)
        if m_tout:
            res.record("session_timeout", int(m_tout.group(1)), line)
            continue

        # SNMP
        if re.search(r"snmp-server\s+community\s+(public|private)\b", line, re.IGNORECASE):
            res.record("snmp_default_community", True, line)
            continue

        # Logging
        if re.search(r"^logging\s+server", line, re.IGNORECASE):
            res.record("logging_enabled", True, line)
            continue

        res.flag_unknown(line)

    return res

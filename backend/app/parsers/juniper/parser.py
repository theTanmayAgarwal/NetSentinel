"""Juniper Junos configuration parser (set format; deterministic — no LLM)."""
from __future__ import annotations

import re

from app.core.types import Vendor
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    pr = ParseResult(vendor=Vendor.JUNIPER.value)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()

        m = re.match(r"set system host-name\s+(\S+)", line, re.IGNORECASE)
        if m:
            pr.hostname = m.group(1)
            pr.record("hostname", m.group(1), line)
            continue

        if "set system services telnet" in low:
            pr.record("telnet_enabled", True, line)
            continue

        m = re.search(r"set system services ssh protocol-version\s+(\d+)", low)
        if m:
            pr.record("ssh_version", int(m.group(1)), line)
            pr.record("ssh_enabled", True, line)
            continue
        if "set system services ssh" in low:
            pr.record("ssh_enabled", True, line)
            continue

        if "set system services web-management https" in low:
            pr.record("https_mgmt_enabled", True, line)
            continue
        if "set system services web-management http" in low:
            pr.record("http_mgmt_enabled", True, line)
            continue

        m = re.search(r"password minimum-length\s+(\d+)", low)
        if m:
            pr.record("password_min_length", int(m.group(1)), line)
            continue

        if "plain-text-password" in low:
            pr.record("weak_plaintext_credentials", True, line)
            continue

        m = re.match(r"set snmp community\s+(\S+)", low)
        if m:
            community = m.group(1).strip('"')
            pr.record("snmp_default_community", community in ("public", "private"), line)
            continue

        if "set system syslog host" in low:
            pr.record("logging_enabled", True, line)
            continue

        if re.search(r"set system ntp server\s+\S+", low):
            pr.record("ntp_configured", True, line)
            continue

        if "set system login message" in low or "set system login announcement" in low:
            pr.record("login_banner_set", True, line)
            continue

        pr.flag_unknown(line)

    return pr

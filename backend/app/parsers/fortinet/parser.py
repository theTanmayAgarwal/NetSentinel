"""Fortinet FortiOS configuration parser (block-structured; deterministic — no LLM).

FortiOS groups directives into ``config <section> ... end`` blocks with nested
``edit <name> ... next`` entries. The meaning of a generic directive like
``set status enable`` depends on its enclosing section, so we track a section
stack while scanning.
"""
from __future__ import annotations

import re

from app.core.types import Vendor
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    pr = ParseResult(vendor=Vendor.FORTINET.value)
    stack: list[str] = []      # enclosing "config <section>" names
    snmp_name: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()

        m = re.match(r"config\s+(.+)$", low)
        if m:
            stack.append(m.group(1).strip())
            continue
        if low == "end":
            if stack:
                stack.pop()
            snmp_name = None
            continue
        if low == "next":
            snmp_name = None
            continue
        if low.startswith("edit "):
            continue

        section = stack[-1] if stack else ""

        m = re.match(r'set hostname\s+"?([^"]+)"?', line, re.IGNORECASE)
        if m and "global" in section:
            pr.hostname = m.group(1)
            pr.record("hostname", m.group(1), line)
            continue

        m = re.match(r"set admintimeout\s+(\d+)", low)
        if m:
            pr.record("idle_timeout_minutes", int(m.group(1)), line)
            continue

        if re.match(r"set admin-https\s+enable", low):
            pr.record("https_mgmt_enabled", True, line)
            continue
        if re.match(r"set admin-http\s+enable", low):
            pr.record("http_mgmt_enabled", True, line)
            continue

        if low.startswith("set allowaccess"):
            protos = low.split("set allowaccess", 1)[1].split()
            if "telnet" in protos:
                pr.record("telnet_enabled", True, line)
            if "ssh" in protos:
                pr.record("ssh_enabled", True, line)
            if "https" in protos:
                pr.record("https_mgmt_enabled", True, line)
            if "http" in protos:
                pr.record("http_mgmt_enabled", True, line)
            continue

        if "system admin" in section and low.startswith("set password"):
            # "ENC ..." is a stored hash (acceptable); anything else is cleartext.
            if "enc" not in low:
                pr.record("weak_plaintext_credentials", True, line)
            continue

        if "snmp community" in section:
            m = re.match(r'set name\s+"?([^"]+)"?', line, re.IGNORECASE)
            if m:
                snmp_name = m.group(1).lower()
                pr.add_evidence("snmp_default_community", line)
                continue
            if low.startswith("set status enable") and snmp_name in ("public", "private"):
                pr.record("snmp_default_community", True, line)
                continue

        if "log syslogd" in section or "log " in section:
            if low.startswith("set status disable"):
                pr.record("logging_enabled", False, line)
                continue
            if low.startswith("set status enable"):
                pr.record("logging_enabled", True, line)
                continue

        if low.startswith("set accprofile") or low.startswith("set ip "):
            continue

        pr.flag_unknown(line)

    return pr

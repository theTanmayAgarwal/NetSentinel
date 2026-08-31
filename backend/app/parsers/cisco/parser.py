"""Cisco IOS configuration parser (deterministic, regex-based — no LLM)."""
from __future__ import annotations

import re

from app.core.types import Vendor
from app.normalization.model import INFINITE_TIMEOUT
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    pr = ParseResult(vendor=Vendor.CISCO.value)
    timeouts: list[int] = []
    timeout_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue
        low = line.lower()

        m = re.match(r"hostname\s+(\S+)", line, re.IGNORECASE)
        if m:
            pr.hostname = m.group(1)
            pr.record("hostname", m.group(1), line)
            continue

        # --- privileged-mode credential ---
        if re.match(r"enable\s+secret\b", low):
            pr.record("enable_secret_set", True, line)
            continue
        if re.match(r"enable\s+password\b", low):
            pr.record("enable_secret_set", False, line)
            pr.record("weak_plaintext_credentials", True, line)
            continue

        # --- password storage ---
        if re.match(r"no\s+service\s+password-encryption", low):
            pr.record("password_encryption_enabled", False, line)
            continue
        if re.match(r"service\s+password-encryption", low):
            pr.record("password_encryption_enabled", True, line)
            continue

        if re.match(r"aaa\s+new-model", low):
            pr.record("aaa_enabled", True, line)
            continue

        # --- local users ---
        if low.startswith("username "):
            if re.search(r"\bsecret\b", low):
                pass  # hashed secret — acceptable
            elif re.search(r"\bpassword\s+7\b", low) or re.search(r"\bpassword\s+0\b", low):
                pr.record("weak_plaintext_credentials", True, line)  # type 0/7 = cleartext/weak
            elif re.search(r"\bpassword\b", low):
                pr.record("weak_plaintext_credentials", True, line)  # untyped = cleartext
            continue

        m = re.match(r"ip\s+ssh\s+version\s+(\d+)", low)
        if m:
            pr.record("ssh_version", int(m.group(1)), line)
            pr.record("ssh_enabled", True, line)
            continue

        m = re.match(r"exec-timeout\s+(\d+)(?:\s+(\d+))?", low)
        if m:
            minutes = int(m.group(1))
            timeouts.append(INFINITE_TIMEOUT if minutes == 0 else minutes)
            timeout_lines.append(line)
            continue

        if low.startswith("transport input"):
            protos = low.split("transport input", 1)[1].split()
            if "telnet" in protos or "all" in protos:
                pr.record("telnet_enabled", True, line)
            if "ssh" in protos or "all" in protos:
                pr.record("ssh_enabled", True, line)
            if protos == ["none"]:
                pr.record("telnet_enabled", False, line)
            continue

        if re.match(r"snmp-server\s+community\s+(public|private)\b", low):
            pr.record("snmp_default_community", True, line)
            continue
        if re.match(r"snmp-server\s+community\s+\S+", low):
            pr.record("snmp_default_community", False, line)
            continue

        if re.match(r"no\s+ip\s+http\s+secure-server", low):
            pr.record("https_mgmt_enabled", False, line)
            continue
        if re.match(r"ip\s+http\s+secure-server", low):
            pr.record("https_mgmt_enabled", True, line)
            continue
        if re.match(r"no\s+ip\s+http\s+server", low):
            pr.record("http_mgmt_enabled", False, line)
            continue
        if re.match(r"ip\s+http\s+server", low):
            pr.record("http_mgmt_enabled", True, line)
            continue

        if re.match(r"logging\s+(host\s+\S+|\d+\.\d+\.\d+\.\d+|buffered|trap)", low):
            pr.record("logging_enabled", True, line)
            continue

        if re.match(r"ntp\s+server\s+\S+", low):
            pr.record("ntp_configured", True, line)
            continue

        if re.match(r"banner\b", low):
            pr.record("login_banner_set", True, line)
            continue

        # recognized context / no-op lines
        if re.match(r"login\b", low) or re.match(r"line\s+", low):
            continue

        pr.flag_unknown(line)

    if timeouts:
        pr.raw["idle_timeout_minutes"] = max(timeouts)
        for tl in timeout_lines:
            pr.add_evidence("idle_timeout_minutes", tl)

    return pr

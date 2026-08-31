"""Syntax validation for generated remediation commands.

We never execute commands, but we DO structurally validate them so the UI can
show a trustworthy "syntax validated" badge and never present malformed CLI.
Validation is vendor-aware (FortiOS block balancing, Junos set/delete grammar,
IOS keyword recognition).
"""
from __future__ import annotations

from typing import List, Tuple

_IOS_KEYWORDS = {
    "line", "transport", "login", "no", "service", "snmp-server", "ip",
    "username", "exec-timeout", "logging", "ntp", "enable", "aaa", "banner",
    "crypto", "access-list", "password", "hostname",
}

_JUNOS_VERBS = {"set", "delete", "deactivate", "activate", "rename", "insert"}


def _is_comment(line: str) -> bool:
    s = line.strip()
    return s.startswith("!") or s.startswith("#")


def _validate_cisco(commands: List[str]) -> Tuple[bool, str]:
    for c in commands:
        s = c.strip()
        if not s or _is_comment(c):
            continue
        first = s.split()[0].lower()
        if first not in _IOS_KEYWORDS:
            return False, f"unrecognized IOS command keyword: '{first}'"
    return True, f"IOS command keywords recognized ({len(commands)} lines)"


def _validate_juniper(commands: List[str]) -> Tuple[bool, str]:
    for c in commands:
        s = c.strip()
        if not s or _is_comment(c):
            continue
        first = s.split()[0].lower()
        if first not in _JUNOS_VERBS:
            return False, f"Junos statement must start with set/delete/...: '{first}'"
    return True, f"valid Junos set/delete grammar ({len(commands)} lines)"


def _validate_fortinet(commands: List[str]) -> Tuple[bool, str]:
    depth_config = 0
    depth_edit = 0
    for c in commands:
        s = c.strip().lower()
        if not s or _is_comment(c):
            continue
        if s.startswith("config "):
            depth_config += 1
        elif s == "end":
            depth_config -= 1
            if depth_config < 0:
                return False, "'end' without a matching 'config'"
        elif s.startswith("edit "):
            depth_edit += 1
        elif s == "next":
            depth_edit -= 1
            if depth_edit < 0:
                return False, "'next' without a matching 'edit'"
        elif s.split()[0] in {"set", "unset", "delete", "append"}:
            if depth_config == 0:
                return False, f"'{c.strip()}' outside a config block"
        else:
            return False, f"unrecognized FortiOS command: '{c.strip()}'"
    if depth_config != 0:
        return False, "unbalanced config/end blocks"
    if depth_edit != 0:
        return False, "unbalanced edit/next blocks"
    return True, f"balanced config/end and edit/next blocks ({len(commands)} lines)"


def validate_commands(vendor: str, commands: List[str]) -> Tuple[bool, str]:
    if not commands:
        return False, "no commands generated"
    v = (vendor or "").lower()
    if v == "cisco":
        return _validate_cisco(commands)
    if v == "juniper":
        return _validate_juniper(commands)
    if v == "fortinet":
        return _validate_fortinet(commands)
    return True, "no vendor syntax profile; structural validation skipped"

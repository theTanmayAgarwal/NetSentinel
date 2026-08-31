"""Device-specific remediation templates (deterministic — no LLM invents CLI).

Keyed by (vendor, control_id). Each template provides:
  * description : human summary of the fix
  * commands    : exact CLI lines an operator would apply (with <PLACEHOLDERS>
                  for site-specific values — never real IPs/secrets)
  * effect      : the normalized field(s) this fix sets to their compliant value,
                  used to simulate the PREDICTED post-remediation compliance.

These commands are shown for human review only. Nothing here is ever executed
against a device (see project guardrails: no SSH, no auto-remediation).
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

# (vendor, control_id) -> template
TEMPLATES: Dict[Tuple[str, str], Dict[str, Any]] = {
    # ---------------- Cisco IOS ----------------
    ("cisco", "NET-01"): {
        "description": "Disable Telnet on VTY lines; allow SSH only.",
        "commands": ["line vty 0 4", " transport input ssh", " login local"],
        "effect": {"telnet_enabled": False},
    },
    ("cisco", "NET-04"): {
        "description": "Disable the plaintext HTTP management server.",
        "commands": ["no ip http server"],
        "effect": {"http_mgmt_enabled": False},
    },
    ("cisco", "NET-05"): {
        "description": "Remove default SNMP community and configure a strong one.",
        "commands": [
            "no snmp-server community public",
            "snmp-server community <STRONG-COMMUNITY> RO",
        ],
        "effect": {"snmp_default_community": False},
    },
    ("cisco", "NET-08"): {
        "description": "Enable encryption of stored plaintext passwords.",
        "commands": ["service password-encryption"],
        "effect": {"password_encryption_enabled": True},
    },
    ("cisco", "NET-09"): {
        "description": "Replace cleartext/type-7 credentials with hashed secrets.",
        "commands": [
            "! remove the cleartext local user",
            "no username netadmin",
            "username netadmin privilege 15 secret <STRONG-SECRET>",
        ],
        "effect": {"weak_plaintext_credentials": False},
    },
    ("cisco", "NET-11"): {
        "description": "Set a 10-minute administrative idle timeout on console and VTY.",
        "commands": [
            "line con 0",
            " exec-timeout 10 0",
            "line vty 0 4",
            " exec-timeout 10 0",
        ],
        "effect": {"idle_timeout_minutes": 10},
    },
    ("cisco", "NET-13"): {
        "description": "Enable remote syslog to a central collector.",
        "commands": ["logging host <SYSLOG-IP>", "logging trap informational"],
        "effect": {"logging_enabled": True},
    },
    ("cisco", "NET-14"): {
        "description": "Configure an authoritative NTP server.",
        "commands": ["ntp server <NTP-IP>"],
        "effect": {"ntp_configured": True},
    },

    # ---------------- Juniper Junos ----------------
    ("juniper", "NET-01"): {
        "description": "Remove the Telnet management service.",
        "commands": ["delete system services telnet"],
        "effect": {"telnet_enabled": False},
    },
    ("juniper", "NET-04"): {
        "description": "Remove plaintext HTTP web-management.",
        "commands": ["delete system services web-management http"],
        "effect": {"http_mgmt_enabled": False},
    },
    ("juniper", "NET-05"): {
        "description": "Remove default SNMP community and set a strong one.",
        "commands": [
            "delete snmp community public",
            "set snmp community <STRONG-COMMUNITY> authorization read-only",
        ],
        "effect": {"snmp_default_community": False},
    },
    ("juniper", "NET-09"): {
        "description": "Replace plain-text-password with hashed authentication.",
        "commands": [
            "delete system login user netops authentication plain-text-password-value",
            "set system login user netops authentication encrypted-password <HASH>",
        ],
        "effect": {"weak_plaintext_credentials": False},
    },
    ("juniper", "NET-10"): {
        "description": "Enforce a minimum password length of at least 8.",
        "commands": ["set system login password minimum-length 12"],
        "effect": {"password_min_length": 12},
    },

    # ---------------- Fortinet FortiOS ----------------
    ("fortinet", "NET-01"): {
        "description": "Remove Telnet from the interface administrative access list.",
        "commands": [
            "config system interface",
            " edit port1",
            "  set allowaccess ping https ssh",
            " next",
            "end",
        ],
        "effect": {"telnet_enabled": False},
    },
    ("fortinet", "NET-03"): {
        "description": "Disable the deprecated SSHv1 protocol.",
        "commands": ["config system global", " set admin-ssh-v1 disable", "end"],
        "effect": {"ssh_version": 2},
    },
    ("fortinet", "NET-04"): {
        "description": "Disable HTTP admin access and remove HTTP from the interface.",
        "commands": [
            "config system global",
            " set admin-http disable",
            "end",
            "config system interface",
            " edit port1",
            "  set allowaccess ping https ssh",
            " next",
            "end",
        ],
        "effect": {"http_mgmt_enabled": False},
    },
    ("fortinet", "NET-05"): {
        "description": "Rename the default 'public' SNMP community to a strong value.",
        "commands": [
            "config system snmp community",
            " edit 1",
            "  set name <STRONG-COMMUNITY>",
            " next",
            "end",
        ],
        "effect": {"snmp_default_community": False},
    },
    ("fortinet", "NET-11"): {
        "description": "Set the administrative idle timeout to 10 minutes.",
        "commands": ["config system global", " set admintimeout 10", "end"],
        "effect": {"idle_timeout_minutes": 10},
    },
    ("fortinet", "NET-13"): {
        "description": "Enable syslog logging to a central collector.",
        "commands": [
            "config log syslogd setting",
            " set status enable",
            " set server <SYSLOG-IP>",
            "end",
        ],
        "effect": {"logging_enabled": True},
    },
}


def get_template(vendor: str, control_id: str) -> Dict[str, Any] | None:
    return TEMPLATES.get((vendor, control_id))

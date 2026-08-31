"""The vendor-neutral security model.

Every vendor parser's output is normalized into this common schema, so the
compliance engine evaluates one representation regardless of original syntax.
A field of ``None`` means "not determined from the configuration"; rules decide
how to treat missing data (see ``on_missing`` in the rule definitions).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# The evaluable normalized fields (used by the engine and for serialization).
NORMALIZED_FIELDS: List[str] = [
    "telnet_enabled",
    "ssh_enabled",
    "ssh_version",
    "http_mgmt_enabled",
    "https_mgmt_enabled",
    "aaa_enabled",
    "enable_secret_set",
    "password_encryption_enabled",
    "weak_plaintext_credentials",
    "password_min_length",
    "idle_timeout_minutes",
    "login_banner_set",
    "snmp_default_community",
    "logging_enabled",
    "ntp_configured",
]

# Sentinel for "no timeout / session never expires" (e.g. Cisco exec-timeout 0 0).
INFINITE_TIMEOUT = 100_000


@dataclass
class SecurityModel:
    vendor: str = "unknown"
    hostname: Optional[str] = None

    # --- Secure management ---
    telnet_enabled: Optional[bool] = None
    ssh_enabled: Optional[bool] = None
    ssh_version: Optional[int] = None
    http_mgmt_enabled: Optional[bool] = None
    https_mgmt_enabled: Optional[bool] = None

    # --- Authentication / passwords ---
    aaa_enabled: Optional[bool] = None
    enable_secret_set: Optional[bool] = None
    password_encryption_enabled: Optional[bool] = None
    weak_plaintext_credentials: Optional[bool] = None
    password_min_length: Optional[int] = None

    # --- Session / access ---
    idle_timeout_minutes: Optional[int] = None
    login_banner_set: Optional[bool] = None

    # --- SNMP ---
    snmp_default_community: Optional[bool] = None

    # --- Logging / time ---
    logging_enabled: Optional[bool] = None
    ntp_configured: Optional[bool] = None

    # Traceability: normalized field name -> raw config line(s) that determined it.
    evidence: Dict[str, List[str]] = field(default_factory=dict)

    def get(self, name: str):
        return getattr(self, name, None)

    def evidence_for(self, name: str) -> List[str]:
        return list(self.evidence.get(name, []))

    def to_dict(self) -> dict:
        data = {name: getattr(self, name) for name in NORMALIZED_FIELDS}
        data["vendor"] = self.vendor
        data["hostname"] = self.hostname
        data["evidence"] = {k: list(v) for k, v in self.evidence.items()}
        return data

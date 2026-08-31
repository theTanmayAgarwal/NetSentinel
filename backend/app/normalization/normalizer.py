"""Normalization: ParseResult -> SecurityModel.

Parsers already emit standardized semantic keys, so normalization is mostly a
typed transfer plus a few cross-field derivations and evidence carry-over. This
keeps a single, vendor-agnostic representation for the compliance engine.
"""
from __future__ import annotations

from app.normalization.model import NORMALIZED_FIELDS, SecurityModel
from app.parsers.base import ParseResult


def normalize(result: ParseResult) -> SecurityModel:
    model = SecurityModel(vendor=result.vendor, hostname=result.hostname)

    for field_name in NORMALIZED_FIELDS:
        if field_name in result.raw:
            setattr(model, field_name, result.raw[field_name])

    for key, lines in result.evidence.items():
        if key in NORMALIZED_FIELDS:
            model.evidence[key] = list(lines)

    # --- derivations ---
    # A configured SSH version implies SSH is enabled.
    if model.ssh_version is not None and model.ssh_enabled is None:
        model.ssh_enabled = True

    return model

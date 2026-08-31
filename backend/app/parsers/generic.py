"""Generic parser for UNKNOWN / unfamiliar vendors.

We deliberately recognize nothing here: every security-relevant line is routed
to ``unknown_lines`` so it can be taught through the interactive learning loop
(Milestone 3) rather than silently ignored. Benign lines (comments, addressing)
are dropped.
"""
from __future__ import annotations

from app.core.types import Vendor
from app.parsers.base import ParseResult


def parse(text: str) -> ParseResult:
    pr = ParseResult(vendor=Vendor.UNKNOWN.value)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        pr.flag_unknown(line)
    return pr

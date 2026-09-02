"""Parser registry: detect vendor and dispatch to the matching parser."""
from __future__ import annotations

from typing import Callable, Dict, Optional

from app.core.types import Vendor
from app.parsers import aruba as aruba_parser
from app.parsers import dell as dell_parser
from app.parsers import generic
from app.parsers.base import ParseResult
from app.parsers.cisco import parser as cisco_parser
from app.parsers.detect import detect_vendor
from app.parsers.fortinet import parser as fortinet_parser
from app.parsers.juniper import parser as juniper_parser

_PARSERS: Dict[Vendor, Callable[[str], ParseResult]] = {
    Vendor.CISCO: cisco_parser.parse,
    Vendor.JUNIPER: juniper_parser.parse,
    Vendor.FORTINET: fortinet_parser.parse,
    Vendor.ARUBA: aruba_parser.parse,
    Vendor.DELL: dell_parser.parse,
    Vendor.UNKNOWN: generic.parse,
}



def parse_config(text: str, vendor: Optional[Vendor] = None) -> ParseResult:
    """Parse ``text``. If ``vendor`` is omitted, detect it deterministically."""
    resolved = vendor or detect_vendor(text)
    parser = _PARSERS.get(resolved, generic.parse)
    result = parser(text)
    result.vendor = resolved.value
    return result

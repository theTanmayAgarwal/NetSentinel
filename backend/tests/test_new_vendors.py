"""Unit tests for HPE Aruba, Dell OS10 parsers and vendor detection."""
import unittest

from app.parsers.detect import detect_vendor, detect_vendor_metadata
from app.parsers.aruba import parse as aruba_parse
from app.parsers.dell import parse as dell_parse
from app.core.types import Vendor

class TestNewVendors(unittest.TestCase):
    def test_aruba_detection_and_parsing(self):
        cfg = """hostname aruba-core-sw01
ssh server vrf default
no ssh server vty-0-4 telnet
snmp-server community public operator
logging 192.168.10.50 severity info
password-policy min-length 12
session-timeout 900
"""
        vendor = detect_vendor(cfg)
        meta = detect_vendor_metadata(cfg)
        self.assertEqual(vendor, Vendor.ARUBA)
        self.assertEqual(meta["vendor"], Vendor.ARUBA)

        parse_res = aruba_parse(cfg)
        facts = parse_res.raw

        self.assertEqual(facts.get("ssh_enabled"), True)
        self.assertEqual(facts.get("telnet_enabled"), False)
        self.assertEqual(facts.get("snmp_default_community"), True)
        self.assertEqual(facts.get("password_min_length"), 12)
        self.assertEqual(facts.get("session_timeout"), 900)

    def test_dell_detection_and_parsing(self):
        cfg = """hostname dell-s5248-sw01
security-password min-length 14
ip ssh server enable
ip ssh version 2
no ip telnet server enable
snmp-server community secret-ro ro
logging server 192.168.20.100 severity informational
system-cli-timeout 600
"""
        vendor = detect_vendor(cfg)
        meta = detect_vendor_metadata(cfg)
        self.assertEqual(vendor, Vendor.DELL)
        self.assertEqual(meta["vendor"], Vendor.DELL)

        parse_res = dell_parse(cfg)
        facts = parse_res.raw

        self.assertEqual(facts.get("ssh_enabled"), True)
        self.assertEqual(facts.get("telnet_enabled"), False)
        self.assertEqual(facts.get("snmp_default_community"), False)
        self.assertEqual(facts.get("password_min_length"), 14)

if __name__ == "__main__":
    unittest.main()

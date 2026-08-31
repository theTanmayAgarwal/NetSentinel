"""Vendor detection tests."""
import unittest

from app.core.types import Vendor
from app.parsers.detect import detect_vendor
from tests.support import read_sample


class TestVendorDetection(unittest.TestCase):
    def test_cisco_detected(self):
        self.assertEqual(detect_vendor(read_sample("cisco")), Vendor.CISCO)

    def test_juniper_detected(self):
        self.assertEqual(detect_vendor(read_sample("juniper")), Vendor.JUNIPER)

    def test_fortinet_detected(self):
        self.assertEqual(detect_vendor(read_sample("fortinet")), Vendor.FORTINET)

    def test_unknown_falls_through(self):
        # An unfamiliar vendor must NOT be misclassified; it routes to UNKNOWN.
        self.assertEqual(detect_vendor(read_sample("unknown")), Vendor.UNKNOWN)

    def test_empty_config_is_unknown(self):
        self.assertEqual(detect_vendor(""), Vendor.UNKNOWN)


if __name__ == "__main__":
    unittest.main()

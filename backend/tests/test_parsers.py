"""Parser + normalization tests: assert exact extracted facts and that known
vendor configs produce no unknown-line noise."""
import unittest

from app.parsers.registry import parse_config
from tests.support import model_for, read_sample


class TestCiscoParser(unittest.TestCase):
    def setUp(self):
        self.m = model_for("cisco")

    def test_hostname(self):
        self.assertEqual(self.m.hostname, "RTR-EDGE-01")

    def test_management_facts(self):
        self.assertTrue(self.m.telnet_enabled)      # transport input telnet ssh
        self.assertTrue(self.m.ssh_enabled)
        self.assertEqual(self.m.ssh_version, 2)
        self.assertTrue(self.m.http_mgmt_enabled)
        self.assertFalse(self.m.https_mgmt_enabled)

    def test_auth_facts(self):
        self.assertTrue(self.m.aaa_enabled)
        self.assertTrue(self.m.enable_secret_set)
        self.assertFalse(self.m.password_encryption_enabled)  # 'no service password-encryption'
        self.assertTrue(self.m.weak_plaintext_credentials)    # username ... password 0

    def test_infinite_idle_timeout(self):
        # exec-timeout 0 0 => never expires => sentinel value
        self.assertGreaterEqual(self.m.idle_timeout_minutes, 100_000)

    def test_snmp_default_community(self):
        self.assertTrue(self.m.snmp_default_community)


class TestJuniperParser(unittest.TestCase):
    def setUp(self):
        self.m = model_for("juniper")

    def test_facts(self):
        self.assertEqual(self.m.hostname, "SRX-BR-02")
        self.assertTrue(self.m.telnet_enabled)
        self.assertEqual(self.m.ssh_version, 2)
        self.assertTrue(self.m.http_mgmt_enabled)
        self.assertTrue(self.m.weak_plaintext_credentials)  # plain-text-password
        self.assertEqual(self.m.password_min_length, 6)
        self.assertTrue(self.m.snmp_default_community)
        self.assertTrue(self.m.logging_enabled)
        self.assertTrue(self.m.ntp_configured)
        self.assertTrue(self.m.login_banner_set)


class TestFortinetParser(unittest.TestCase):
    def setUp(self):
        self.m = model_for("fortinet")

    def test_facts(self):
        self.assertEqual(self.m.hostname, "FGT-DC-03")
        self.assertTrue(self.m.telnet_enabled)           # allowaccess ... telnet
        self.assertTrue(self.m.ssh_enabled)
        self.assertTrue(self.m.http_mgmt_enabled)        # admin-http + allowaccess http
        self.assertEqual(self.m.idle_timeout_minutes, 480)
        self.assertTrue(self.m.snmp_default_community)   # community name "public" enabled
        self.assertFalse(self.m.logging_enabled)         # syslogd status disable

    def test_enc_password_not_flagged_weak(self):
        # "set password ENC <hash>" is a stored hash, not cleartext
        self.assertIsNone(self.m.weak_plaintext_credentials)


class TestUnknownVendorRouting(unittest.TestCase):
    def test_all_security_lines_are_unknown(self):
        pr = parse_config(read_sample("unknown"))
        self.assertEqual(pr.vendor, "unknown")
        # every security-relevant line in the sample should surface for training
        self.assertEqual(len(pr.unknown_lines), 7)
        joined = "\n".join(pr.unknown_lines)
        self.assertIn("telnet", joined)
        self.assertIn("snmp-server community", joined)


class TestNoNoiseForKnownVendors(unittest.TestCase):
    def test_known_configs_have_no_unknown_lines(self):
        for name in ("cisco", "juniper", "fortinet"):
            pr = parse_config(read_sample(name))
            self.assertEqual(
                pr.unknown_lines, [], f"{name} produced unexpected unknown lines"
            )


if __name__ == "__main__":
    unittest.main()

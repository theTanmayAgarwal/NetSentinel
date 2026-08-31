"""Secret redaction tests."""
import unittest

from app.core.redaction import REDACTED, redact_line


class TestRedaction(unittest.TestCase):
    def test_benign_lines_untouched(self):
        for line in [
            "no service password-encryption",
            "transport input telnet ssh",
            "ip http server",
            "snmp-server community public RO",
            "set system login password minimum-length 6",
            'set name "public"',
        ]:
            self.assertEqual(redact_line(line), line, f"unexpected redaction of: {line}")

    def test_cisco_cleartext_password_redacted(self):
        out = redact_line("username netadmin privilege 15 password 0 CHANGEME-DEMO")
        self.assertIn(REDACTED, out)
        self.assertNotIn("CHANGEME-DEMO", out)
        self.assertIn("password 0", out)  # keyword + type retained

    def test_enable_secret_hash_redacted(self):
        out = redact_line("enable secret 5 $1$abcd$EFGHijklmnop")
        self.assertIn(REDACTED, out)
        self.assertNotIn("$1$abcd$EFGHijklmnop", out)

    def test_juniper_quoted_secret_redacted(self):
        out = redact_line('set ... plain-text-password-value "SECRET-VALUE"')
        self.assertIn(REDACTED, out)
        self.assertNotIn("SECRET-VALUE", out)

    def test_fortinet_enc_redacted(self):
        out = redact_line("set password ENC SANITIZED_FAKE_HASH")
        self.assertIn(REDACTED, out)
        self.assertNotIn("SANITIZED_FAKE_HASH", out)

    def test_nondefault_community_redacted(self):
        out = redact_line("snmp-server community S3cr3tStr RO")
        self.assertIn(REDACTED, out)
        self.assertNotIn("S3cr3tStr", out)


if __name__ == "__main__":
    unittest.main()

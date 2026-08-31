"""Smoke tests for the framework-agnostic core.

Runnable two ways:
    python -m unittest discover -s tests -v   # stdlib only, no third-party deps
    pytest                                     # on a full install (same tests)
"""
import unittest

from app.core.config import settings
from app.core.health import health_payload


class TestConfig(unittest.TestCase):
    def test_defaults_present(self):
        self.assertTrue(settings.app_name)
        self.assertEqual(settings.version, "0.1.0")
        self.assertGreater(settings.api_port, 0)
        self.assertTrue(0.0 < settings.similarity_threshold < 1.0)

    def test_cors_origins_parsed(self):
        self.assertIsInstance(settings.cors_origins, list)
        self.assertTrue(any("5173" in origin for origin in settings.cors_origins))


class TestHealth(unittest.TestCase):
    def test_health_payload_shape(self):
        payload = health_payload()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("version", payload)
        self.assertIn("timestamp", payload)
        self.assertTrue(payload["app"])


if __name__ == "__main__":
    unittest.main()

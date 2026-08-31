"""End-to-end pipeline tests (no persistence and with persistence)."""
import unittest

from app.services.audit_service import run_audit
from tests.support import read_sample


class TestPipelineReportShape(unittest.TestCase):
    def test_report_contains_all_sections(self):
        report = run_audit("rtr-edge-01.cfg", read_sample("cisco"))
        for key in ("filename", "vendor", "hostname", "summary",
                    "predicted_after", "findings", "model", "unknown_lines"):
            self.assertIn(key, report)
        self.assertEqual(report["vendor"], "cisco")
        self.assertEqual(len(report["findings"]), 14)

    def test_predicted_after_beats_before(self):
        report = run_audit("fgt-dc-03.conf", read_sample("fortinet"))
        self.assertGreater(report["predicted_after"]["score"], report["summary"]["score"])
        self.assertGreaterEqual(report["predicted_after"]["delta"], 0)

    def test_unknown_vendor_surfaces_training_lines(self):
        report = run_audit("other-device-01.cfg", read_sample("unknown"))
        self.assertEqual(report["vendor"], "unknown")
        self.assertEqual(len(report["unknown_lines"]), 7)

    def test_findings_are_json_serializable(self):
        import json
        report = run_audit("srx-br-02.conf", read_sample("juniper"))
        json.dumps(report)  # must not raise


if __name__ == "__main__":
    unittest.main()

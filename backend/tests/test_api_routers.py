"""Integration test suite for FastAPI routers."""
from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPIRouters(unittest.TestCase):
    def test_health_and_root(self):
        res_root = client.get("/")
        self.assertEqual(res_root.status_code, 200)

        res_health = client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")

    def test_audits_upload_text(self):
        cisco_cfg = """
        hostname rtr-edge-01
        line vty 0 4
         transport input telnet
        ip ssh version 2
        ip http server
        no logging
        """
        response = client.post(
            "/api/audits/text",
            json={"filename": "test-cisco.cfg", "config_text": cisco_cfg},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vendor"], "cisco")
        self.assertEqual(data["hostname"], "rtr-edge-01")
        self.assertIn("summary", data)
        self.assertIn("findings", data)
        self.assertIn("predicted_after", data)
        self.assertIn("audit_id", data)

        audit_id = data["audit_id"]

        # Fetch list audits
        res_list = client.get("/api/audits")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # Fetch get audit by id
        res_get = client.get(f"/api/audits/{audit_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], audit_id)

    def test_devices_and_findings(self):
        res_dev = client.get("/api/devices")
        self.assertEqual(res_dev.status_code, 200)

        res_find = client.get("/api/findings")
        self.assertEqual(res_find.status_code, 200)

    def test_training_and_tgr(self):
        # Classify unknown line
        res_class = client.post(
            "/api/training/classify",
            json={"line": "set xyz secure-admin-timeout 300", "vendor": "juniper"},
        )
        self.assertEqual(res_class.status_code, 200)

        # Teach exemplar
        res_teach = client.post(
            "/api/training/exemplars",
            json={
                "raw_text": "set xyz secure-admin-timeout 300",
                "category": "authentication",
                "parameter": "admin_session_timeout",
                "expected_value": "300",
                "control_id": "CIS-NET-18",
                "vendor": "juniper",
            },
        )
        self.assertEqual(res_teach.status_code, 200)
        ex_id = res_teach.json()["id"]

        # Approve exemplar
        res_app = client.post(f"/api/training/exemplars/{ex_id}/approve", json={"approved": True})
        self.assertEqual(res_app.status_code, 200)
        self.assertIn(res_app.json()["status"], ["ACTIVE", "APPROVED"])

        # TGR evaluation
        res_tgr = client.get("/api/training/tgr")
        self.assertEqual(res_tgr.status_code, 200)
        self.assertIn("tgr_percentage", res_tgr.json())

    def test_report_downloads(self):
        # Create an audit first
        audit_res = client.post(
            "/api/audits/text",
            json={"filename": "test-rpt.cfg", "config_text": "set system services ssh"},
        )
        audit_id = audit_res.json()["audit_id"]

        # PDF download
        res_pdf = client.get(f"/api/reports/pdf/{audit_id}")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.headers["content-type"], "application/pdf")

        # CSV download
        res_csv = client.get(f"/api/reports/csv/{audit_id}")
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn("text/csv", res_csv.headers["content-type"])

        # JSON download
        res_json = client.get(f"/api/reports/json/{audit_id}")
        self.assertEqual(res_json.status_code, 200)
        self.assertIn("application/json", res_json.headers["content-type"])


if __name__ == "__main__":
    unittest.main()

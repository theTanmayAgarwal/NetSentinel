"""Unit and integration tests for PART D - Audit -> Training Center Integration pipeline."""
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import app
from app.persistence.repository import Repository
from app.services.audit_service import run_audit

client = TestClient(app)


class TestAuditTrainingIntegration(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(db_path=":memory:")
        app.dependency_overrides[get_repo] = lambda: self.repo

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_d1_unknown_creates_pending(self):
        """TEST D1: Unknown configuration syntax produces PENDING learned_mapping record."""
        unknown_config = "set custom-firewall-rule 9000 disable"
        report = run_audit(filename="test_d1.cfg", config_text=unknown_config, repo=self.repo)

        # 1. Audit line remains in unknown_lines / UNMAPPED
        self.assertIn(unknown_config, report["unknown_lines"])

        # 2. A single PENDING mapping was created in database
        pending_mappings = self.repo.list_mappings(status="PENDING")
        matching = [m for m in pending_mappings if m["command_pattern"] == unknown_config]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "PENDING")

    def test_d2_pending_is_not_trusted(self):
        """TEST D2: PENDING mapping is NOT trusted for compliance PASS."""
        line = "set custom-ssh-port 2222"
        # Create PENDING mapping manually
        pending = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "ssh_port",
            "value": "2222",
            "status": "PENDING",
        })

        report = run_audit(filename="test_d2.cfg", config_text=line, repo=self.repo)

        # Line remains in unknown_lines and is NOT trusted for compliance pass
        self.assertIn(line, report["unknown_lines"])
        self.assertFalse(any(m["mapping_id"] == pending["id"] for m in report.get("reused_mappings", [])))

    def test_d3_active_mapping_is_reused(self):
        """TEST D3: ACTIVE mapping is reused and does not create duplicate mapping."""
        line = "set system services ssh"
        initial_count = len(self.repo.list_mappings())

        # An ACTIVE seed mapping exists for this command
        report = run_audit(filename="test_d3.cfg", config_text=line, repo=self.repo)

        final_count = len(self.repo.list_mappings())
        # No new mapping row was created
        self.assertEqual(final_count, initial_count)
        # ACTIVE mapping was reused
        self.assertTrue(len(report.get("reused_mappings", [])) >= 1)

    def test_d4_duplicate_audit_run(self):
        """TEST D4: Rerunning same audit with unknown syntax does NOT create duplicate PENDING rows."""
        unknown_config = "set custom-admin-timeout 500"

        # Run 1
        run_audit(filename="run1.cfg", config_text=unknown_config, repo=self.repo)
        count_after_run1 = len(self.repo.list_mappings())

        # Run 2
        run_audit(filename="run2.cfg", config_text=unknown_config, repo=self.repo)
        count_after_run2 = len(self.repo.list_mappings())

        self.assertEqual(count_after_run1, count_after_run2)

    def test_d5_rejected_is_not_trusted(self):
        """TEST D5: REJECTED mapping is NOT trusted."""
        line = "set dangerous-security-setting disable"
        rejected = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "dangerous_setting",
            "status": "REJECTED",
        })

        report = run_audit(filename="test_d5.cfg", config_text=line, repo=self.repo)

        self.assertIn(line, report["unknown_lines"])
        self.assertFalse(any(m["mapping_id"] == rejected["id"] for m in report.get("reused_mappings", [])))

    def test_d6_ai_failure_fallback(self):
        """TEST D6: AI proposal exception/failure is handled safely without crashing audit."""
        line = "set crash-test-timeout 1"

        with patch("app.training.service.TrainingService.ai_propose", side_effect=RuntimeError("AI Timeout")):
            report = run_audit(filename="test_d6.cfg", config_text=line, repo=self.repo)

        self.assertIsNotNone(report)
        self.assertIn(line, report["unknown_lines"])

    def test_d7_original_configuration_preserved(self):
        """TEST D7: Exact original configuration line remains available."""
        line = "set exact-line-preservation-timeout 99"
        report = run_audit(filename="test_d7.cfg", config_text=line, repo=self.repo)

        self.assertEqual(report["unknown_lines"], [line])
        pending = self.repo.list_mappings(status="PENDING")
        matching = [m for m in pending if m["command_pattern"] == line]
        self.assertEqual(len(matching), 1)

    def test_d8_training_center_visibility(self):
        """TEST D8: Newly created PENDING mapping is returned via GET /api/mappings?status=PENDING."""
        line = "set tc-visibility-timeout 123"
        run_audit(filename="test_d8.cfg", config_text=line, repo=self.repo)

        res = client.get("/api/mappings", params={"status": "PENDING"})
        self.assertEqual(res.status_code, 200)
        items = res.json()
        matching = [m for m in items if m["command_pattern"] == line]
        self.assertEqual(len(matching), 1)

    def test_d9_single_record_lifecycle(self):
        """TEST D9: Mapping ID created in Audit = mapping ID in Training Center = mapping ID in Knowledge Base."""
        line = "set single-id-lifecycle-timeout 888"
        report = run_audit(filename="test_d9.cfg", config_text=line, repo=self.repo)

        self.assertTrue(len(report["pending_proposals"]) >= 1)
        created_proposal = report["pending_proposals"][0]
        m_id = created_proposal["mapping_id"]

        # 1. Same ID returned by GET /api/mappings?status=PENDING (Training Center)
        tc_res = client.get("/api/mappings", params={"status": "PENDING"}).json()
        tc_match = [m for m in tc_res if m["id"] == m_id]
        self.assertEqual(len(tc_match), 1)

        # 2. Same ID returned by GET /api/mappings (Knowledge Base)
        kb_res = client.get("/api/mappings").json()
        kb_match = [m for m in kb_res if m["id"] == m_id]
        self.assertEqual(len(kb_match), 1)


if __name__ == "__main__":
    unittest.main()

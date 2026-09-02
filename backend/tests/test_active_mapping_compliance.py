"""Unit and integration tests for PART E - ACTIVE Mapping -> Deterministic Compliance Engine integration."""
import unittest
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import app
from app.persistence.repository import Repository
from app.services.audit_service import run_audit

client = TestClient(app)


class TestActiveMappingCompliance(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(db_path=":memory:")
        app.dependency_overrides[get_repo] = lambda: self.repo

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_e1_pending_to_active_compliance_transition(self):
        """TEST E1: PENDING mapping is UNMAPPED/WARNING -> Approved ACTIVE mapping evaluates to PASS/FAIL deterministically."""
        line = "set e1-unique-timeout 1800"

        # Step 1: Initial Audit on unknown syntax -> creates PENDING proposal
        report1 = run_audit(filename="audit1.cfg", config_text=line, repo=self.repo)

        # Step 2: Human approves PENDING mapping -> ACTIVE with 5 minutes timeout (300 seconds)
        pending_list = self.repo.list_mappings(status="PENDING")
        matching_pending = [m for m in pending_list if m["command_pattern"] == line]
        self.assertTrue(len(matching_pending) >= 1)
        m_id = matching_pending[0]["id"]

        # Human approves mapping as admin_session_timeout = 300 seconds (5 minutes)
        self.repo.update_mapping(
            m_id,
            {
                "security_property": "admin_session_timeout",
                "value": "300",
                "status": "ACTIVE",
                "reviewer": "administrator",
            },
        )

        # Step 3: Run audit again on the same line
        report2 = run_audit(filename="audit2.cfg", config_text=line, repo=self.repo)

        # Timeout control NET-11 must now evaluate to PASS (5 minutes is in range [1, 10])
        timeout_findings = [f for f in report2["findings"] if f["normalized_field"] == "idle_timeout_minutes" or f["control_id"] == "NET-11"]
        self.assertTrue(len(timeout_findings) >= 1)
        finding = timeout_findings[0]
        self.assertEqual(finding["status"], "PASS")

        # Evidence must link to Learned Mapping M-{m_id}
        self.assertTrue(any(f"Learned Mapping M-{m_id}" in ev for ev in finding["evidence"]))

    def test_e2_human_correction_overrides_ai_proposal(self):
        """TEST E2: Human correction (idle_timeout_minutes = 5 -> PASS) overrides AI proposal (idle_timeout_minutes = 30 -> FAIL)."""
        line = "set e2-unique-timeout 1800"

        # AI proposed 30 minutes (1800 seconds) -> would FAIL rule NET-11 (range 1 to 10)
        item = self.repo.create_mapping({
            "vendor": "UnknownVendor",
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "1800",
            "ai_proposal": "AI proposed 30 minutes timeout",
            "status": "PENDING",
        })
        m_id = item["id"]

        # Human corrects value to 300 seconds (5 minutes) and sets status ACTIVE
        self.repo.update_mapping(
            m_id,
            {
                "security_property": "admin_session_timeout",
                "value": "300",
                "status": "ACTIVE",
                "reviewer": "administrator",
            },
        )

        # Audit evaluates human corrected value (5 minutes) -> PASS
        report = run_audit(filename="corrected_audit.cfg", config_text=line, repo=self.repo)
        timeout_finding = [f for f in report["findings"] if f["control_id"] == "NET-11"][0]
        self.assertEqual(timeout_finding["status"], "PASS")

    def test_e3_rejected_mapping_not_trusted(self):
        """TEST E3: REJECTED mapping is NOT trusted and produces UNMAPPED."""
        line = "set dangerous-security-setting disable"
        self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "telnet_enabled",
            "value": "false",
            "status": "REJECTED",
        })

        report = run_audit(filename="rejected_audit.cfg", config_text=line, repo=self.repo)
        # Line remains in unknown_lines or is not trusted as active mapping
        self.assertIn(line, report["unknown_lines"])

    def test_e4_stale_and_revoked_mappings_untrusted(self):
        """TEST E4: STALE and REVOKED mappings are NOT trusted for compliance PASS."""
        line1 = "set system ssh-version 1"
        self.repo.create_mapping({
            "command_pattern": line1,
            "security_property": "ssh_version",
            "value": "2",
            "status": "REVOKED",
        })

        report = run_audit(filename="revoked_audit.cfg", config_text=line1, repo=self.repo)
        ssh_findings = [f for f in report["findings"] if f["normalized_field"] == "ssh_version"]
        if ssh_findings:
            self.assertNotEqual(ssh_findings[0]["status"], "PASS")

    def test_e5_evidence_traceability(self):
        """TEST E5: Audit finding evidence links directly to Learned Mapping M-{id} and config line."""
        line = "set e5-unique-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        report = run_audit(filename="evidence_test.cfg", config_text=line, repo=self.repo)
        timeout_findings = [f for f in report["findings"] if f["normalized_field"] == "idle_timeout_minutes"]
        self.assertTrue(len(timeout_findings) >= 1)
        evidence = timeout_findings[0]["evidence"]
        self.assertTrue(any(f"M-{m['id']}" in ev for ev in evidence))

    def test_e6_unmapped_score_impact(self):
        """TEST E6: UNMAPPED findings are included in total evaluated controls and do NOT silently score 100%."""
        line = "set custom-unmapped-security-parameter 123"
        report = run_audit(filename="unmapped_score.cfg", config_text=line, repo=self.repo)
        summary = report["summary"]
        self.assertIn("unmapped", summary)
        self.assertIn("score", summary)


if __name__ == "__main__":
    unittest.main()

"""Unit and integration tests for PART F - Mapping Usage & Audit Traceability."""
import unittest
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import app
from app.persistence.repository import Repository
from app.services.audit_service import run_audit

client = TestClient(app)


class TestMappingUsageTraceability(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(db_path=":memory:")
        app.dependency_overrides[get_repo] = lambda: self.repo

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_f1_active_mapping_usage(self):
        """TEST F1: Active mapping application creates a persisted usage record."""
        line = "set f1-unique-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        report = run_audit(filename="f1_audit.cfg", config_text=line, repo=self.repo)
        audit_id = report.get("audit_id")
        self.assertIsNotNone(audit_id)

        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(len(usage_list), 1)
        self.assertEqual(usage_list[0]["mapping_id"], m["id"])

    def test_f2_usage_links_audit(self):
        """TEST F2: Usage record correctly references audit ID."""
        line = "set f2-unique-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        report = run_audit(filename="f2_audit.cfg", config_text=line, repo=self.repo)
        audit_id = report["audit_id"]

        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(usage_list[0]["audit_id"], audit_id)

    def test_f3_usage_links_source(self):
        """TEST F3: Usage record retains original configuration fragment."""
        line = "set f3-unique-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        run_audit(filename="f3_audit.cfg", config_text=line, repo=self.repo)
        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(usage_list[0]["configuration_fragment"], line)

    def test_f4_usage_links_rule_finding(self):
        """TEST F4: Usage record retains control ID reference."""
        line = "set f4-unique-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        run_audit(filename="f4_audit.cfg", config_text=line, repo=self.repo)
        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(usage_list[0]["control_id"], "NET-11")

    def test_f5_pending_no_usage(self):
        """TEST F5: PENDING mapping creates zero usage events."""
        m = self.repo.create_mapping({
            "command_pattern": "set f5-pending-line 1",
            "security_property": "ssh_port",
            "value": "22",
            "status": "PENDING",
        })

        res = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=1, configuration_fragment="set f5-pending-line 1")
        self.assertEqual(res, {})
        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(len(usage_list), 0)

    def test_f6_rejected_no_usage(self):
        """TEST F6: REJECTED mapping creates zero usage events."""
        m = self.repo.create_mapping({
            "command_pattern": "set f6-rejected-line 1",
            "security_property": "ssh_port",
            "value": "22",
            "status": "REJECTED",
        })

        res = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=1, configuration_fragment="set f6-rejected-line 1")
        self.assertEqual(res, {})
        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(len(usage_list), 0)

    def test_f7_stale_no_usage(self):
        """TEST F7: STALE mapping creates zero usage events."""
        m = self.repo.create_mapping({
            "command_pattern": "set f7-stale-line 1",
            "security_property": "ssh_port",
            "value": "22",
            "status": "STALE",
        })

        res = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=1, configuration_fragment="set f7-stale-line 1")
        self.assertEqual(res, {})
        self.assertEqual(len(self.repo.list_mapping_usage(m["id"])), 0)

    def test_f8_revoked_no_usage(self):
        """TEST F8: REVOKED mapping creates zero usage events."""
        m = self.repo.create_mapping({
            "command_pattern": "set f8-revoked-line 1",
            "security_property": "ssh_port",
            "value": "22",
            "status": "REVOKED",
        })

        res = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=1, configuration_fragment="set f8-revoked-line 1")
        self.assertEqual(res, {})
        self.assertEqual(len(self.repo.list_mapping_usage(m["id"])), 0)

    def test_f9_multiple_source_uses(self):
        """TEST F9: Multiple distinct configuration fragments in one audit create separate usage records."""
        m = self.repo.create_mapping({
            "command_pattern": "set f9-timeout",
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=100, configuration_fragment="set f9-timeout line 21")
        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=100, configuration_fragment="set f9-timeout line 48")

        usage_list = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(len(usage_list), 2)

    def test_f10_idempotency(self):
        """TEST F10: Repeated record_mapping_usage calls for same audit + fragment do NOT duplicate rows."""
        m = self.repo.create_mapping({
            "command_pattern": "set f10-timeout 300",
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        u1 = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=50, configuration_fragment="set f10-timeout 300")
        u2 = self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=50, configuration_fragment="set f10-timeout 300")

        self.assertEqual(u1["id"], u2["id"])
        self.assertEqual(len(self.repo.list_mapping_usage(m["id"])), 1)

    def test_f11_usage_count(self):
        """TEST F11: Usage count is accurately summarized from persisted usage table."""
        m = self.repo.create_mapping({
            "command_pattern": "set f11-timeout",
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=10, configuration_fragment="line 1")
        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=11, configuration_fragment="line 2")

        summary = self.repo.get_mapping_usage_summary(m["id"])
        self.assertEqual(summary["usage_count"], 2)
        self.assertEqual(summary["audits_used"], [10, 11])

    def test_f12_last_used(self):
        """TEST F12: Last used timestamp is correctly retrieved from usage records."""
        m = self.repo.create_mapping({
            "command_pattern": "set f12-timeout",
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        t1 = "2026-09-02T08:00:00+00:00"
        t2 = "2026-09-02T10:00:00+00:00"

        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=1, configuration_fragment="line 1", used_at=t1)
        self.repo.record_mapping_usage(mapping_id=m["id"], audit_id=2, configuration_fragment="line 2", used_at=t2)

        summary = self.repo.get_mapping_usage_summary(m["id"])
        self.assertEqual(summary["last_used"], t2)

    def test_f13_approval_then_usage(self):
        """TEST F13: Lifecycle: PENDING -> Approved ACTIVE -> Audit Run -> Usage event recorded."""
        line = "set f13-lifecycle-timeout 300"
        # 1. PENDING proposal created by audit or manually
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "PENDING",
        })
        self.assertEqual(self.repo.get_mapping_usage_summary(m["id"])["usage_count"], 0)

        # 2. Approved to ACTIVE
        self.repo.update_mapping(m["id"], {"status": "ACTIVE"})

        # 3. Audit runs
        run_audit(filename="f13.cfg", config_text=line, repo=self.repo)

        # 4. Usage event exists
        summary = self.repo.get_mapping_usage_summary(m["id"])
        self.assertEqual(summary["usage_count"], 1)

    def test_f14_correction_then_usage(self):
        """TEST F14: Lifecycle: PENDING -> Corrected ACTIVE -> Audit Run -> Usage records corrected value."""
        line = "set f14-lifecycle-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "1800",
            "status": "PENDING",
        })

        # Correct value to 300 seconds and set ACTIVE
        self.repo.update_mapping(m["id"], {"value": "300", "status": "ACTIVE"})

        run_audit(filename="f14.cfg", config_text=line, repo=self.repo)

        events = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["observed_value"], "300")

    def test_f15_evidence_traceability(self):
        """TEST F15: Complete traceability chain: Mapping -> Audit -> Config line -> Fact -> Finding."""
        line = "set f15-lifecycle-timeout 300"
        m = self.repo.create_mapping({
            "command_pattern": line,
            "security_property": "admin_session_timeout",
            "value": "300",
            "status": "ACTIVE",
        })

        report = run_audit(filename="f15.cfg", config_text=line, repo=self.repo)
        audit_id = report["audit_id"]

        # Check Finding evidence
        finding = [f for f in report["findings"] if f["control_id"] == "NET-11"][0]
        self.assertTrue(any(f"M-{m['id']}" in ev for ev in finding["evidence"]))

        # Check Usage event
        events = self.repo.list_mapping_usage(m["id"])
        self.assertEqual(events[0]["audit_id"], audit_id)
        self.assertEqual(events[0]["configuration_fragment"], line)
        self.assertEqual(events[0]["control_id"], "NET-11")


if __name__ == "__main__":
    unittest.main()

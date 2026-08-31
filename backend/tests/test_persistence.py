"""Persistence + audit-log integrity tests (in-memory SQLite)."""
import unittest

from app.persistence.repository import Repository
from app.services.audit_service import run_audit
from tests.support import read_sample


class TestRepositoryRoundTrip(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(":memory:")

    def tearDown(self):
        self.repo.close()

    def test_save_and_get_audit(self):
        report = run_audit("rtr-edge-01.cfg", read_sample("cisco"), repo=self.repo)
        aid = report["audit_id"]
        fetched = self.repo.get_audit(aid)
        self.assertEqual(fetched["hostname"], "RTR-EDGE-01")
        self.assertEqual(fetched["vendor"], "cisco")
        self.assertEqual(len(fetched["findings"]), 14)

    def test_device_dedup(self):
        run_audit("a.cfg", read_sample("cisco"), repo=self.repo)
        run_audit("b.cfg", read_sample("cisco"), repo=self.repo)
        # same hostname+vendor => one device row, two audits
        devices = self.repo._conn.execute("SELECT COUNT(*) c FROM devices").fetchone()["c"]
        self.assertEqual(devices, 1)
        self.assertEqual(len(self.repo.list_audits()), 2)

    def test_list_audits_desc(self):
        run_audit("a.cfg", read_sample("cisco"), repo=self.repo)
        run_audit("b.cfg", read_sample("juniper"), repo=self.repo)
        audits = self.repo.list_audits()
        self.assertEqual(audits[0]["id"], 2)  # newest first


class TestExemplarStore(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(":memory:")

    def tearDown(self):
        self.repo.close()

    def test_add_and_update_status(self):
        eid = self.repo.add_exemplar({
            "text": "management telnet server enabled",
            "category": "Secure Management",
            "parameter": "telnet_enabled",
            "expected_value": "false",
            "control_id": "NET-01",
            "vendor": "unknown",
            "embedding": [0.1, 0.2, 0.3],
            "created_by": "trainer",
            "status": "PENDING",
        })
        self.assertEqual(len(self.repo.list_exemplars(status="PENDING")), 1)
        self.repo.update_exemplar_status(eid, "APPROVED", True)
        self.assertEqual(len(self.repo.list_exemplars(status="PENDING")), 0)
        self.assertEqual(len(self.repo.list_exemplars(status="APPROVED")), 1)
        self.assertEqual(self.repo.list_exemplars()[0]["embedding"], [0.1, 0.2, 0.3])


class TestAuditLogChain(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(":memory:")

    def tearDown(self):
        self.repo.close()

    def test_chain_intact_then_tamper_detected(self):
        run_audit("a.cfg", read_sample("cisco"), actor="demo", repo=self.repo)
        run_audit("b.cfg", read_sample("juniper"), actor="demo", repo=self.repo)
        self.assertEqual(len(self.repo.get_log()), 2)
        self.assertTrue(self.repo.verify_log())
        self.repo._conn.execute("UPDATE audit_log SET detail_json='{}' WHERE id=1")
        self.repo._conn.commit()
        self.assertFalse(self.repo.verify_log())


if __name__ == "__main__":
    unittest.main()

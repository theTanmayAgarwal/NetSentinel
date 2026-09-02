"""Unit and integration tests for PART A & PART B - learned_mappings database and Human-in-the-Loop Training Center workflow."""
import tempfile
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.repository import Repository

client = TestClient(app)


class TestLearnedMappings(unittest.TestCase):
    def setUp(self):
        # Use isolated in-memory repository for fast unit testing
        self.repo = Repository(db_path=":memory:")

    def test_create_and_retrieve_mapping(self):
        mapping_data = {
            "vendor": "juniper",
            "os_version": "21.4",
            "command_pattern": "set system services telnet disable",
            "security_property": "telnet_enabled",
            "value": "false",
            "unit": "",
            "category": "Secure Management",
            "control_id": "CIS-NET-02",
            "ai_confidence": 0.95,
            "ai_proposal": "Disable insecure telnet protocol",
            "status": "PENDING",
            "version": 1,
            "reviewer": "administrator",
        }
        created = self.repo.create_mapping(mapping_data)
        self.assertIsNotNone(created["id"])
        self.assertEqual(created["status"], "PENDING")
        self.assertEqual(created["version"], 1)

        fetched = self.repo.get_mapping(created["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["command_pattern"], "set system services telnet disable")
        self.assertEqual(fetched["security_property"], "telnet_enabled")

    def test_update_mapping_and_status_change(self):
        created = self.repo.create_mapping({
            "command_pattern": "set secure-management port 8443",
            "security_property": "admin_port",
            "value": "8443",
            "status": "PENDING",
        })
        m_id = created["id"]

        # Update status to ACTIVE
        updated = self.repo.change_mapping_status(m_id, "ACTIVE", reviewer="security_admin")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "ACTIVE")
        self.assertEqual(updated["reviewer"], "security_admin")
        self.assertIsNotNone(updated.get("reviewed_at"))

        # Update value and bump version
        updated_val = self.repo.update_mapping(m_id, {"value": "9443", "version": 2})
        self.assertEqual(updated_val["value"], "9443")
        self.assertEqual(updated_val["version"], 2)

    def test_invalid_status_raises_error(self):
        created = self.repo.create_mapping({
            "command_pattern": "test pattern",
            "security_property": "test_prop",
        })
        with self.assertRaises(ValueError):
            self.repo.change_mapping_status(created["id"], "INVALID_STATUS")

    def test_part_b_approve_workflow(self):
        # 1. Create PENDING mapping
        pending = self.repo.create_mapping({
            "vendor": "UnknownVendor",
            "os_version": "5.2",
            "command_pattern": "set xyz secure-admin-timeout 300",
            "security_property": "admin_session_timeout",
            "value": "300",
            "unit": "seconds",
            "category": "Secure Management",
            "control_id": "CIS-NET-18",
            "ai_confidence": 0.92,
            "ai_proposal": "Detected session timeout from syntax.",
            "status": "PENDING",
            "version": 1,
            "reviewer": "administrator",
        })
        m_id = pending["id"]

        # Verify PENDING list includes mapping
        pending_list = self.repo.list_mappings(status="PENDING")
        self.assertTrue(any(m["id"] == m_id for m in pending_list))

        # 2. Approve mapping: PENDING -> ACTIVE
        approved = self.repo.change_mapping_status(m_id, "ACTIVE", reviewer="admin_user")
        self.assertEqual(approved["status"], "ACTIVE")
        self.assertEqual(approved["reviewer"], "admin_user")
        self.assertIsNotNone(approved.get("reviewed_at"))

        # Verify no longer returned under PENDING
        pending_after = self.repo.list_mappings(status="PENDING")
        self.assertFalse(any(m["id"] == m_id for m in pending_after))

        # Verify returned under ACTIVE
        active_list = self.repo.list_mappings(status="ACTIVE")
        self.assertTrue(any(m["id"] == m_id for m in active_list))

    def test_part_b_correct_workflow(self):
        # 1. Create PENDING mapping with initial AI proposal
        pending = self.repo.create_mapping({
            "vendor": "UnknownVendor",
            "os_version": "5.2",
            "command_pattern": "set xyz secure-admin-timeout 300",
            "security_property": "wrong_property",
            "value": "100",
            "unit": "ms",
            "ai_proposal": "Original AI proposal text",
            "status": "PENDING",
        })
        m_id = pending["id"]

        # 2. Administrator corrects fields and approves (PENDING -> ACTIVE)
        corrected = self.repo.update_mapping(
            m_id,
            {
                "security_property": "admin_session_timeout",
                "value": "300",
                "unit": "seconds",
                "status": "ACTIVE",
                "reviewer": "administrator",
            },
        )
        self.assertEqual(corrected["security_property"], "admin_session_timeout")
        self.assertEqual(corrected["value"], "300")
        self.assertEqual(corrected["unit"], "seconds")
        self.assertEqual(corrected["status"], "ACTIVE")
        # Ensure original AI proposal was preserved for auditability
        self.assertEqual(corrected["ai_proposal"], "Original AI proposal text")

    def test_part_b_reject_workflow(self):
        # 1. Create PENDING mapping
        pending = self.repo.create_mapping({
            "command_pattern": "set bad-syntax 999",
            "security_property": "unknown_prop",
            "status": "PENDING",
        })
        m_id = pending["id"]

        # 2. Reject mapping (PENDING -> REJECTED)
        rejected = self.repo.change_mapping_status(m_id, "REJECTED", reviewer="administrator")
        self.assertEqual(rejected["status"], "REJECTED")

        # 3. Verify record remains in DB (not deleted)
        fetched = self.repo.get_mapping(m_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "REJECTED")

        # 4. Verify NOT returned in ACTIVE trusted mappings list
        active_list = self.repo.list_mappings(status="ACTIVE")
        self.assertFalse(any(m["id"] == m_id for m in active_list))

    def test_part_b_persistence_across_restart(self):
        # Create temp file DB for restart test
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        repo1 = Repository(db_path=tmp_path)
        item = repo1.create_mapping({
            "command_pattern": "set persistent-test 1",
            "security_property": "test_persistent",
            "value": "1",
            "status": "PENDING",
        })
        m_id = item["id"]
        repo1.change_mapping_status(m_id, "ACTIVE", reviewer="restart_tester")
        repo1.close()

        # Re-open database instance (simulating backend restart)
        repo2 = Repository(db_path=tmp_path)
        restarted_item = repo2.get_mapping(m_id)
        self.assertIsNotNone(restarted_item)
        self.assertEqual(restarted_item["status"], "ACTIVE")
        self.assertEqual(restarted_item["reviewer"], "restart_tester")
        repo2.close()

    def test_api_crud_endpoints(self):
        # 1. GET /api/mappings
        res_list = client.get("/api/mappings")
        self.assertEqual(res_list.status_code, 200)
        self.assertIsInstance(res_list.json(), list)

        # 2. POST /api/mappings
        new_payload = {
            "vendor": "fortinet",
            "os_version": "7.2",
            "command_pattern": "set admin-sport 443",
            "security_property": "admin_https_port",
            "value": "443",
            "unit": "",
            "category": "Management",
            "control_id": "CIS-NET-05",
            "ai_confidence": 0.99,
            "status": "ACTIVE",
            "version": 1,
            "reviewer": "admin",
        }
        res_create = client.post("/api/mappings", json=new_payload)
        self.assertEqual(res_create.status_code, 201)
        created_data = res_create.json()
        m_id = created_data["id"]

        # 3. GET /api/mappings/{id}
        res_get = client.get(f"/api/mappings/{m_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["command_pattern"], "set admin-sport 443")

        # 4. PATCH /api/mappings/{id}
        res_patch = client.patch(f"/api/mappings/{m_id}", json={"status": "REVOKED"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["status"], "REVOKED")

        # 5. GET 404 for non-existent mapping
        res_404 = client.get("/api/mappings/999999")
        self.assertEqual(res_404.status_code, 404)

        # 6. POST invalid status 400
        res_bad = client.post("/api/mappings", json={
            "command_pattern": "bad",
            "security_property": "bad",
            "status": "NOT_A_STATUS"
        })
        self.assertEqual(res_bad.status_code, 400)


if __name__ == "__main__":
    unittest.main()

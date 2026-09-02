"""Unit and integration tests for PART C - Training Center ↔ Knowledge Base shared data integration."""
import unittest
from fastapi.testclient import TestClient

from app.api.deps import get_repo
from app.main import app
from app.persistence.repository import Repository

client = TestClient(app)


class TestKnowledgeBaseIntegration(unittest.TestCase):
    def setUp(self):
        # Use isolated in-memory repository for test assertions
        self.repo = Repository(db_path=":memory:")
        app.dependency_overrides[get_repo] = lambda: self.repo

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_c1_pending_mapping_shared(self):
        """TEST 1: Create PENDING mapping in Training Center, verify Knowledge Base receives the exact same mapping."""
        pending_data = {
            "vendor": "UnknownVendor",
            "os_version": "5.2",
            "command_pattern": "set xyz secure-admin-timeout 300",
            "security_property": "admin_session_timeout",
            "value": "300",
            "unit": "seconds",
            "category": "Secure Management",
            "control_id": "CIS-NET-18",
            "ai_confidence": 0.92,
            "ai_proposal": "Detected administrative session timeout setting",
            "status": "PENDING",
            "version": 1,
            "reviewer": "administrator",
        }
        created = self.repo.create_mapping(pending_data)
        m_id = created["id"]

        # Knowledge Base queries GET /api/mappings
        res = client.get("/api/mappings")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        matching = [item for item in items if item["id"] == m_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "PENDING")
        self.assertEqual(matching[0]["command_pattern"], "set xyz secure-admin-timeout 300")

    def test_c2_approve_reflects_in_knowledge_base(self):
        """TEST 2: Change mapping PENDING -> ACTIVE in Training Center, verify Knowledge Base returns ACTIVE."""
        created = self.repo.create_mapping({
            "command_pattern": "set admin-timeout 600",
            "security_property": "admin_session_timeout",
            "value": "600",
            "status": "PENDING",
        })
        m_id = created["id"]

        # Approve mapping
        self.repo.change_mapping_status(m_id, "ACTIVE", reviewer="administrator")

        # Knowledge Base query
        fetched = self.repo.get_mapping(m_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "ACTIVE")
        self.assertEqual(fetched["reviewer"], "administrator")

        # API query
        res = client.get(f"/api/mappings/{m_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ACTIVE")

    def test_c3_reject_reflects_in_knowledge_base(self):
        """TEST 3: Change mapping PENDING -> REJECTED in Training Center, verify Knowledge Base returns REJECTED."""
        created = self.repo.create_mapping({
            "command_pattern": "set bad-syntax 999",
            "security_property": "unknown_prop",
            "status": "PENDING",
        })
        m_id = created["id"]

        # Reject mapping
        self.repo.change_mapping_status(m_id, "REJECTED", reviewer="administrator")

        # Knowledge Base query
        fetched = self.repo.get_mapping(m_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "REJECTED")

        # API query with status filter
        res_rejected = client.get("/api/mappings", params={"status": "REJECTED"})
        self.assertEqual(res_rejected.status_code, 200)
        rejected_ids = [item["id"] for item in res_rejected.json()]
        self.assertIn(m_id, rejected_ids)

    def test_c4_correct_mapping_fields_reflect(self):
        """TEST 4: Correct mapping fields in Training Center, verify Knowledge Base returns corrected values."""
        created = self.repo.create_mapping({
            "command_pattern": "set xyz secure-admin-timeout 300",
            "security_property": "wrong_prop",
            "value": "100",
            "unit": "ms",
            "ai_proposal": "Original AI proposal text",
            "status": "PENDING",
        })
        m_id = created["id"]

        # Correct fields
        self.repo.update_mapping(
            m_id,
            {
                "security_property": "admin_session_timeout",
                "value": "300",
                "unit": "seconds",
                "status": "ACTIVE",
                "reviewer": "administrator",
            },
        )

        # Knowledge Base query
        fetched = self.repo.get_mapping(m_id)
        self.assertEqual(fetched["security_property"], "admin_session_timeout")
        self.assertEqual(fetched["value"], "300")
        self.assertEqual(fetched["unit"], "seconds")
        self.assertEqual(fetched["status"], "ACTIVE")
        # Ensure original AI proposal text preserved
        self.assertEqual(fetched["ai_proposal"], "Original AI proposal text")

    def test_c5_no_duplicate_rows_on_status_change(self):
        """TEST 5: Ensure no duplicate database rows are created when status changes."""
        initial_count = len(self.repo.list_mappings())
        created = self.repo.create_mapping({
            "command_pattern": "test dup pattern",
            "security_property": "test_prop",
            "status": "PENDING",
        })
        m_id = created["id"]

        count_after_create = len(self.repo.list_mappings())
        self.assertEqual(count_after_create, initial_count + 1)

        # Transition status 3 times
        self.repo.change_mapping_status(m_id, "ACTIVE")
        self.repo.change_mapping_status(m_id, "STALE")
        self.repo.change_mapping_status(m_id, "ACTIVE")

        count_after_transitions = len(self.repo.list_mappings())
        self.assertEqual(count_after_transitions, initial_count + 1)

    def test_c6_single_mapping_id_throughout_lifecycle(self):
        """TEST 6: Ensure the same mapping ID (M-{id}) is preserved throughout its lifecycle."""
        created = self.repo.create_mapping({
            "command_pattern": "set lifecycle test 1",
            "security_property": "lifecycle_prop",
            "status": "PENDING",
        })
        m_id = created["id"]

        item_pending = self.repo.get_mapping(m_id)
        self.assertEqual(item_pending["id"], m_id)

        self.repo.change_mapping_status(m_id, "ACTIVE")
        item_active = self.repo.get_mapping(m_id)
        self.assertEqual(item_active["id"], m_id)

        self.repo.change_mapping_status(m_id, "REVOKED")
        item_revoked = self.repo.get_mapping(m_id)
        self.assertEqual(item_revoked["id"], m_id)


if __name__ == "__main__":
    unittest.main()

"""Training Service for Unknown Command Learning & Adaptive Security Memory."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.embeddings.embedder import get_embedding
from app.embeddings.store import VectorStore
from app.persistence.repository import Repository


class TrainingService:
    def __init__(self, repo: Repository, confidence_threshold: float = 0.80) -> None:
        self.repo = repo
        self.vector_store = VectorStore(confidence_threshold=confidence_threshold)

    def classify_unknown_line(self, line: str, vendor: Optional[str] = None) -> Dict[str, Any]:
        """Classify unknown configuration line against active learned mappings."""
        active_mappings = self.repo.list_exemplars(status="ACTIVE")
        # Also include legacy APPROVED status for backward compatibility
        approved_mappings = self.repo.list_exemplars(status="APPROVED")
        candidate_pool = active_mappings + [m for m in approved_mappings if m not in active_mappings]

        if vendor:
            candidate_pool = [
                ex for ex in candidate_pool if not ex.get("vendor") or ex.get("vendor") == vendor
            ]

        res = self.vector_store.classify_command(line, candidate_pool)
        res["source_line"] = line
        res["vendor"] = vendor
        return res

    def ai_propose(
        self,
        line: str,
        context: Optional[str] = None,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
        os_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured AI proposal for unknown command fragment."""
        text = line.strip()

        # Deterministic semantic inference engine for unknown command syntax
        if re.search(r"secure-admin-timeout|admin-timeout|session-timeout|idle-timeout", text, re.I):
            m = re.search(r"(\d+)", text)
            val = int(m.group(1)) if m else 300
            return {
                "property": "admin_session_timeout",
                "value": val,
                "unit": "seconds",
                "confidence": 0.92,
                "reason": "Detected administrative session timeout setting from command syntax",
                "pattern": text,
            }
        elif re.search(r"ssh-version|ssh\s+version", text, re.I):
            m = re.search(r"(\d+)", text)
            val = int(m.group(1)) if m else 2
            return {
                "property": "ssh_version",
                "value": val,
                "unit": None,
                "confidence": 0.95,
                "reason": "Detected SSH version protocol restriction",
                "pattern": text,
            }
        elif re.search(r"telnet", text, re.I):
            val = False if re.search(r"disabled|no|off", text, re.I) else True
            return {
                "property": "telnet_enabled",
                "value": val,
                "unit": None,
                "confidence": 0.90,
                "reason": "Detected Telnet management service state",
                "pattern": text,
            }
        elif re.search(r"password.*length|pwd.*length", text, re.I):
            m = re.search(r"(\d+)", text)
            val = int(m.group(1)) if m else 10
            return {
                "property": "password_min_length",
                "value": val,
                "unit": "characters",
                "confidence": 0.88,
                "reason": "Detected password minimum length requirement",
                "pattern": text,
            }
        else:
            return {
                "property": "custom_security_setting",
                "value": text,
                "unit": None,
                "confidence": 0.70,
                "reason": "Generic security-relevant command fragment detected",
                "pattern": text,
            }

    def teach_exemplar(
        self,
        raw_text: str,
        category: str,
        parameter: str,
        expected_value: str,
        control_id: Optional[str] = None,
        vendor: Optional[str] = None,
        platform: Optional[str] = None,
        os_version: Optional[str] = None,
        actor: str = "administrator",
    ) -> Dict[str, Any]:
        """Record an administrator-taught exemplar / active mapping."""
        embedding = get_embedding(raw_text)

        exemplar_data = {
            "text": raw_text.strip(),
            "category": category,
            "parameter": parameter,
            "security_property": parameter,
            "expected_value": expected_value,
            "value": expected_value,
            "control_id": control_id,
            "vendor": vendor,
            "platform": platform,
            "os_version": os_version,
            "embedding": embedding,
            "created_by": actor,
            "reviewer": actor,
            "version": 1,
            "approved": True,
            "status": "ACTIVE",
            "confidence": 1.0,
        }

        exemplar_id = self.repo.add_exemplar(exemplar_data)
        exemplar_data["id"] = exemplar_id

        self.repo.append_log(
            actor=actor,
            action="teach_exemplar",
            entity="mapping",
            entity_id=str(exemplar_id),
            detail={
                "text": raw_text,
                "category": category,
                "parameter": parameter,
                "expected_value": expected_value,
                "control_id": control_id,
                "vendor": vendor,
                "status": "ACTIVE",
            },
        )

        return exemplar_data

    def list_exemplars(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repo.list_exemplars(status=status)

    def approve_exemplar(self, exemplar_id: int, approved: bool = True, actor: str = "administrator") -> None:
        status = "ACTIVE" if approved else "REJECTED"
        self.repo.update_exemplar_status(exemplar_id, status=status, approved=approved, reviewer=actor)
        self.repo.append_log(
            actor=actor,
            action="approve_mapping" if approved else "reject_mapping",
            entity="mapping",
            entity_id=str(exemplar_id),
            detail={"status": status, "approved": approved},
        )

    def correct_mapping(self, exemplar_id: int, updates: Dict[str, Any], actor: str = "administrator") -> None:
        updates["status"] = "ACTIVE"
        updates["approved"] = 1
        self.repo.update_exemplar(exemplar_id, updates, reviewer=actor)
        self.repo.append_log(
            actor=actor,
            action="correct_mapping",
            entity="mapping",
            entity_id=str(exemplar_id),
            detail=updates,
        )

    def revalidate_mapping(self, exemplar_id: int, actor: str = "administrator") -> None:
        self.repo.revalidate_exemplar(exemplar_id, reviewer=actor)
        self.repo.append_log(
            actor=actor,
            action="revalidate_mapping",
            entity="mapping",
            entity_id=str(exemplar_id),
            detail={"status": "ACTIVE"},
        )

    def revoke_mapping(self, exemplar_id: int, actor: str = "administrator") -> None:
        self.repo.revoke_exemplar(exemplar_id, reviewer=actor)
        self.repo.append_log(
            actor=actor,
            action="revoke_mapping",
            entity="mapping",
            entity_id=str(exemplar_id),
            detail={"status": "REVOKED"},
        )


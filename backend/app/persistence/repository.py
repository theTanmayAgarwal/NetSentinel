"""SQLite persistence via a stdlib ``sqlite3`` repository.

Deliberately NOT an ORM: a thin, explicit repository keeps the whole core
verifiable offline (no SQLAlchemy dependency) while presenting a clean interface
that could be swapped for Postgres later. Supports an in-memory database
(``:memory:``) for fast, isolated tests.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_DDL = """
CREATE TABLE IF NOT EXISTS devices (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname  TEXT,
    vendor    TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(hostname, vendor)
);

CREATE TABLE IF NOT EXISTS audits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id     INTEGER REFERENCES devices(id),
    filename      TEXT,
    vendor        TEXT,
    hostname      TEXT,
    score         REAL,
    passed        INTEGER,
    failed        INTEGER,
    warnings      INTEGER,
    critical      INTEGER,
    predicted_after_score REAL,
    created_at    TEXT NOT NULL,
    summary_json  TEXT,
    model_json    TEXT,
    unknown_json  TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id       INTEGER NOT NULL REFERENCES audits(id),
    control_id     TEXT,
    title          TEXT,
    category       TEXT,
    framework      TEXT,
    status         TEXT,
    severity       TEXT,
    observed       TEXT,
    expected       TEXT,
    rationale      TEXT,
    explanation    TEXT,
    evidence_json  TEXT,
    remediation_json TEXT
);

CREATE TABLE IF NOT EXISTS exemplars (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    text         TEXT NOT NULL,
    category     TEXT,
    parameter    TEXT,
    expected_value TEXT,
    control_id   TEXT,
    vendor       TEXT,
    embedding_json TEXT,
    created_by   TEXT,
    created_at   TEXT NOT NULL,
    version      INTEGER DEFAULT 1,
    approved     INTEGER DEFAULT 0,
    status       TEXT DEFAULT 'PENDING',
    confidence   REAL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    actor      TEXT,
    action     TEXT,
    entity     TEXT,
    entity_id  TEXT,
    detail_json TEXT,
    prev_hash  TEXT,
    hash       TEXT
);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()

    def close(self) -> None:
        self._conn.close()

    def init_schema(self) -> None:
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------ devices
    def upsert_device(self, hostname: Optional[str], vendor: str) -> int:
        cur = self._conn.execute(
            "SELECT id FROM devices WHERE hostname IS ? AND vendor = ?",
            (hostname, vendor),
        )
        row = cur.fetchone()
        if row:
            return int(row["id"])
        cur = self._conn.execute(
            "INSERT INTO devices (hostname, vendor, created_at) VALUES (?, ?, ?)",
            (hostname, vendor, _utcnow()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    # ------------------------------------------------------------------- audits
    def save_audit(self, report: Dict[str, Any]) -> int:
        summary = report.get("summary", {})
        device_id = self.upsert_device(report.get("hostname"), report.get("vendor", "unknown"))
        cur = self._conn.execute(
            """INSERT INTO audits
               (device_id, filename, vendor, hostname, score, passed, failed,
                warnings, critical, predicted_after_score, created_at,
                summary_json, model_json, unknown_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                device_id,
                report.get("filename"),
                report.get("vendor"),
                report.get("hostname"),
                summary.get("score"),
                summary.get("passed"),
                summary.get("failed"),
                summary.get("warnings"),
                summary.get("critical"),
                report.get("predicted_after", {}).get("score"),
                _utcnow(),
                json.dumps(summary),
                json.dumps(report.get("model", {})),
                json.dumps(report.get("unknown_lines", [])),
            ),
        )
        audit_id = int(cur.lastrowid)
        for f in report.get("findings", []):
            self._conn.execute(
                """INSERT INTO findings
                   (audit_id, control_id, title, category, framework, status,
                    severity, observed, expected, rationale, explanation,
                    evidence_json, remediation_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    audit_id,
                    f.get("control_id"),
                    f.get("title"),
                    f.get("category"),
                    f.get("framework"),
                    f.get("status"),
                    f.get("severity"),
                    f.get("observed"),
                    f.get("expected"),
                    f.get("rationale"),
                    f.get("explanation"),
                    json.dumps(f.get("evidence", [])),
                    json.dumps(f.get("remediation")),
                ),
            )
        self._conn.commit()
        return audit_id

    def get_audit(self, audit_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute("SELECT * FROM audits WHERE id = ?", (audit_id,)).fetchone()
        if not row:
            return None
        audit = dict(row)
        audit["summary"] = json.loads(audit.pop("summary_json") or "{}")
        audit["model"] = json.loads(audit.pop("model_json") or "{}")
        audit["unknown_lines"] = json.loads(audit.pop("unknown_json") or "[]")
        audit["findings"] = self.get_findings(audit_id)
        return audit

    def list_audits(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, filename, vendor, hostname, score, passed, failed, "
            "warnings, critical, predicted_after_score, created_at "
            "FROM audits ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_findings(self, audit_id: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM findings WHERE audit_id = ? ORDER BY id", (audit_id,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["evidence"] = json.loads(d.pop("evidence_json") or "[]")
            d["remediation"] = json.loads(d.pop("remediation_json") or "null")
            out.append(d)
        return out

    # ---------------------------------------------------------------- exemplars
    def add_exemplar(self, exemplar: Dict[str, Any]) -> int:
        cur = self._conn.execute(
            """INSERT INTO exemplars
               (text, category, parameter, expected_value, control_id, vendor,
                embedding_json, created_by, created_at, version, approved,
                status, confidence)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                exemplar["text"],
                exemplar.get("category"),
                exemplar.get("parameter"),
                exemplar.get("expected_value"),
                exemplar.get("control_id"),
                exemplar.get("vendor"),
                json.dumps(exemplar.get("embedding")) if exemplar.get("embedding") is not None else None,
                exemplar.get("created_by", "trainer"),
                _utcnow(),
                exemplar.get("version", 1),
                1 if exemplar.get("approved") else 0,
                exemplar.get("status", "PENDING"),
                exemplar.get("confidence"),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def list_exemplars(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM exemplars WHERE status = ? ORDER BY id", (status,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM exemplars ORDER BY id").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["embedding"] = json.loads(d.pop("embedding_json")) if d.get("embedding_json") else None
            out.append(d)
        return out

    def update_exemplar_status(self, exemplar_id: int, status: str, approved: bool) -> None:
        self._conn.execute(
            "UPDATE exemplars SET status = ?, approved = ? WHERE id = ?",
            (status, 1 if approved else 0, exemplar_id),
        )
        self._conn.commit()

    # ---------------------------------------------------------------- audit log
    def append_log(
        self,
        actor: str,
        action: str,
        entity: str,
        entity_id: str,
        detail: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a tamper-evident, hash-chained audit-log entry."""
        prev = self._conn.execute(
            "SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = prev["hash"] if prev else ""
        ts = _utcnow()
        detail_json = json.dumps(detail or {}, sort_keys=True)
        payload = f"{prev_hash}|{ts}|{actor}|{action}|{entity}|{entity_id}|{detail_json}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._conn.execute(
            """INSERT INTO audit_log
               (ts, actor, action, entity, entity_id, detail_json, prev_hash, hash)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ts, actor, action, entity, entity_id, detail_json, prev_hash, digest),
        )
        self._conn.commit()
        return {"ts": ts, "actor": actor, "action": action, "hash": digest, "prev_hash": prev_hash}

    def get_log(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def verify_log(self) -> bool:
        """Recompute the hash chain; return True if intact."""
        prev_hash = ""
        for r in self._conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall():
            payload = (
                f"{prev_hash}|{r['ts']}|{r['actor']}|{r['action']}|"
                f"{r['entity']}|{r['entity_id']}|{r['detail_json']}"
            )
            if hashlib.sha256(payload.encode("utf-8")).hexdigest() != r["hash"]:
                return False
            prev_hash = r["hash"]
        return True

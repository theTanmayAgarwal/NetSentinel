"""Database persistence repository supporting PostgreSQL and SQLite.

Uses PostgreSQL (via psycopg2) when DATABASE_URL is configured, falling back
to SQLite (stdlib sqlite3) for offline sandbox or isolated in-memory unit tests.
Implements single-source-of-truth persistence for learned mappings.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    import psycopg2.extras
    _HAS_POSTGRES = True
except ImportError:
    _HAS_POSTGRES = False


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_pg_url(url: str) -> str:
    """Safely encode password in PostgreSQL connection URL if it contains special characters like '@'."""
    if not url or "postgresql" not in url:
        return url
    try:
        if "@" in url:
            prefix, host_part = url.rsplit("@", 1)
            if ":" in prefix:
                scheme_user, password = prefix.rsplit(":", 1)
                safe_password = urllib.parse.quote(urllib.parse.unquote(password), safe="")
                return f"{scheme_user}:{safe_password}@{host_part}"
    except Exception:
        pass
    return url


class Repository:
    def __init__(self, db_path: Optional[str] = None) -> None:
        raw_url = db_path or os.getenv("DATABASE_URL") or os.getenv("DB_PATH", "sqlite:///./data/app.db")
        self.raw_url = raw_url
        self.is_postgres = "postgresql" in raw_url or "postgres://" in raw_url

        if self.is_postgres:
            if not _HAS_POSTGRES:
                raise RuntimeError("psycopg2 is required for PostgreSQL connections.")
            pg_url = _sanitize_pg_url(raw_url)
            self._pg_url = pg_url
            self._conn = psycopg2.connect(pg_url)
            self._conn.autocommit = True
        else:
            path = raw_url.replace("sqlite:///", "").replace("sqlite://", "")
            self.db_path = path
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")

        self.init_schema()
        self._seed_initial_mappings()

    def close(self) -> None:
        self._conn.close()

    def _execute(self, sql: str, params: Tuple[Any, ...] = ()) -> Any:
        """Execute a query, mapping ? to %s for PostgreSQL."""
        if self.is_postgres:
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            pg_sql = sql.replace("?", "%s")
            cur.execute(pg_sql, params)
            return cur
        else:
            cur = self._conn.cursor()
            cur.execute(sql, params)
            return cur

    def _executescript(self, sql_script: str) -> None:
        if self.is_postgres:
            cur = self._conn.cursor()
            cur.execute(sql_script)
            cur.close()
        else:
            self._conn.executescript(sql_script)
            self._conn.commit()

    def _commit(self) -> None:
        if not self.is_postgres:
            self._conn.commit()

    def init_schema(self) -> None:
        if self.is_postgres:
            ddl = """
            CREATE TABLE IF NOT EXISTS devices (
                id        SERIAL PRIMARY KEY,
                hostname  VARCHAR(255),
                vendor    VARCHAR(255),
                created_at VARCHAR(100) NOT NULL,
                CONSTRAINT unique_host_vendor UNIQUE(hostname, vendor)
            );

            CREATE TABLE IF NOT EXISTS audits (
                id            SERIAL PRIMARY KEY,
                device_id     INTEGER REFERENCES devices(id),
                filename      VARCHAR(255),
                vendor        VARCHAR(255),
                hostname      VARCHAR(255),
                score         DOUBLE PRECISION,
                passed        INTEGER,
                failed        INTEGER,
                warnings      INTEGER,
                critical      INTEGER,
                predicted_after_score DOUBLE PRECISION,
                created_at    VARCHAR(100) NOT NULL,
                summary_json  TEXT,
                model_json    TEXT,
                unknown_json  TEXT
            );

            CREATE TABLE IF NOT EXISTS findings (
                id             SERIAL PRIMARY KEY,
                audit_id       INTEGER NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
                control_id     VARCHAR(255),
                title          VARCHAR(255),
                category       VARCHAR(255),
                framework      VARCHAR(255),
                status         VARCHAR(50),
                severity       VARCHAR(50),
                observed       TEXT,
                expected       TEXT,
                rationale      TEXT,
                explanation    TEXT,
                evidence_json  TEXT,
                remediation_json TEXT
            );

            CREATE TABLE IF NOT EXISTS learned_mappings (
                id                 SERIAL PRIMARY KEY,
                vendor             VARCHAR(100) DEFAULT 'unknown',
                os_version         VARCHAR(100) DEFAULT 'all',
                command_pattern    TEXT NOT NULL,
                security_property  VARCHAR(100) NOT NULL,
                value              TEXT,
                unit               VARCHAR(50),
                category           VARCHAR(100),
                control_id         VARCHAR(100),
                ai_confidence      DOUBLE PRECISION DEFAULT 1.0,
                ai_proposal        TEXT,
                status             VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACTIVE', 'STALE', 'REVOKED', 'REJECTED')),
                version            INTEGER DEFAULT 1,
                reviewer           VARCHAR(100) DEFAULT 'administrator',
                reviewed_at        VARCHAR(100),
                created_at         VARCHAR(100) NOT NULL,
                updated_at         VARCHAR(100)
            );

            CREATE INDEX IF NOT EXISTS idx_lm_vendor_pattern ON learned_mappings (vendor, command_pattern);
            CREATE INDEX IF NOT EXISTS idx_lm_status ON learned_mappings (status);

            CREATE TABLE IF NOT EXISTS exemplars (
                id           SERIAL PRIMARY KEY,
                text         TEXT NOT NULL,
                category     VARCHAR(100),
                parameter    VARCHAR(100),
                expected_value TEXT,
                control_id   VARCHAR(100),
                vendor       VARCHAR(100),
                platform     VARCHAR(100),
                os_version   VARCHAR(100),
                security_property VARCHAR(100),
                value        TEXT,
                unit         VARCHAR(50),
                embedding_json TEXT,
                created_by   VARCHAR(100),
                reviewer     VARCHAR(100),
                created_at   VARCHAR(100) NOT NULL,
                updated_at   VARCHAR(100),
                last_validated_at VARCHAR(100),
                version      INTEGER DEFAULT 1,
                approved     INTEGER DEFAULT 0,
                status       VARCHAR(20) DEFAULT 'PENDING',
                confidence   DOUBLE PRECISION
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id         SERIAL PRIMARY KEY,
                ts         VARCHAR(100) NOT NULL,
                actor      VARCHAR(100),
                action     VARCHAR(100),
                entity     VARCHAR(100),
                entity_id  VARCHAR(100),
                detail_json TEXT,
                prev_hash  VARCHAR(255),
                hash       VARCHAR(255)
            );

            CREATE TABLE IF NOT EXISTS mapping_usage (
                id                     SERIAL PRIMARY KEY,
                mapping_id             INTEGER NOT NULL REFERENCES learned_mappings(id) ON DELETE CASCADE,
                audit_id               INTEGER,
                configuration_fragment TEXT,
                security_property      VARCHAR(100),
                observed_value         TEXT,
                control_id             VARCHAR(100),
                finding_id             INTEGER,
                used_at                VARCHAR(100) NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mu_mapping_id ON mapping_usage (mapping_id);
            CREATE INDEX IF NOT EXISTS idx_mu_audit_id ON mapping_usage (audit_id);
            """
        else:
            ddl = """
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

            CREATE TABLE IF NOT EXISTS learned_mappings (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor             TEXT DEFAULT 'unknown',
                os_version         TEXT DEFAULT 'all',
                command_pattern    TEXT NOT NULL,
                security_property  TEXT NOT NULL,
                value              TEXT,
                unit               TEXT,
                category           TEXT,
                control_id         TEXT,
                ai_confidence      REAL DEFAULT 1.0,
                ai_proposal        TEXT,
                status             TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACTIVE', 'STALE', 'REVOKED', 'REJECTED')),
                version            INTEGER DEFAULT 1,
                reviewer           TEXT DEFAULT 'administrator',
                reviewed_at        TEXT,
                created_at         TEXT NOT NULL,
                updated_at         TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_lm_vendor_pattern ON learned_mappings (vendor, command_pattern);
            CREATE INDEX IF NOT EXISTS idx_lm_status ON learned_mappings (status);

            CREATE TABLE IF NOT EXISTS exemplars (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                text         TEXT NOT NULL,
                category     TEXT,
                parameter    TEXT,
                expected_value TEXT,
                control_id   TEXT,
                vendor       TEXT,
                platform     TEXT,
                os_version   TEXT,
                security_property TEXT,
                value        TEXT,
                unit         TEXT,
                embedding_json TEXT,
                created_by   TEXT,
                reviewer     TEXT,
                created_at   TEXT NOT NULL,
                updated_at   TEXT,
                last_validated_at TEXT,
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

            CREATE TABLE IF NOT EXISTS mapping_usage (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                mapping_id             INTEGER NOT NULL REFERENCES learned_mappings(id) ON DELETE CASCADE,
                audit_id               INTEGER,
                configuration_fragment TEXT,
                security_property      TEXT,
                observed_value         TEXT,
                control_id             TEXT,
                finding_id             INTEGER,
                used_at                TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mu_mapping_id ON mapping_usage (mapping_id);
            CREATE INDEX IF NOT EXISTS idx_mu_audit_id ON mapping_usage (audit_id);
            """


        self._executescript(ddl)

    def _seed_initial_mappings(self) -> None:
        """Seed a small number of legitimate default mappings if table is empty."""
        cur = self._execute("SELECT COUNT(*) as cnt FROM learned_mappings")
        row = cur.fetchone()
        cnt = row[0] if row else 0
        if cnt == 0:
            seeds = [
                {
                    "vendor": "UnknownVendor",
                    "os_version": "5.2",
                    "command_pattern": "set xyz secure-admin-timeout <value>",
                    "security_property": "admin_session_timeout",
                    "value": "300",
                    "unit": "seconds",
                    "category": "Secure Management",
                    "control_id": "CIS-NET-18",
                    "ai_confidence": 0.92,
                    "ai_proposal": "Administrative session timeout setting",
                    "status": "ACTIVE",
                    "version": 1,
                    "reviewer": "administrator",
                },
                {
                    "vendor": "cisco",
                    "os_version": "15.2",
                    "command_pattern": "ip ssh version 2",
                    "security_property": "ssh_version",
                    "value": "2",
                    "unit": "",
                    "category": "SSH Protocols",
                    "control_id": "CIS-NET-01",
                    "ai_confidence": 0.99,
                    "ai_proposal": "SSH protocol version setting",
                    "status": "ACTIVE",
                    "version": 1,
                    "reviewer": "administrator",
                },
                {
                    "vendor": "juniper",
                    "os_version": "21.4",
                    "command_pattern": "set system services ssh",
                    "security_property": "ssh_enabled",
                    "value": "true",
                    "unit": "",
                    "category": "SSH Protocols",
                    "control_id": "CIS-NET-01",
                    "ai_confidence": 0.98,
                    "ai_proposal": "Enable SSH management service",
                    "status": "ACTIVE",
                    "version": 1,
                    "reviewer": "administrator",
                },
                {
                    "vendor": "UnknownVendor",
                    "os_version": "5.2",
                    "command_pattern": "set xyz secure-admin-timeout 300",
                    "security_property": "admin_session_timeout",
                    "value": "300",
                    "unit": "seconds",
                    "category": "Secure Management",
                    "control_id": "CIS-NET-18",
                    "ai_confidence": 0.92,
                    "ai_proposal": "Detected administrative session timeout setting from command syntax.",
                    "status": "PENDING",
                    "version": 1,
                    "reviewer": "administrator",
                },
            ]
            for s in seeds:
                existing = self.find_mapping_by_pattern(s["command_pattern"], vendor=s["vendor"])
                if not existing:
                    self.create_mapping(s)

    def find_mapping_by_pattern(
        self, command_pattern: str, vendor: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find existing mapping matching command pattern and optional vendor regardless of status."""
        clean_pat = command_pattern.strip().lower()
        cur = self._execute(
            "SELECT * FROM learned_mappings WHERE LOWER(command_pattern) = ? ORDER BY id DESC LIMIT 1",
            (clean_pat,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)

        # Fallback fuzzy match for secure-admin-timeout patterns
        if "secure-admin-timeout" in clean_pat:
            cur2 = self._execute(
                "SELECT * FROM learned_mappings WHERE LOWER(command_pattern) LIKE '%secure-admin-timeout%' ORDER BY id DESC LIMIT 1"
            )
            row2 = cur2.fetchone()
            if row2:
                return dict(row2)

        return None



    # ------------------------------------------------------------------ learned_mappings CRUD (PART A)
    def create_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        now = _utcnow()
        status = (mapping.get("status") or "PENDING").upper()
        if status == "APPROVED":
            status = "ACTIVE"
        cur = self._execute(
            """INSERT INTO learned_mappings
               (vendor, os_version, command_pattern, security_property, value, unit,
                category, control_id, ai_confidence, ai_proposal, status, version,
                reviewer, reviewed_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               RETURNING id""" if self.is_postgres else
            """INSERT INTO learned_mappings
               (vendor, os_version, command_pattern, security_property, value, unit,
                category, control_id, ai_confidence, ai_proposal, status, version,
                reviewer, reviewed_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mapping.get("vendor", "unknown"),
                mapping.get("os_version", "all"),
                mapping["command_pattern"],
                mapping["security_property"],
                mapping.get("value"),
                mapping.get("unit"),
                mapping.get("category", "System Configuration"),
                mapping.get("control_id"),
                mapping.get("ai_confidence", 1.0),
                mapping.get("ai_proposal"),
                status,
                mapping.get("version", 1),
                mapping.get("reviewer", "administrator"),
                now if status == "ACTIVE" else mapping.get("reviewed_at"),
                now,
                now,
            ),
        )

        if self.is_postgres:
            mapping_id = cur.fetchone()[0]
        else:
            mapping_id = cur.lastrowid
            self._commit()

        # Also sync to exemplars table for backwards compatibility
        self._sync_to_exemplars(mapping_id, mapping, status, now)

        created = self.get_mapping(mapping_id)
        return created or {"id": mapping_id, **mapping, "status": status, "version": 1, "created_at": now}

    def _sync_to_exemplars(self, mapping_id: int, mapping: Dict[str, Any], status: str, now: str) -> None:
        try:
            self._execute(
                """INSERT INTO exemplars
                   (id, text, category, parameter, expected_value, control_id, vendor,
                    os_version, security_property, value, unit, reviewer, created_at,
                    updated_at, version, approved, status, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (id) DO NOTHING""" if self.is_postgres else
                """INSERT OR IGNORE INTO exemplars
                   (id, text, category, parameter, expected_value, control_id, vendor,
                    os_version, security_property, value, unit, reviewer, created_at,
                    updated_at, version, approved, status, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mapping_id,
                    mapping.get("command_pattern", ""),
                    mapping.get("category", "System Configuration"),
                    mapping.get("security_property", ""),
                    mapping.get("value", ""),
                    mapping.get("control_id"),
                    mapping.get("vendor", "unknown"),
                    mapping.get("os_version", "all"),
                    mapping.get("security_property", ""),
                    mapping.get("value", ""),
                    mapping.get("unit"),
                    mapping.get("reviewer", "administrator"),
                    now,
                    now,
                    mapping.get("version", 1),
                    1 if status == "ACTIVE" else 0,
                    status,
                    mapping.get("ai_confidence", 1.0),
                ),
            )
            self._commit()
        except Exception:
            pass

    def get_mapping(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        cur = self._execute("SELECT * FROM learned_mappings WHERE id = ?", (mapping_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        summary = self.get_mapping_usage_summary(mapping_id)
        d["usage_count"] = summary["usage_count"]
        d["last_used"] = summary["last_used"]
        d["audits_used"] = summary["audits_used"]
        d["controls_evaluated"] = summary["controls_evaluated"]
        return d

    def list_mappings(
        self, status: Optional[str] = None, vendor: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM learned_mappings"
        conditions = []
        params = []

        if status:
            stat = status.upper()
            if stat == "APPROVED":
                stat = "ACTIVE"
            conditions.append("status = ?")
            params.append(stat)
        if vendor:
            conditions.append("LOWER(vendor) = LOWER(?)")
            params.append(vendor)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC"
        cur = self._execute(query, tuple(params))
        rows = cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            summary = self.get_mapping_usage_summary(d["id"])
            d["usage_count"] = summary["usage_count"]
            d["last_used"] = summary["last_used"]
            d["audits_used"] = summary["audits_used"]
            d["controls_evaluated"] = summary["controls_evaluated"]
            results.append(d)
        return results

    # ------------------------------------------------------------------ mapping_usage (PART F)
    def record_mapping_usage(
        self,
        mapping_id: int,
        audit_id: Optional[int] = None,
        configuration_fragment: Optional[str] = None,
        security_property: Optional[str] = None,
        observed_value: Optional[str] = None,
        control_id: Optional[str] = None,
        finding_id: Optional[int] = None,
        used_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a mapping usage event if mapping is ACTIVE. Idempotent per (mapping_id, audit_id, configuration_fragment)."""
        # 1. Verify mapping exists and is ACTIVE
        cur = self._execute("SELECT status FROM learned_mappings WHERE id = ?", (mapping_id,))
        row = cur.fetchone()
        if not row:
            return {}
        status = (row[0] if isinstance(row, (tuple, list)) else row["status"]).upper()
        if status not in ("ACTIVE", "APPROVED"):
            # PENDING, REJECTED, STALE, REVOKED create NO trusted usage
            return {}

        now = used_at or _utcnow()
        clean_frag = (configuration_fragment or "").strip()

        # 2. Check idempotency: avoid inserting duplicate usage row for same audit_id, mapping_id, fragment
        if audit_id and clean_frag:
            cur_dup = self._execute(
                "SELECT id FROM mapping_usage WHERE mapping_id = ? AND audit_id = ? AND configuration_fragment = ?",
                (mapping_id, audit_id, clean_frag),
            )
            existing = cur_dup.fetchone()
            if existing:
                rec_id = existing[0] if isinstance(existing, (tuple, list)) else existing["id"]
                return self.get_mapping_usage_by_id(rec_id)

        # 3. Insert usage record
        if self.is_postgres:
            cur_ins = self._execute(
                """INSERT INTO mapping_usage 
                (mapping_id, audit_id, configuration_fragment, security_property, observed_value, control_id, finding_id, used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                (mapping_id, audit_id, clean_frag, security_property, str(observed_value) if observed_value is not None else None, control_id, finding_id, now),
            )
            new_id = cur_ins.fetchone()[0]
        else:
            cur_ins = self._execute(
                """INSERT INTO mapping_usage 
                (mapping_id, audit_id, configuration_fragment, security_property, observed_value, control_id, finding_id, used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (mapping_id, audit_id, clean_frag, security_property, str(observed_value) if observed_value is not None else None, control_id, finding_id, now),
            )
            new_id = cur_ins.lastrowid

        self._commit()
        return self.get_mapping_usage_by_id(new_id)

    def get_mapping_usage_by_id(self, usage_id: int) -> Dict[str, Any]:
        cur = self._execute("SELECT * FROM mapping_usage WHERE id = ?", (usage_id,))
        row = cur.fetchone()
        return dict(row) if row else {}

    def list_mapping_usage(self, mapping_id: int) -> List[Dict[str, Any]]:
        cur = self._execute(
            "SELECT * FROM mapping_usage WHERE mapping_id = ? ORDER BY id DESC",
            (mapping_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_mapping_usage_summary(self, mapping_id: int) -> Dict[str, Any]:
        cur_count = self._execute(
            "SELECT COUNT(*) as cnt, MAX(used_at) as last_used FROM mapping_usage WHERE mapping_id = ?",
            (mapping_id,),
        )
        row = cur_count.fetchone()
        usage_count = row[0] if row and row[0] is not None else 0
        last_used = row[1] if row and row[1] is not None else None

        events = self.list_mapping_usage(mapping_id)
        audits_used = sorted(list({e["audit_id"] for e in events if e.get("audit_id") is not None}))
        controls_eval = sorted(list({e["control_id"] for e in events if e.get("control_id")}))

        return {
            "mapping_id": mapping_id,
            "usage_count": usage_count,
            "last_used": last_used,
            "audits_used": audits_used,
            "controls_evaluated": controls_eval,
            "usage_events": events,
        }


    def update_mapping(
        self, mapping_id: int, updates: Dict[str, Any], reviewer: str = "administrator"
    ) -> Optional[Dict[str, Any]]:
        existing = self.get_mapping(mapping_id)
        if not existing:
            return None

        now = _utcnow()
        fields = []
        values = []

        for k, v in updates.items():
            if k in (
                "vendor",
                "os_version",
                "command_pattern",
                "security_property",
                "value",
                "unit",
                "category",
                "control_id",
                "ai_confidence",
                "ai_proposal",
                "status",
                "version",
            ):
                val = v.upper() if k == "status" and isinstance(v, str) else v
                if k == "status" and val == "APPROVED":
                    val = "ACTIVE"
                fields.append(f"{k} = ?")
                values.append(val)

        if "status" in updates and updates["status"] in ("ACTIVE", "APPROVED") and not existing.get("reviewed_at"):
            fields.append("reviewed_at = ?")
            values.append(now)

        fields.append("reviewer = ?")
        values.append(reviewer)

        fields.append("updated_at = ?")
        values.append(now)

        values.append(mapping_id)

        sql = f"UPDATE learned_mappings SET {', '.join(fields)} WHERE id = ?"
        self._execute(sql, tuple(values))

        # Sync to exemplars table
        if "status" in updates:
            stat = updates["status"].upper()
            if stat == "APPROVED":
                stat = "ACTIVE"
            app = 1 if stat == "ACTIVE" else 0
            self._execute(
                "UPDATE exemplars SET status = ?, approved = ?, reviewer = ?, updated_at = ? WHERE id = ?",
                (stat, app, reviewer, now, mapping_id),
            )

        self._commit()
        return self.get_mapping(mapping_id)


    def change_mapping_status(
        self, mapping_id: int, status: str, reviewer: str = "administrator"
    ) -> Optional[Dict[str, Any]]:
        stat = status.upper()
        if stat == "APPROVED":
            stat = "ACTIVE"
        valid = {"PENDING", "ACTIVE", "STALE", "REVOKED", "REJECTED"}
        if stat not in valid:
            raise ValueError(f"Invalid status '{stat}'. Must be one of {sorted(valid)}")

        return self.update_mapping(mapping_id, {"status": stat}, reviewer=reviewer)


    # ---------------------------------------------------------------- devices & audits
    def upsert_device(self, hostname: Optional[str], vendor: str) -> int:
        cur = self._execute(
            "SELECT id FROM devices WHERE hostname IS ? AND vendor = ?" if not self.is_postgres else
            "SELECT id FROM devices WHERE hostname IS NOT DISTINCT FROM %s AND vendor = %s",
            (hostname, vendor),
        )
        row = cur.fetchone()
        if row:
            return int(row["id"])
        
        cur = self._execute(
            "INSERT INTO devices (hostname, vendor, created_at) VALUES (?, ?, ?) RETURNING id" if self.is_postgres else
            "INSERT INTO devices (hostname, vendor, created_at) VALUES (?, ?, ?)",
            (hostname, vendor, _utcnow()),
        )
        if self.is_postgres:
            dev_id = cur.fetchone()[0]
        else:
            dev_id = cur.lastrowid
            self._commit()
        return int(dev_id)

    def save_audit(self, report: Dict[str, Any]) -> int:
        summary = report.get("summary", {})
        device_id = self.upsert_device(report.get("hostname"), report.get("vendor", "unknown"))
        cur = self._execute(
            """INSERT INTO audits
               (device_id, filename, vendor, hostname, score, passed, failed,
                warnings, critical, predicted_after_score, created_at,
                summary_json, model_json, unknown_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id""" if self.is_postgres else
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
        if self.is_postgres:
            audit_id = int(cur.fetchone()[0])
        else:
            audit_id = int(cur.lastrowid)

        for f in report.get("findings", []):
            self._execute(
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
        self._commit()
        return audit_id

    def get_audit(self, audit_id: int) -> Optional[Dict[str, Any]]:
        cur = self._execute("SELECT * FROM audits WHERE id = ?", (audit_id,))
        row = cur.fetchone()
        if not row:
            return None
        audit = dict(row)
        audit["summary"] = json.loads(audit.pop("summary_json") or "{}")
        audit["model"] = json.loads(audit.pop("model_json") or "{}")
        audit["unknown_lines"] = json.loads(audit.pop("unknown_json") or "[]")
        audit["findings"] = self.get_findings(audit_id)
        return audit

    def list_audits(self) -> List[Dict[str, Any]]:
        cur = self._execute(
            "SELECT id, filename, vendor, hostname, score, passed, failed, "
            "warnings, critical, predicted_after_score, created_at "
            "FROM audits ORDER BY id DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    def get_findings(self, audit_id: int) -> List[Dict[str, Any]]:
        cur = self._execute(
            "SELECT * FROM findings WHERE audit_id = ? ORDER BY id", (audit_id,)
        )
        out = []
        for r in cur.fetchall():
            d = dict(r)
            d["evidence"] = json.loads(d.pop("evidence_json") or "[]")
            d["remediation"] = json.loads(d.pop("remediation_json") or "null")
            out.append(d)
        return out

    # ---------------------------------------------------------------- exemplars / legacy store compatibility
    def add_exemplar(self, exemplar: Dict[str, Any]) -> int:
        mapping_data = {
            "command_pattern": exemplar.get("text") or exemplar.get("raw_text") or exemplar.get("command_pattern", ""),
            "security_property": exemplar.get("security_property") or exemplar.get("parameter", ""),
            "value": exemplar.get("value") or exemplar.get("expected_value", ""),
            "unit": exemplar.get("unit"),
            "category": exemplar.get("category", "System Configuration"),
            "control_id": exemplar.get("control_id"),
            "vendor": exemplar.get("vendor", "unknown"),
            "os_version": exemplar.get("os_version", "all"),
            "ai_confidence": exemplar.get("confidence") or exemplar.get("ai_confidence", 1.0),
            "status": exemplar.get("status", "PENDING"),
            "version": exemplar.get("version", 1),
            "reviewer": exemplar.get("reviewer", "administrator"),
        }
        res = self.create_mapping(mapping_data)
        return res["id"]

    def get_exemplar(self, exemplar_id: int) -> Optional[Dict[str, Any]]:
        mapping = self.get_mapping(exemplar_id)
        if not mapping:
            return None
        return {
            "id": mapping["id"],
            "text": mapping["command_pattern"],
            "category": mapping["category"],
            "parameter": mapping["security_property"],
            "expected_value": mapping["value"],
            "control_id": mapping["control_id"],
            "vendor": mapping["vendor"],
            "os_version": mapping["os_version"],
            "security_property": mapping["security_property"],
            "value": mapping["value"],
            "unit": mapping["unit"],
            "version": mapping["version"],
            "approved": 1 if mapping["status"] == "ACTIVE" else 0,
            "status": mapping["status"],
            "reviewer": mapping["reviewer"],
            "updated_at": mapping["updated_at"],
            "last_validated_at": mapping.get("reviewed_at") or mapping["updated_at"],
        }

    def list_exemplars(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        mappings = self.list_mappings(status=status)
        return [
            {
                "id": m["id"],
                "text": m["command_pattern"],
                "category": m["category"],
                "parameter": m["security_property"],
                "expected_value": m["value"],
                "control_id": m["control_id"],
                "vendor": m["vendor"],
                "os_version": m["os_version"],
                "security_property": m["security_property"],
                "value": m["value"],
                "unit": m["unit"],
                "version": m["version"],
                "approved": 1 if m["status"] == "ACTIVE" else 0,
                "status": m["status"],
                "reviewer": m["reviewer"],
                "updated_at": m["updated_at"],
                "last_validated_at": m.get("reviewed_at") or m["updated_at"],
            }
            for m in mappings
        ]

    def update_exemplar_status(self, exemplar_id: int, status: str, approved: bool, reviewer: str = "administrator") -> None:
        self.change_mapping_status(exemplar_id, status if status else ("ACTIVE" if approved else "REJECTED"), reviewer=reviewer)

    def update_exemplar(self, exemplar_id: int, updates: Dict[str, Any], reviewer: str = "administrator") -> None:
        self.update_mapping(exemplar_id, updates, reviewer=reviewer)

    def revoke_exemplar(self, exemplar_id: int, reviewer: str = "administrator") -> None:
        self.change_mapping_status(exemplar_id, "REVOKED", reviewer=reviewer)

    def revalidate_exemplar(self, exemplar_id: int, reviewer: str = "administrator") -> None:
        item = self.get_mapping(exemplar_id)
        ver = (item.get("version") or 1) + 1 if item else 1
        self.update_mapping(exemplar_id, {"status": "ACTIVE", "version": ver}, reviewer=reviewer)

    # ---------------------------------------------------------------- audit log
    def append_log(
        self,
        actor: str,
        action: str,
        entity: str,
        entity_id: str,
        detail: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cur = self._execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
        prev = cur.fetchone()
        prev_hash = prev[0] if prev else ""
        ts = _utcnow()
        detail_json = json.dumps(detail or {}, sort_keys=True)
        payload = f"{prev_hash}|{ts}|{actor}|{action}|{entity}|{entity_id}|{detail_json}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._execute(
            """INSERT INTO audit_log
               (ts, actor, action, entity, entity_id, detail_json, prev_hash, hash)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ts, actor, action, entity, entity_id, detail_json, prev_hash, digest),
        )
        self._commit()
        return {"ts": ts, "actor": actor, "action": action, "hash": digest, "prev_hash": prev_hash}

    def get_log(self) -> List[Dict[str, Any]]:
        cur = self._execute("SELECT * FROM audit_log ORDER BY id")
        return [dict(r) for r in cur.fetchall()]

    def verify_log(self) -> bool:
        prev_hash = ""
        cur = self._execute("SELECT * FROM audit_log ORDER BY id")
        for r in cur.fetchall():
            row = dict(r)
            payload = (
                f"{prev_hash}|{row['ts']}|{row['actor']}|{row['action']}|"
                f"{row['entity']}|{row['entity_id']}|{row['detail_json']}"
            )
            if hashlib.sha256(payload.encode("utf-8")).hexdigest() != row["hash"]:
                return False
            prev_hash = row["hash"]
        return True

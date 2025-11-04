"""Persistence adapters for premium API metadata."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .models import ApiKeyRecord


class ApiKeyRepository:
    """Storage abstraction for API keys."""

    def create(self, record: ApiKeyRecord) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def get_by_prefix(self, prefix: str) -> ApiKeyRecord | None:  # pragma: no cover - interface
        raise NotImplementedError

    def mark_revoked(self, key_id: str, revoked_at: datetime) -> None:  # pragma: no cover
        raise NotImplementedError


class SqliteApiKeyRepository(ApiKeyRepository):
    """SQLite-backed implementation suitable for edge deployments."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    plan_tier TEXT NOT NULL,
                    prefix TEXT NOT NULL UNIQUE,
                    hashed_key TEXT NOT NULL,
                    rate_limit_per_minute INTEGER NOT NULL,
                    rate_limit_burst INTEGER NOT NULL,
                    premium_rate REAL NOT NULL DEFAULT 0.10,
                    created_at TEXT NOT NULL,
                    rotated_at TEXT,
                    revoked_at TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    metadata TEXT
                )
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(api_keys)")}
            if "premium_rate" not in columns:
                conn.execute("ALTER TABLE api_keys ADD COLUMN premium_rate REAL NOT NULL DEFAULT 0.10")
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_keys_customer
                    ON api_keys(customer_id)
                """
            )
            conn.commit()

    def create(self, record: ApiKeyRecord) -> None:
        payload = record.model_dump()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (
                    key_id, customer_id, plan_tier, prefix, hashed_key,
                    rate_limit_per_minute, rate_limit_burst, premium_rate, created_at,
                    rotated_at, revoked_at, active, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["key_id"],
                    payload["customer_id"],
                    payload["plan_tier"],
                    payload["prefix"],
                    payload["hashed_key"],
                    payload["rate_limit_per_minute"],
                    payload["rate_limit_burst"],
                    payload.get("premium_rate", 0.10),
                    payload["created_at"].isoformat(),
                    payload["rotated_at"].isoformat() if payload["rotated_at"] else None,
                    payload["revoked_at"].isoformat() if payload["revoked_at"] else None,
                    1 if payload["active"] else 0,
                    json.dumps(payload["metadata"], separators=(",", ":")) if payload["metadata"] else None,
                ),
            )
            conn.commit()

    def get_by_prefix(self, prefix: str) -> ApiKeyRecord | None:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE prefix = ? AND active = 1", (prefix,)
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def mark_revoked(self, key_id: str, revoked_at: datetime) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE api_keys SET active = 0, revoked_at = ? WHERE key_id = ?",
                (revoked_at.isoformat(), key_id),
            )
            conn.commit()

    def _row_to_record(self, row: sqlite3.Row) -> ApiKeyRecord:
        metadata_raw = row["metadata"]
        metadata = json.loads(metadata_raw) if metadata_raw else {}
        return ApiKeyRecord(
            key_id=row["key_id"],
            customer_id=row["customer_id"],
            plan_tier=row["plan_tier"],
            prefix=row["prefix"],
            hashed_key=row["hashed_key"],
            rate_limit_per_minute=row["rate_limit_per_minute"],
            rate_limit_burst=row["rate_limit_burst"],
            premium_rate=row["premium_rate"],
            created_at=datetime.fromisoformat(row["created_at"]),
            rotated_at=datetime.fromisoformat(row["rotated_at"]) if row["rotated_at"] else None,
            revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
            active=bool(row["active"]),
            metadata=metadata,
        )


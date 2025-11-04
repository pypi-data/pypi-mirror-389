"""Job persistence and service helpers."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator
from uuid import UUID

from .models import JobRecord, JobResult, JobStatus


class JobRepository:
    """Storage abstraction for asynchronous jobs."""

    def create(self, record: JobRecord) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def get(self, job_id: UUID) -> JobRecord | None:  # pragma: no cover - interface
        raise NotImplementedError

    def mark_running(self, job_id: UUID, started_at: datetime) -> None:  # pragma: no cover
        raise NotImplementedError

    def complete(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        result: dict | None,
        usage: dict | None,
        error_code: str | None,
        error_message: str | None,
        completed_at: datetime,
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        completed_at: datetime | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    def get_result(self, job_id: UUID) -> JobResult | None:  # pragma: no cover
        raise NotImplementedError


class SqliteJobRepository(JobRepository):
    """SQLite-backed repository for job metadata and results."""

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
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model TEXT NOT NULL,
                    parameters TEXT,
                    metadata TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    webhook_url TEXT,
                    webhook_id TEXT,
                    webhook_secret TEXT,
                    webhook_events TEXT,
                    request_payload TEXT,
                    result_payload TEXT,
                    usage_payload TEXT,
                    premium_rate REAL NOT NULL DEFAULT 0.10
                )
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(jobs)")
            }
            if "premium_rate" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN premium_rate REAL NOT NULL DEFAULT 0.10")
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_jobs_customer
                    ON jobs(customer_id)
                """
            )
            conn.commit()

    def create(self, record: JobRecord) -> None:
        values = (
            str(record.job_id),
            record.customer_id,
            record.status.value,
            record.model,
            json.dumps(record.parameters, separators=(",", ":")) if record.parameters else None,
            json.dumps(record.metadata, separators=(",", ":")) if record.metadata else None,
            record.error_code,
            record.error_message,
            record.created_at.isoformat(),
            record.started_at.isoformat() if record.started_at else None,
            record.completed_at.isoformat() if record.completed_at else None,
            record.webhook_url,
            record.webhook_id,
            record.webhook_secret,
            json.dumps(record.webhook_events, separators=(",", ":")) if record.webhook_events else None,
            json.dumps(record.request_payload, separators=(",", ":")) if record.request_payload else None,
            None,
            None,
            record.premium_rate,
        )
        assert len(values) == 19
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, customer_id, status, model, parameters,
                    metadata, error_code, error_message, created_at,
                    started_at, completed_at, webhook_url, webhook_id, webhook_secret,
                    webhook_events, request_payload, result_payload, usage_payload, premium_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            conn.commit()

    def get(self, job_id: UUID) -> JobRecord | None:
        with self._connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (str(job_id),))
            row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def mark_running(self, job_id: UUID, started_at: datetime) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, started_at = ? WHERE job_id = ?",
                (JobStatus.running.value, started_at.isoformat(), str(job_id)),
            )
            conn.commit()

    def complete(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        result: dict | None,
        usage: dict | None,
        error_code: str | None,
        error_message: str | None,
        completed_at: datetime,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE jobs
                   SET status = ?,
                       completed_at = ?,
                       error_code = ?,
                       error_message = ?,
                       result_payload = ?,
                       usage_payload = ?
                 WHERE job_id = ?
                """,
                (
                    status.value,
                    completed_at.isoformat(),
                    error_code,
                    error_message,
                    json.dumps(result, separators=(",", ":")) if result else None,
                    json.dumps(usage, separators=(",", ":")) if usage else None,
                    str(job_id),
                ),
            )
            conn.commit()

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        completed_at: datetime | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error_code = ?, error_message = ?, completed_at = COALESCE(?, completed_at) WHERE job_id = ?",
                (status.value, error_code, error_message, completed_at.isoformat() if completed_at else None, str(job_id)),
            )
            conn.commit()

    def get_result(self, job_id: UUID) -> JobResult | None:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT job_id, status, result_payload, usage_payload, error_code, error_message, completed_at"
                "  FROM jobs WHERE job_id = ?",
                (str(job_id),),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return JobResult(
            job_id=UUID(row["job_id"]),
            status=JobStatus(row["status"]),
            result=json.loads(row["result_payload"]) if row["result_payload"] else None,
            usage=json.loads(row["usage_payload"]) if row["usage_payload"] else None,
            error_code=row["error_code"],
            error_message=row["error_message"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

    def _row_to_record(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            job_id=UUID(row["job_id"]),
            customer_id=row["customer_id"],
            status=JobStatus(row["status"]),
            model=row["model"],
            parameters=json.loads(row["parameters"]) if row["parameters"] else {},
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            request_payload=json.loads(row["request_payload"]) if row["request_payload"] else {},
            error_code=row["error_code"],
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            webhook_url=row["webhook_url"],
            webhook_id=row["webhook_id"],
            webhook_secret=row["webhook_secret"],
            webhook_events=json.loads(row["webhook_events"]) if row["webhook_events"] else None,
            premium_rate=float(row["premium_rate"]) if row["premium_rate"] is not None else 0.10,
        )


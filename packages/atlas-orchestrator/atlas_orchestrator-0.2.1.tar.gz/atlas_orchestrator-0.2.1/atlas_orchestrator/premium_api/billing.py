"""Billing engine and persistence for premium API usage."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .audit import AuditLogger
from .models import JobRecord, JobStatus


_DECIMAL_QUANTIZE = Decimal("0.000001")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        if not value:
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            return None
    return None


def _decimal_to_str(value: Decimal) -> str:
    return str(value.quantize(_DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP))


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value.quantize(_DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP):.6f}"


def _month_period(timestamp: datetime) -> str:
    ts = timestamp.astimezone(timezone.utc)
    return ts.strftime("%Y-%m")


class UsageRecord(BaseModel):
    """Persisted usage snapshot per job."""

    model_config = ConfigDict(frozen=True)

    usage_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    customer_id: str
    premium_rate: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    openrouter_cost: Decimal | None = None
    premium_value: Decimal = Field(default_factory=lambda: Decimal("0"))
    total_billed: Decimal = Field(default_factory=lambda: Decimal("0"))
    currency: str = "USD"
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    anomaly_flag: bool = False
    anomaly_reason: str | None = None
    raw_usage: dict[str, Any] = Field(default_factory=dict)

    def to_job_usage_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.prompt_tokens is not None:
            payload["prompt_tokens"] = self.prompt_tokens
        if self.completion_tokens is not None:
            payload["completion_tokens"] = self.completion_tokens
        if self.total_tokens is not None:
            payload["total_tokens"] = self.total_tokens
        if self.openrouter_cost is not None:
            payload["openrouter_cost"] = {
                "value": _format_decimal(self.openrouter_cost),
                "currency": self.currency,
            }
        payload["premium"] = {
            "rate": self.premium_rate,
            "value": _format_decimal(self.premium_value),
        }
        payload["total_billed"] = {
            "value": _format_decimal(self.total_billed),
            "currency": self.currency,
        }
        if self.anomaly_flag:
            payload["anomaly"] = {"flagged": True, "reason": self.anomaly_reason}
        return payload

    def to_api_payload(self) -> dict[str, Any]:
        payload = {
            "usage_id": str(self.usage_id),
            "job_id": str(self.job_id),
            "customer_id": self.customer_id,
            "recorded_at": self.recorded_at.isoformat(),
            "premium": {
                "rate": self.premium_rate,
                "value": _format_decimal(self.premium_value),
            },
            "total_billed": {
                "value": _format_decimal(self.total_billed),
                "currency": self.currency,
            },
        }
        if self.openrouter_cost is not None:
            payload["openrouter_cost"] = {
                "value": _format_decimal(self.openrouter_cost),
                "currency": self.currency,
            }
        if self.prompt_tokens is not None:
            payload["prompt_tokens"] = self.prompt_tokens
        if self.completion_tokens is not None:
            payload["completion_tokens"] = self.completion_tokens
        if self.total_tokens is not None:
            payload["total_tokens"] = self.total_tokens
        if self.anomaly_flag:
            payload["anomaly"] = {"flagged": True, "reason": self.anomaly_reason}
        return payload


class InvoiceSummary(BaseModel):
    """Aggregated totals per customer and billing period."""

    model_config = ConfigDict(frozen=True)

    customer_id: str
    period: str
    total_openrouter_cost: Decimal
    total_premium_value: Decimal
    total_billed_value: Decimal
    usage_count: int
    currency: str = "USD"
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BillingRepository:
    """Storage abstraction for billing usage metadata."""

    def record_usage(self, record: UsageRecord) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def list_usage(
        self,
        customer_id: str,
        *,
        limit: int,
        starting_after: UUID | None = None,
        ending_before: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[UsageRecord]:  # pragma: no cover - interface
        raise NotImplementedError

    def get_invoice(self, customer_id: str, period: str) -> InvoiceSummary | None:  # pragma: no cover - interface
        raise NotImplementedError

    def upsert_invoice(self, summary: InvoiceSummary) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class SqliteBillingRepository(BillingRepository):
    """SQLite-backed persistence for usage records and invoice summaries."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_records (
                    usage_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    premium_rate REAL NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    openrouter_cost TEXT,
                    premium_value TEXT NOT NULL,
                    total_billed_value TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    raw_usage TEXT,
                    anomaly_flag INTEGER NOT NULL DEFAULT 0,
                    anomaly_reason TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS invoice_summaries (
                    customer_id TEXT NOT NULL,
                    period TEXT NOT NULL,
                    total_openrouter_cost TEXT NOT NULL,
                    total_premium_value TEXT NOT NULL,
                    total_billed_value TEXT NOT NULL,
                    usage_count INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    PRIMARY KEY (customer_id, period)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_customer_recorded
                    ON usage_records(customer_id, recorded_at DESC)
                """
            )
            conn.commit()

    def record_usage(self, record: UsageRecord) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO usage_records (
                    usage_id,
                    job_id,
                    customer_id,
                    premium_rate,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    openrouter_cost,
                    premium_value,
                    total_billed_value,
                    currency,
                    recorded_at,
                    raw_usage,
                    anomaly_flag,
                    anomaly_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.usage_id),
                    str(record.job_id),
                    record.customer_id,
                    record.premium_rate,
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,
                    _format_decimal(record.openrouter_cost),
                    _format_decimal(record.premium_value),
                    _format_decimal(record.total_billed),
                    record.currency,
                    record.recorded_at.isoformat(),
                    json.dumps(record.raw_usage, separators=(",", ":")) if record.raw_usage else None,
                    1 if record.anomaly_flag else 0,
                    record.anomaly_reason,
                ),
            )
            period = _month_period(record.recorded_at)
            open_value = record.openrouter_cost or Decimal("0")
            premium_value = record.premium_value
            total_value = record.total_billed
            row = conn.execute(
                "SELECT total_openrouter_cost, total_premium_value, total_billed_value, usage_count, currency"
                "  FROM invoice_summaries WHERE customer_id = ? AND period = ?",
                (record.customer_id, period),
            ).fetchone()
            if row:
                total_open = (_to_decimal(row["total_openrouter_cost"]) or Decimal("0")) + open_value
                total_premium = (_to_decimal(row["total_premium_value"]) or Decimal("0")) + premium_value
                total_billed = (_to_decimal(row["total_billed_value"]) or Decimal("0")) + total_value
                usage_count = int(row["usage_count"]) + 1
                currency = row["currency"] or record.currency
                conn.execute(
                    """
                    UPDATE invoice_summaries
                       SET total_openrouter_cost = ?,
                           total_premium_value = ?,
                           total_billed_value = ?,
                           usage_count = ?,
                           currency = ?,
                           last_updated = ?
                     WHERE customer_id = ? AND period = ?
                    """,
                    (
                        _decimal_to_str(total_open),
                        _decimal_to_str(total_premium),
                        _decimal_to_str(total_billed),
                        usage_count,
                        currency,
                        record.recorded_at.isoformat(),
                        record.customer_id,
                        period,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO invoice_summaries (
                        customer_id,
                        period,
                        total_openrouter_cost,
                        total_premium_value,
                        total_billed_value,
                        usage_count,
                        currency,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.customer_id,
                        period,
                        _decimal_to_str(open_value),
                        _decimal_to_str(premium_value),
                        _decimal_to_str(total_value),
                        1,
                        record.currency,
                        record.recorded_at.isoformat(),
                    ),
                )
            conn.commit()

    def list_usage(
        self,
        customer_id: str,
        *,
        limit: int,
        starting_after: UUID | None = None,
        ending_before: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[UsageRecord]:
        clauses = ["customer_id = ?"]
        params: list[Any] = [customer_id]

        def _cursor_clause(cursor: UUID | None, *, before: bool) -> tuple[str, list[Any]]:
            if cursor is None:
                return "", []
            with self._connection() as cursor_conn:
                row = cursor_conn.execute(
                    "SELECT recorded_at, usage_id FROM usage_records WHERE usage_id = ?",
                    (str(cursor),),
                ).fetchone()
            if row is None:
                return "", []
            recorded = row["recorded_at"]
            usage_id = row["usage_id"]
            comparator = "<" if before else ">"
            clause = f"(recorded_at {comparator} ? OR (recorded_at = ? AND usage_id {comparator} ?))"
            return clause, [recorded, recorded, usage_id]

        if start is not None:
            clauses.append("recorded_at >= ?")
            params.append(start.astimezone(timezone.utc).isoformat())
        if end is not None:
            clauses.append("recorded_at <= ?")
            params.append(end.astimezone(timezone.utc).isoformat())

        cursor_clause, cursor_params = _cursor_clause(starting_after, before=True)
        if cursor_clause:
            clauses.append(cursor_clause)
            params.extend(cursor_params)
        cursor_clause, cursor_params = _cursor_clause(ending_before, before=False)
        if cursor_clause:
            clauses.append(cursor_clause)
            params.extend(cursor_params)

        where = " AND ".join(clauses)
        query = (
            "SELECT usage_id, job_id, customer_id, premium_rate, prompt_tokens, completion_tokens, total_tokens, "
            "openrouter_cost, premium_value, total_billed_value, currency, recorded_at, raw_usage, anomaly_flag, anomaly_reason "
            "FROM usage_records WHERE "
            f"{where} ORDER BY recorded_at DESC, usage_id DESC LIMIT ?"
        )
        params.append(limit)
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        records: list[UsageRecord] = []
        for row in rows:
            records.append(
                UsageRecord(
                    usage_id=UUID(row["usage_id"]),
                    job_id=UUID(row["job_id"]),
                    customer_id=row["customer_id"],
                    premium_rate=float(row["premium_rate"]),
                    prompt_tokens=row["prompt_tokens"],
                    completion_tokens=row["completion_tokens"],
                    total_tokens=row["total_tokens"],
                    openrouter_cost=_to_decimal(row["openrouter_cost"]),
                    premium_value=_to_decimal(row["premium_value"]) or Decimal("0"),
                    total_billed=_to_decimal(row["total_billed_value"]) or Decimal("0"),
                    currency=row["currency"],
                    recorded_at=datetime.fromisoformat(row["recorded_at"]),
                    raw_usage=json.loads(row["raw_usage"]) if row["raw_usage"] else {},
                    anomaly_flag=bool(row["anomaly_flag"]),
                    anomaly_reason=row["anomaly_reason"],
                )
            )
        return records

    def get_invoice(self, customer_id: str, period: str) -> InvoiceSummary | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT customer_id, period, total_openrouter_cost, total_premium_value, total_billed_value, usage_count, currency, last_updated "
                "FROM invoice_summaries WHERE customer_id = ? AND period = ?",
                (customer_id, period),
            ).fetchone()
        if row is None:
            return None
        return InvoiceSummary(
            customer_id=row["customer_id"],
            period=row["period"],
            total_openrouter_cost=_to_decimal(row["total_openrouter_cost"]) or Decimal("0"),
            total_premium_value=_to_decimal(row["total_premium_value"]) or Decimal("0"),
            total_billed_value=_to_decimal(row["total_billed_value"]) or Decimal("0"),
            usage_count=row["usage_count"],
            currency=row["currency"],
            last_updated=datetime.fromisoformat(row["last_updated"]),
        )

    def upsert_invoice(self, summary: InvoiceSummary) -> None:
        payload = (
            summary.customer_id,
            summary.period,
            _decimal_to_str(summary.total_openrouter_cost),
            _decimal_to_str(summary.total_premium_value),
            _decimal_to_str(summary.total_billed_value),
            summary.usage_count,
            summary.currency,
            summary.last_updated.isoformat(),
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO invoice_summaries (
                    customer_id,
                    period,
                    total_openrouter_cost,
                    total_premium_value,
                    total_billed_value,
                    usage_count,
                    currency,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id, period) DO UPDATE SET
                    total_openrouter_cost = excluded.total_openrouter_cost,
                    total_premium_value = excluded.total_premium_value,
                    total_billed_value = excluded.total_billed_value,
                    usage_count = excluded.usage_count,
                    currency = excluded.currency,
                    last_updated = excluded.last_updated
                """,
                payload,
            )
            conn.commit()


class BillingEngine:
    """Apply premium markup, persist usage, and detect anomalies."""

    def __init__(
        self,
        *,
        repository: BillingRepository,
        audit: AuditLogger,
        currency: str = "USD",
        anomaly_threshold: Decimal | None = None,
    ) -> None:
        self._repository = repository
        self._audit = audit
        self._currency = currency
        self._anomaly_threshold = anomaly_threshold or Decimal("50")

    def record_usage(
        self,
        *,
        job: JobRecord,
        usage: dict[str, Any] | None,
        status: JobStatus,
    ) -> dict[str, Any] | None:
        if status is not JobStatus.succeeded or usage is None:
            if status is JobStatus.succeeded and usage is None:
                self._audit.record(
                    "billing.usage.missing",
                    {"job_id": str(job.job_id), "customer_id": job.customer_id},
                )
            return usage
        record = self._build_record(job=job, raw_usage=usage)
        self._repository.record_usage(record)
        event_payload = {
            "job_id": str(job.job_id),
            "customer_id": job.customer_id,
            "usage_id": str(record.usage_id),
            "premium_rate": job.premium_rate,
            "total_billed": _format_decimal(record.total_billed),
            "anomaly": record.anomaly_flag,
        }
        event = "billing.usage.recorded"
        if record.anomaly_flag:
            event = "billing.usage.anomaly"
            event_payload["reason"] = record.anomaly_reason
        self._audit.record(event, event_payload)
        return record.to_job_usage_payload()

    def list_usage(
        self,
        customer_id: str,
        *,
        limit: int = 50,
        starting_after: UUID | None = None,
        ending_before: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, Any]]:
        records = self._repository.list_usage(
            customer_id,
            limit=limit,
            starting_after=starting_after,
            ending_before=ending_before,
            start=start,
            end=end,
        )
        return [record.to_api_payload() for record in records]

    def _build_record(self, *, job: JobRecord, raw_usage: dict[str, Any]) -> UsageRecord:
        prompt_tokens = raw_usage.get("prompt_tokens")
        completion_tokens = raw_usage.get("completion_tokens")
        total_tokens = raw_usage.get("total_tokens")

        openrouter_cost = None
        currency = self._currency
        raw_cost = raw_usage.get("openrouter_cost")
        if isinstance(raw_cost, dict):
            openrouter_cost = _to_decimal(raw_cost.get("value"))
            currency = raw_cost.get("currency") or currency
        elif "total_cost" in raw_usage:
            openrouter_cost = _to_decimal(raw_usage.get("total_cost"))
        elif "cost" in raw_usage:
            openrouter_cost = _to_decimal(raw_usage.get("cost"))

        premium_rate = job.premium_rate
        premium_value = (openrouter_cost or Decimal("0")) * Decimal(str(premium_rate))
        total_billed = (openrouter_cost or Decimal("0")) + premium_value

        provided_total = None
        total_payload = raw_usage.get("total_billed")
        if isinstance(total_payload, dict):
            provided_total = _to_decimal(total_payload.get("value"))

        reasons: list[str] = []
        if openrouter_cost is None:
            reasons.append("missing_openrouter_cost")
        if provided_total is not None:
            diff = (provided_total - total_billed).copy_abs()
            if diff > Decimal("0.0005"):
                reasons.append("total_mismatch")
        if total_billed > self._anomaly_threshold:
            reasons.append("exceeds_threshold")

        anomaly_flag = bool(reasons)
        anomaly_reason = ",".join(reasons) if reasons else None

        return UsageRecord(
            job_id=job.job_id,
            customer_id=job.customer_id,
            premium_rate=premium_rate,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            openrouter_cost=openrouter_cost,
            premium_value=premium_value,
            total_billed=total_billed,
            currency=currency,
            anomaly_flag=anomaly_flag,
            anomaly_reason=anomaly_reason,
            raw_usage=raw_usage,
        )


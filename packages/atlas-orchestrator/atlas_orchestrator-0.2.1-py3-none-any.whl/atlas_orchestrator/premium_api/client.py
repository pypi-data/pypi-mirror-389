"""HTTP client for interacting with the Atlas Orchestrator premium API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import time
from typing import Any, Awaitable, Callable, Iterable, Mapping, MutableMapping, Sequence

import httpx

from .models import JobStatus


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return Decimal(value)
    raise TypeError(f"Unsupported decimal value: {type(value)!r}")


def _maybe_await(callback_result: Awaitable[None] | None) -> Awaitable[None] | None:
    if callback_result is None:
        return None
    if asyncio.iscoroutine(callback_result):
        return callback_result
    return None


@dataclass(frozen=True)
class BillingBreakdown:
    """Structured summary of premium usage charges."""

    premium_rate: float
    premium_value: Decimal
    total_billed_value: Decimal
    currency: str
    openrouter_cost: Decimal | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    anomaly: Mapping[str, Any] | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_usage_payload(cls, payload: Mapping[str, Any]) -> BillingBreakdown:
        premium = payload.get("premium") or {}
        total_billed = payload.get("total_billed") or {}
        openrouter = payload.get("openrouter_cost") or {}
        return cls(
            premium_rate=float(premium.get("rate", 0.0)),
            premium_value=_to_decimal(premium.get("value")) or Decimal("0"),
            total_billed_value=_to_decimal(total_billed.get("value")) or Decimal("0"),
            currency=total_billed.get("currency", "USD"),
            openrouter_cost=_to_decimal(openrouter.get("value")) if openrouter else None,
            prompt_tokens=payload.get("prompt_tokens"),
            completion_tokens=payload.get("completion_tokens"),
            total_tokens=payload.get("total_tokens"),
            anomaly=payload.get("anomaly"),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class JobSubmission:
    job_id: str
    status: JobStatus
    submitted_at: datetime
    poll_after: datetime | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> JobSubmission:
        return cls(
            job_id=str(payload["job_id"]),
            status=JobStatus(payload["status"]),
            submitted_at=_parse_datetime(payload.get("submitted_at")) or datetime.now(timezone.utc),
            poll_after=_parse_datetime(payload.get("poll_after")),
        )


@dataclass(frozen=True)
class JobDetails:
    job_id: str
    status: JobStatus
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    result: Mapping[str, Any] | None = None
    usage: BillingBreakdown | None = None
    error: Mapping[str, Any] | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            JobStatus.succeeded,
            JobStatus.failed,
            JobStatus.cancelled,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> JobDetails:
        usage_payload = payload.get("usage")
        error_payload = payload.get("error")
        metadata = payload.get("metadata") or {}
        return cls(
            job_id=str(payload["job_id"]),
            status=JobStatus(payload["status"]),
            submitted_at=_parse_datetime(payload.get("submitted_at")) or datetime.now(timezone.utc),
            started_at=_parse_datetime(payload.get("started_at")),
            completed_at=_parse_datetime(payload.get("completed_at")),
            metadata=dict(metadata),
            result=payload.get("result"),
            usage=BillingBreakdown.from_usage_payload(usage_payload) if usage_payload else None,
            error=dict(error_payload) if error_payload else None,
        )


@dataclass(frozen=True)
class UsageRecord:
    usage_id: str
    job_id: str
    recorded_at: datetime
    customer_id: str
    charges: BillingBreakdown
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> UsageRecord:
        return cls(
            usage_id=str(payload["usage_id"]),
            job_id=str(payload["job_id"]),
            recorded_at=_parse_datetime(payload.get("recorded_at")) or datetime.now(timezone.utc),
            customer_id=str(payload.get("customer_id", "")),
            charges=BillingBreakdown.from_usage_payload(payload),
            raw=dict(payload),
        )


@dataclass(frozen=True)
class UsagePage:
    records: list[UsageRecord]
    has_more: bool
    next_cursor: str | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> UsagePage:
        records = [UsageRecord.from_payload(item) for item in payload.get("data", [])]
        return cls(
            records=records,
            has_more=bool(payload.get("has_more", False)),
            next_cursor=payload.get("next_cursor"),
        )


@dataclass(frozen=True)
class WebhookDefinition:
    webhook_id: str
    url: str
    events: Sequence[str] | None = None
    secret: str | None = None
    active: bool = True

    def to_payload(self) -> Mapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "id": self.webhook_id,
            "url": self.url,
            "active": self.active,
        }
        if self.secret is not None:
            payload["secret"] = self.secret
        if self.events is not None:
            payload["events"] = list(self.events)
        return payload


@dataclass(frozen=True)
class WebhookInfo:
    webhook_id: str
    url: str
    events: Sequence[str]
    active: bool
    updated_at: datetime

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WebhookInfo:
        return cls(
            webhook_id=str(payload.get("id")),
            url=str(payload.get("url")),
            events=tuple(payload.get("events") or ()),
            active=bool(payload.get("active", True)),
            updated_at=_parse_datetime(payload.get("updated_at")) or datetime.now(timezone.utc),
        )


JobUpdateCallback = Callable[[JobDetails], Awaitable[None] | None]


class PremiumApiClient:
    """Async HTTP client that wraps the premium API endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float | httpx.Timeout | None = None,
        transport: httpx.BaseTransport | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must be provided")
        headers = {"Authorization": f"Bearer {api_key}"}
        if client is not None:
            self._client = client
            self._owns_client = False
            self._client.headers.update(headers)
        else:
            normalized_url = base_url.rstrip("/")
            self._client = httpx.AsyncClient(
                base_url=normalized_url,
                headers=headers,
                timeout=timeout or httpx.Timeout(10.0),
                transport=transport,
            )
            self._owns_client = True

    async def __aenter__(self) -> PremiumApiClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @property
    def base_url(self) -> str:
        return str(self._client.base_url)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def submit_job(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        response_format: Mapping[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        webhook: Mapping[str, Any] | None = None,
    ) -> JobSubmission:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
        }
        if response_format is not None:
            payload["response_format"] = dict(response_format)
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if metadata is not None:
            payload["metadata"] = dict(metadata)
        if webhook is not None:
            payload["webhook"] = dict(webhook)
        response = await self._client.post("/v1/jobs", json=payload)
        response.raise_for_status()
        return JobSubmission.from_payload(response.json())

    async def get_job(self, job_id: str) -> JobDetails:
        response = await self._client.get(f"/v1/jobs/{job_id}")
        response.raise_for_status()
        return JobDetails.from_payload(response.json())

    async def cancel_job(self, job_id: str) -> JobDetails:
        response = await self._client.post(f"/v1/jobs/{job_id}/cancel")
        response.raise_for_status()
        return JobDetails.from_payload(response.json())

    async def upsert_webhooks(
        self,
        definitions: Iterable[WebhookDefinition],
    ) -> list[WebhookInfo]:
        payload = {"webhooks": [definition.to_payload() for definition in definitions]}
        response = await self._client.put("/v1/webhooks", json=payload)
        response.raise_for_status()
        data = response.json().get("webhooks", [])
        return [WebhookInfo.from_payload(item) for item in data]

    async def list_usage(
        self,
        *,
        limit: int = 50,
        starting_after: str | None = None,
        ending_before: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> UsagePage:
        params: dict[str, Any] = {"limit": limit}
        if starting_after is not None:
            params["starting_after"] = starting_after
        if ending_before is not None:
            params["ending_before"] = ending_before
        if from_ts is not None:
            params["from"] = from_ts.astimezone(timezone.utc).isoformat()
        if to_ts is not None:
            params["to"] = to_ts.astimezone(timezone.utc).isoformat()
        response = await self._client.get("/v1/usage", params=params)
        response.raise_for_status()
        return UsagePage.from_payload(response.json())

    async def wait_for_job(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = 300.0,
        on_update: JobUpdateCallback | None = None,
        on_result: JobUpdateCallback | None = None,
    ) -> JobDetails:
        start = time.monotonic()
        while True:
            details = await self.get_job(job_id)
            if on_update is not None:
                maybe = on_update(details)
                awaited = _maybe_await(maybe)
                if awaited is not None:
                    await awaited
            if details.is_terminal:
                if on_result is not None:
                    maybe = on_result(details)
                    awaited = _maybe_await(maybe)
                    if awaited is not None:
                        await awaited
                return details
            if timeout is not None and time.monotonic() - start > timeout:
                raise TimeoutError(f"Timed out waiting for job {job_id}")
            await asyncio.sleep(max(poll_interval, 0.0))

    async def submit_and_wait(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        response_format: Mapping[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, Any] | None = None,
        webhook: Mapping[str, Any] | None = None,
        poll_interval: float = 2.0,
        timeout: float | None = 300.0,
        on_update: JobUpdateCallback | None = None,
        on_result: JobUpdateCallback | None = None,
        respect_poll_after: bool = True,
    ) -> JobDetails:
        submission = await self.submit_job(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
            webhook=webhook,
        )
        if respect_poll_after and submission.poll_after is not None:
            delay = (submission.poll_after - datetime.now(timezone.utc)).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
        return await self.wait_for_job(
            submission.job_id,
            poll_interval=poll_interval,
            timeout=timeout,
            on_update=on_update,
            on_result=on_result,
        )


__all__ = [
    "BillingBreakdown",
    "JobDetails",
    "JobSubmission",
    "PremiumApiClient",
    "UsagePage",
    "UsageRecord",
    "WebhookDefinition",
    "WebhookInfo",
]

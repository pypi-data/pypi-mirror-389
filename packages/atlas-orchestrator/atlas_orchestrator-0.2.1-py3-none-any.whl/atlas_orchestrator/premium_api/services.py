"""Core services supporting the premium API."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from . import observability
from .audit import AuditLogger
from .billing import BillingEngine
from .config import SecuritySettings
from .hashing import KeyHasher
from .jobs import JobRepository
from .models import (
    ApiKeyMaterial,
    ApiKeyRecord,
    CustomerContext,
    JobRecord,
    JobRequestPayload,
    JobResult,
    JobStatus,
    QueueJob,
    RateLimitSettings,
)
from .queue import JobQueue
from .webhooks import WebhookDispatcher


class KeyService:
    """High-level orchestration for issuing and validating API keys."""

    def __init__(
        self,
        *,
        repository: Any,
        hasher: KeyHasher,
        audit: AuditLogger,
        key_prefix: str,
        prefix_length: int,
        default_rate_limit: RateLimitSettings,
        default_premium_rate: float = 0.10,
        security: SecuritySettings | None = None,
    ) -> None:
        self._repository = repository
        self._default_premium_rate = default_premium_rate
        self._hasher = hasher
        self._audit = audit
        self._key_prefix = key_prefix
        self._prefix_length = prefix_length
        self._default_rate_limit = default_rate_limit
        self._security = security

    def issue_key(
        self,
        *,
        customer_id: str,
        plan_tier: str,
        rate_limit: RateLimitSettings | None = None,
        metadata: dict[str, Any] | None = None,
        premium_rate: float | None = None,
    ) -> ApiKeyMaterial:
        metadata = dict(metadata or {})
        key_id = f"key_{uuid4()}"
        if self._security and self._security.request_signing.enabled:
            enforce_signature = metadata.get("require_signature")
            if enforce_signature is None:
                tiers = self._security.request_signing.required_plan_tiers
                enforce_signature = not tiers or plan_tier in tiers
            if enforce_signature:
                metadata["require_signature"] = True
                metadata.setdefault("signing_key_id", key_id)
        material = self._generate_key()
        now = datetime.now(timezone.utc)
        limits = rate_limit or self._default_rate_limit
        markup = premium_rate if premium_rate is not None else self._default_premium_rate
        record = ApiKeyRecord(
            key_id=key_id,
            customer_id=customer_id,
            plan_tier=plan_tier,
            prefix=self._extract_prefix(material),
            hashed_key=self._hasher.hash(material),
            rate_limit_per_minute=limits.per_minute,
            rate_limit_burst=limits.burst,
            premium_rate=markup,
            created_at=now,
            metadata=metadata,
        )
        self._repository.create(record)
        self._audit.record(
            "api_key.issued",
            {
                "key_id": record.key_id,
                "customer_id": customer_id,
                "plan_tier": plan_tier,
                "rate_limit_per_minute": limits.per_minute,
                "rate_limit_burst": limits.burst,
                "premium_rate": markup,
            },
        )
        return ApiKeyMaterial(
            api_key=material,
            prefix=record.prefix,
            customer_id=customer_id,
            plan_tier=plan_tier,
            key_id=record.key_id,
            created_at=now,
        )

    def authenticate(self, api_key: str) -> ApiKeyRecord:
        prefix = self._extract_prefix(api_key)
        record = self._repository.get_by_prefix(prefix)
        if record is None or not record.is_active():
            self._audit.record(
                "api_key.auth.failed",
                {"prefix": prefix, "reason": "unknown"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_api_key",
            )
        if not self._hasher.verify(api_key, record.hashed_key):
            self._audit.record(
                "api_key.auth.failed",
                {"key_id": record.key_id, "customer_id": record.customer_id, "reason": "hash_mismatch"},
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_api_key")
        return record

    def revoke(self, key_id: str) -> None:
        now = datetime.now(timezone.utc)
        self._repository.mark_revoked(key_id, now)
        self._audit.record("api_key.revoked", {"key_id": key_id, "revoked_at": now.isoformat()})

    def customer_context(self, record: ApiKeyRecord) -> CustomerContext:
        metadata = dict(record.metadata)
        requires_signature = bool(metadata.get("require_signature", False))
        if not requires_signature and self._security and self._security.request_signing.enabled:
            tiers = self._security.request_signing.required_plan_tiers
            requires_signature = not tiers or record.plan_tier in tiers
        signing_key_id = metadata.get("signing_key_id")
        if requires_signature and not signing_key_id:
            signing_key_id = record.key_id
        signing_secret = metadata.get("signing_secret")
        ip_allow = tuple(metadata.get("ip_allowlist", [])) if metadata.get("ip_allowlist") else None
        ip_deny = tuple(metadata.get("ip_denylist", [])) if metadata.get("ip_denylist") else None
        return CustomerContext(
            key_id=record.key_id,
            customer_id=record.customer_id,
            plan_tier=record.plan_tier,
            rate_limit=RateLimitSettings(
                per_minute=record.rate_limit_per_minute,
                burst=record.rate_limit_burst,
            ),
            premium_rate=record.premium_rate,
            metadata=metadata,
            requires_signature=requires_signature,
            signing_key_id=signing_key_id,
            signing_secret=signing_secret,
            ip_allowlist=ip_allow,
            ip_denylist=ip_deny,
        )

    def _extract_prefix(self, api_key: str) -> str:
        length = self._prefix_length
        if len(api_key) < length:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_api_key")
        return api_key[:length]

    def _generate_key(self) -> str:
        random_segment = secrets.token_urlsafe(32).replace("-", "").replace("_", "")
        return f"{self._key_prefix}{random_segment}"


class JobService:
    """Coordinates job submission, status inspection, completion, and notifications."""

    def __init__(
        self,
        *,
        repository: JobRepository,
        queue: JobQueue,
        audit: AuditLogger,
        dispatcher: WebhookDispatcher | None = None,
        billing: BillingEngine | None = None,
    ) -> None:
        self._repository = repository
        self._queue = queue
        self._audit = audit
        self._dispatcher = dispatcher
        self._billing = billing

    async def submit(
        self,
        *,
        payload: JobRequestPayload,
        context: CustomerContext,
        webhook: dict[str, object] | None = None,
    ) -> JobRecord:
        now = datetime.now(timezone.utc)
        job_id = uuid4()
        webhook_details = webhook or {}
        record = JobRecord(
            job_id=job_id,
            customer_id=context.customer_id,
            status=JobStatus.pending,
            model=payload.model,
            parameters={
                "temperature": payload.temperature,
                "max_tokens": payload.max_tokens,
                "response_format": payload.response_format,
            },
            metadata=payload.metadata or {},
            request_payload=payload.model_dump(),
            created_at=now,
            webhook_url=webhook_details.get("url"),
            webhook_id=webhook_details.get("id") if webhook_details.get("id") else None,
            webhook_secret=webhook_details.get("secret") if webhook_details.get("secret") else None,
            webhook_events=list(webhook_details.get("events") or []),
            premium_rate=context.premium_rate,
        )
        self._repository.create(record)
        queue_job = QueueJob(
            job_id=job_id,
            customer_id=context.customer_id,
            payload=payload,
            submitted_at=now,
            customer_context=context,
        )
        await self._queue.enqueue(queue_job)
        observability.record_job_submission(context.plan_tier)
        self._audit.record(
            "job.submitted",
            {
                "job_id": str(job_id),
                "customer_id": context.customer_id,
                "plan_tier": context.plan_tier,
                "model": payload.model,
            },
        )
        return record

    def get(self, job_id: UUID) -> JobRecord | None:
        return self._repository.get(job_id)

    def get_result(self, job_id: UUID) -> JobResult | None:
        return self._repository.get_result(job_id)

    def mark_running(self, job_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        self._repository.mark_running(job_id, now)
        self._audit.record("job.running", {"job_id": str(job_id), "started_at": now.isoformat()})

    def cancel(self, job_id: UUID) -> JobRecord:
        record = self._repository.get(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")
        if record.status in {JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cancel_not_allowed")
        now = datetime.now(timezone.utc)
        self._repository.update_status(job_id, JobStatus.cancelled, completed_at=now)
        self._audit.record("job.cancelled", {"job_id": str(job_id), "completed_at": now.isoformat()})
        updated = self._repository.get(job_id)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")
        observability.record_job_completion(JobStatus.cancelled.value)
        return updated

    def complete(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        result: dict | None,
        usage: dict | None,
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        record = self._repository.get(job_id)
        sanitized_usage = usage
        if record and self._billing:
            try:
                sanitized_usage = self._billing.record_usage(
                    job=record,
                    usage=usage,
                    status=status,
                )
            except Exception as exc:  # pragma: no cover - defensive billing guard
                self._audit.record(
                    "billing.usage.error",
                    {
                        "job_id": str(job_id),
                        "customer_id": record.customer_id,
                        "error": str(exc),
                    },
                )
        self._repository.complete(
            job_id,
            status=status,
            result=result,
            usage=sanitized_usage,
            error_code=error_code,
            error_message=error_message,
            completed_at=now,
        )
        observability.record_job_completion(status.value)
        payload = {
            "job_id": str(job_id),
            "status": status.value,
            "completed_at": now.isoformat(),
        }
        if error_code:
            payload["error_code"] = error_code
        self._audit.record("job.completed", payload)
        if self._dispatcher:
            record = self._repository.get(job_id)
            result_payload = self._repository.get_result(job_id)
            self._dispatch_webhook(record, result_payload)

    def _dispatch_webhook(self, record: JobRecord | None, result: JobResult | None) -> None:
        if record is None or not record.webhook_url:
            return
        events = record.webhook_events or []
        event_type = f"job.{record.status.value}"
        if events and event_type not in events:
            return
        payload: dict[str, object] = {
            "event": event_type,
            "job_id": str(record.job_id),
            "status": record.status.value,
            "submitted_at": record.created_at.isoformat(),
        }
        if record.completed_at:
            payload["completed_at"] = record.completed_at.isoformat()
        if result and result.result:
            payload["result"] = result.result  # type: ignore[assignment]
        if result and result.usage:
            payload["usage"] = result.usage  # type: ignore[assignment]
        if result and result.error_code:
            payload["error"] = {
                "code": result.error_code,
                "message": result.error_message,
            }
        self._dispatcher.enqueue(
            url=record.webhook_url,
            secret=record.webhook_secret,
            payload=payload,
        )

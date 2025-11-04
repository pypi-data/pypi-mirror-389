"""Domain models for premium API keys and job processing."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyRecord(BaseModel):
    """Persisted metadata for an issued API key."""

    model_config = ConfigDict(frozen=True)

    key_id: str
    customer_id: str
    plan_tier: str
    prefix: str
    hashed_key: str
    rate_limit_per_minute: int
    rate_limit_burst: int
    created_at: datetime
    rotated_at: datetime | None = None
    revoked_at: datetime | None = None
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    premium_rate: float = 0.10

    def is_active(self) -> bool:
        return self.active and self.revoked_at is None


class ApiKeyMaterial(BaseModel):
    """Plain-text material returned once upon key creation."""

    model_config = ConfigDict(frozen=True)

    api_key: str
    prefix: str
    customer_id: str
    plan_tier: str
    key_id: str
    created_at: datetime


@dataclass(frozen=True)
class RateLimitSettings:
    """Rate limiting constraints for a customer."""

    per_minute: int
    burst: int


@dataclass(frozen=True)
class CustomerContext:
    """Resolved customer context injected into request handlers."""

    key_id: str
    customer_id: str
    plan_tier: str
    rate_limit: RateLimitSettings
    premium_rate: float = 0.10
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_signature: bool = False
    signing_key_id: str | None = None
    signing_secret: str | None = None
    ip_allowlist: tuple[str, ...] | None = None
    ip_denylist: tuple[str, ...] | None = None


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelling = "cancelling"
    cancelled = "cancelled"


class JobRecord(BaseModel):
    """Persisted job metadata."""

    model_config = ConfigDict(frozen=True)

    job_id: UUID
    customer_id: str
    status: JobStatus
    model: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_payload: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    webhook_url: str | None = None
    webhook_id: str | None = None
    webhook_secret: str | None = None
    webhook_events: list[str] | None = None
    premium_rate: float = 0.10


class JobResult(BaseModel):
    """Outcome of a processed job."""

    model_config = ConfigDict(frozen=True)

    job_id: UUID
    status: JobStatus
    result: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


class JobRequestPayload(BaseModel):
    """Incoming job payload from API."""

    model_config = ConfigDict(extra="forbid")

    model: str
    messages: list[dict[str, Any]]
    response_format: dict[str, Any] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] | None = None
    webhook: dict[str, Any] | None = None


class QueueJob(BaseModel):
    """Payload stored in the queue for asynchronous execution."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    job_id: UUID
    customer_id: str
    payload: JobRequestPayload
    submitted_at: datetime
    customer_context: CustomerContext

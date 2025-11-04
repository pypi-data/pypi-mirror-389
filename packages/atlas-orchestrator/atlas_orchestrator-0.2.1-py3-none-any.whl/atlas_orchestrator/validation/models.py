"""Validation domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationCheck(BaseModel):
    """Result of an individual validation check."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: Literal["tests", "semantic"]
    status: Literal["passed", "failed", "skipped"]
    summary: str
    details: str | None = None
    requirement_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationDocument(BaseModel):
    """Structured evaluation record containing validation results."""

    model_config = ConfigDict(extra="forbid")

    draft_id: str
    spec_id: str
    checks: list[ValidationCheck]
    remediation: list[str] = Field(default_factory=list)


class ValidationMetadata(BaseModel):
    """Metadata describing the validation artifact."""

    model_config = ConfigDict(extra="forbid")

    validation_id: str
    status: Literal["passed", "failed", "overridden"]
    draft_id: str
    spec_id: str
    created_at: datetime
    override_reason: str | None = None
    provider: str = Field(default="validation-service")


class ValidationArtifact(BaseModel):
    """Composite validation artifact."""

    model_config = ConfigDict(extra="forbid")

    document: ValidationDocument
    metadata: ValidationMetadata

    def model_dump_with_metadata(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["metadata"]["created_at"] = self.metadata.created_at.isoformat()
        return payload

    @classmethod
    def model_validate_with_metadata(cls, data: dict[str, Any]) -> "ValidationArtifact":
        converted = dict(data)
        metadata = dict(converted.get("metadata", {}))
        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            metadata["created_at"] = datetime.fromisoformat(created_at)
        converted["metadata"] = metadata
        return cls.model_validate(converted)


__all__ = [
    "ValidationArtifact",
    "ValidationCheck",
    "ValidationDocument",
    "ValidationMetadata",
]

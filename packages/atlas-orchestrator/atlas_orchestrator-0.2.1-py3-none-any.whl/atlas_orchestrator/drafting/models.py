"""Drafting domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from atlas_orchestrator.ai.usage import LLMUsage


class ToolResult(BaseModel):
    """Represents the outcome of a tooling step run against a module."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    module_id: str
    status: Literal["ok", "warning", "error"]
    output: str


class DraftModule(BaseModel):
    """Generated draft content for a single module."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    path: str
    language: str
    content: str


class DraftDocument(BaseModel):
    """Holds the full set of modules for a draft artifact."""

    model_config = ConfigDict(extra="forbid")

    spec_id: str
    summary: str
    modules: list[DraftModule]


class DraftMetadata(BaseModel):
    """Metadata describing the draft artifact."""

    model_config = ConfigDict(extra="forbid")

    draft_id: str
    spec_id: str
    version: int
    created_at: datetime
    provider: str
    modules: list[str]
    target_modules: list[str]
    tool_results: list[ToolResult] = Field(default_factory=list)
    validation_status: Literal["pending", "passed", "failed", "overridden"] = Field(default="pending")
    validation_record_id: str | None = None
    validation_override_reason: str | None = None
    usage: LLMUsage | None = None


class DraftArtifact(BaseModel):
    """Composite object bundling draft document and metadata."""

    model_config = ConfigDict(extra="forbid")

    document: DraftDocument
    metadata: DraftMetadata

    def model_dump_with_metadata(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["metadata"]["created_at"] = self.metadata.created_at.isoformat()
        return payload

    @classmethod
    def model_validate_with_metadata(cls, data: dict[str, Any]) -> "DraftArtifact":
        converted = dict(data)
        metadata = dict(converted.get("metadata", {}))
        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            metadata["created_at"] = datetime.fromisoformat(created_at)
        converted["metadata"] = metadata
        return cls.model_validate(converted)


__all__ = [
    "DraftArtifact",
    "DraftDocument",
    "DraftMetadata",
    "DraftModule",
    "ToolResult",
]

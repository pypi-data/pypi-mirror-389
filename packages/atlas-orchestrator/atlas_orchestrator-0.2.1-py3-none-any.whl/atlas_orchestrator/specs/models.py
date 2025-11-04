"""Specification domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from atlas_orchestrator.ai.usage import LLMUsage


class RequirementTrace(BaseModel):
    """Traceability link between module work items and requirements."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    description: str
    source_task_id: str
    section: str | None = None


class ModuleCoverage(BaseModel):
    """Coverage metrics for PRD requirements linked to a module."""

    model_config = ConfigDict(extra="forbid")

    module_id: str
    requirement_ids: list[str]
    sections: list[str]
    total_requirements: int
    status: Literal["covered", "gap"]


class SpecModule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    overview: str
    acceptance_criteria: list[str]
    traces: list[RequirementTrace]


class SpecificationDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    summary: str
    modules: list[SpecModule]
    coverage: list[ModuleCoverage] = Field(default_factory=list)


class SpecificationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_id: str
    plan_id: str
    version: int
    provider: str
    created_at: datetime
    modules: list[str]
    source: str = Field(default="generate")
    parent_spec_id: str | None = None
    usage: LLMUsage | None = None


class SpecificationArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: SpecificationDocument
    metadata: SpecificationMetadata

    def model_dump_with_metadata(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["metadata"]["created_at"] = self.metadata.created_at.isoformat()
        return payload

    @classmethod
    def model_validate_with_metadata(cls, data: dict[str, Any]) -> "SpecificationArtifact":
        converted = dict(data)
        metadata = dict(converted.get("metadata", {}))
        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            metadata["created_at"] = datetime.fromisoformat(created_at)
        converted["metadata"] = metadata
        return cls.model_validate(converted)


__all__ = [
    "ModuleCoverage",
    "RequirementTrace",
    "SpecModule",
    "SpecificationArtifact",
    "SpecificationDocument",
    "SpecificationMetadata",
]

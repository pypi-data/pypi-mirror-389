"""Planning domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from atlas_orchestrator.ai.usage import LLMUsage


class PlanTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    definition_of_done: str


class PlanMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    tasks: list[PlanTask]


class PlanDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str
    summary: str
    milestones: list[PlanMilestone]
    context: str | None = None


class PlanMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(description="Stable identifier for this artifact")
    version: int = Field(default=1)
    provider: str
    created_at: datetime
    source: str = Field(default="create")
    parent_plan_id: str | None = None
    feedback: str | None = None
    usage: LLMUsage | None = None


class PlanArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: PlanDraft
    metadata: PlanMetadata

    def model_dump_with_metadata(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["metadata"]["created_at"] = self.metadata.created_at.isoformat()
        return payload

    @classmethod
    def model_validate_with_metadata(cls, data: dict[str, Any]) -> "PlanArtifact":
        metadata = dict(data.get("metadata", {}))
        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            metadata["created_at"] = datetime.fromisoformat(created_at)
        data = dict(data)
        data["metadata"] = metadata
        return cls.model_validate(data)


__all__ = [
    "PlanArtifact",
    "PlanDraft",
    "PlanMetadata",
    "PlanMilestone",
    "PlanTask",
]


"""Context bundle models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContextBundle(BaseModel):
    """Represents cached context assembled for specification workflows."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    summary: str
    modules: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    plan_revision: float | None = None


__all__ = ["ContextBundle"]

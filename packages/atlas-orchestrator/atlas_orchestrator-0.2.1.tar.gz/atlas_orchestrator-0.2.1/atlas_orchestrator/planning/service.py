"""Planning service implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Callable
from uuid import uuid4

from atlas_orchestrator.ai.base import AIConnector
from atlas_orchestrator.planning.models import PlanArtifact, PlanDraft, PlanMetadata
from atlas_orchestrator.planning.repository import PlanRepository

StreamCallback = Callable[[str], None]


class PlanningService:
    """Application service orchestrating plan generation and persistence."""

    def __init__(
        self,
        *,
        connector: AIConnector,
        repository: PlanRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._connector = connector
        self._repository = repository
        self._clock = clock or datetime.utcnow

    def generate_plan(
        self,
        objective: str,
        *,
        context: str | None = None,
        stream: StreamCallback | None = None,
    ) -> PlanArtifact:
        draft = self._connector.generate_plan(objective, context)
        self._emit_stream(draft, stream)
        artifact = self._build_artifact(
            draft,
            source="create",
            feedback=None,
            parent=None,
            version=1,
        )
        self._remember_provider(artifact.metadata.plan_id, artifact.metadata.provider)
        self._repository.save(artifact)
        return artifact

    def _provider_name(self) -> str:
        name = getattr(self._connector, 'current_provider_name', None)
        if isinstance(name, str) and name:
            return name
        return getattr(self._connector, 'name', 'unknown')

    def _prepare_provider(self, provider: str | None) -> None:
        prepare = getattr(self._connector, 'prepare_for_plan', None)
        if callable(prepare):
            prepare(provider)

    def _remember_provider(self, plan_id: str, provider: str) -> None:
        remember = getattr(self._connector, 'remember_plan', None)
        if callable(remember):
            remember(plan_id, provider)

    def refine_plan(
        self,
        plan_id: str,
        feedback: str,
        *,
        stream: StreamCallback | None = None,
    ) -> PlanArtifact:
        existing = self._repository.load(plan_id)
        self._prepare_provider(existing.metadata.provider)
        refined_draft = self._connector.refine_plan(existing.plan, feedback)
        self._emit_stream(refined_draft, stream)
        artifact = self._build_artifact(
            refined_draft,
            source="refine",
            feedback=feedback,
            parent=existing.metadata.plan_id,
            version=existing.metadata.version + 1,
        )
        self._remember_provider(artifact.metadata.plan_id, artifact.metadata.provider)
        self._repository.save(artifact)
        return artifact

    def _build_artifact(
        self,
        draft: PlanDraft,
        *,
        source: str,
        feedback: str | None,
        parent: str | None,
        version: int,
    ) -> PlanArtifact:
        plan_id = uuid4().hex
        metadata = PlanMetadata(
            plan_id=plan_id,
            version=version,
            provider=self._provider_name(),
            created_at=self._clock(),
            source=source,
            parent_plan_id=parent,
            feedback=feedback,
        )
        return PlanArtifact(plan=draft, metadata=metadata)

    def _emit_stream(self, draft: PlanDraft, stream: StreamCallback | None) -> None:
        if stream is None:
            return
        for chunk in self._connector.summarize_for_stream(draft):
            stream(chunk)


__all__ = ["PlanningService", "StreamCallback"]


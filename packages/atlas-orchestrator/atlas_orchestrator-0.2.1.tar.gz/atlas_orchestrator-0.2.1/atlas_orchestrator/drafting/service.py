"""Drafting service orchestrating generation, tooling, and persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, Sequence
from uuid import uuid4

from atlas_orchestrator.specs import SpecificationRepository
from atlas_orchestrator.workflows import WorkflowExecutionError, WorkflowStateStore

from .generator import DraftGenerator
from .models import DraftArtifact, DraftDocument, DraftMetadata, DraftModule, ToolResult
from .repository import DraftRepository
from .tools import ToolRunner

StreamCallback = Callable[[str], None]


class DraftingService:
    """Generate implementation drafts from specifications."""

    def __init__(
        self,
        *,
        specification_repository: SpecificationRepository,
        repository: DraftRepository,
        generator: DraftGenerator,
        tool_runners: Sequence[ToolRunner],
        state_store: WorkflowStateStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._spec_repository = specification_repository
        self._repository = repository
        self._generator = generator
        self._tool_runners = list(tool_runners)
        self._state_store = state_store
        self._clock = clock or datetime.utcnow

    def generate(
        self,
        spec_id: str,
        *,
        module_ids: Iterable[str] | None = None,
        resume: bool = False,
        stream: StreamCallback | None = None,
    ) -> DraftArtifact:
        spec = self._spec_repository.load(spec_id)
        target_modules = list(module_ids) if module_ids else []
        modules = self._generator.generate_modules(spec.document, target_modules or None)
        if not modules:
            raise ValueError("No modules generated for specification")

        order = [module.id for module in modules]
        state_completed: set[str] = set()
        preserved_modules: dict[str, DraftModule] = {}
        previous_tool_results: list[ToolResult] = []

        if self._state_store is not None:
            state = self._state_store.load("drafting", spec_id)
            state_completed = set(state.get("completed_modules", []))

        if not resume and state_completed and self._state_store is not None:
            self._state_store.clear("drafting", spec_id)
            state_completed.clear()

        latest_artifact = None
        if resume and state_completed:
            latest_artifact = self._latest_draft(spec_id)
            if latest_artifact is not None:
                preserved_modules = {
                    module.id: module
                    for module in latest_artifact.document.modules
                    if module.id in state_completed
                }
                previous_tool_results = list(latest_artifact.metadata.tool_results)
            else:
                state_completed.clear()

        pending_modules = modules if not state_completed else [
            module for module in modules if module.id not in state_completed
        ]

        if resume and not pending_modules and latest_artifact is not None:
            if self._state_store is not None:
                self._state_store.clear("drafting", spec_id)
            self._emit_stream(spec.metadata.plan_id, latest_artifact.document.modules, stream)
            return latest_artifact

        completed = set(state_completed)
        try:
            processed_modules, tool_results = self._run_tools(
                pending_modules,
                spec_id=spec_id,
                completed=completed if pending_modules else None,
            )
        except Exception as exc:  # pragma: no cover - wrapped for resumable workflows
            self._handle_failure(spec_id, completed, exc)

        combined_modules = self._combine_modules(order, processed_modules, preserved_modules)
        all_tool_results = [*previous_tool_results, *tool_results]

        self._emit_stream(spec.metadata.plan_id, combined_modules, stream)

        draft_id = uuid4().hex
        version = self._next_version(spec_id)
        document = DraftDocument(
            spec_id=spec_id,
            summary=self._build_summary(spec_id, combined_modules, resume),
            modules=combined_modules,
        )
        metadata = DraftMetadata(
            draft_id=draft_id,
            spec_id=spec_id,
            version=version,
            created_at=self._clock(),
            provider=self._generator.name,
            modules=[module.id for module in combined_modules],
            target_modules=target_modules or [module.id for module in combined_modules],
            tool_results=all_tool_results,
            validation_status='pending',
            validation_record_id=None,
            validation_override_reason=None,
        )
        artifact = DraftArtifact(document=document, metadata=metadata)
        self._repository.save(artifact)
        if self._state_store is not None:
            self._state_store.clear("drafting", spec_id)
        return artifact

    def load(self, draft_id: str) -> DraftArtifact:
        return self._repository.load(draft_id)

    def list_ids(self) -> Iterable[str]:
        return self._repository.list_ids()

    def _next_version(self, spec_id: str) -> int:
        existing = list(self._repository.list_by_spec(spec_id))
        if not existing:
            return 1
        return max(artifact.metadata.version for artifact in existing) + 1

    def _run_tools(
        self,
        modules: list[DraftModule],
        *,
        spec_id: str | None = None,
        completed: set[str] | None = None,
    ) -> tuple[list[DraftModule], list[ToolResult]]:
        tool_results: list[ToolResult] = []
        transformed: list[DraftModule] = []
        for module in modules:
            current = module
            for tool in self._tool_runners:
                current, result = tool.run(current)
                tool_results.append(result)
            transformed.append(current)
            if spec_id is not None and completed is not None:
                completed.add(current.id)
                self._persist_progress(spec_id, completed)
        return transformed, tool_results

    def _emit_stream(
        self,
        plan_id: str,
        modules: Sequence[DraftModule],
        stream: StreamCallback | None,
    ) -> None:
        if stream is None:
            return
        stream(f"plan={plan_id} modules={len(modules)}")
        for module in modules:
            stream(f"module={module.id} path={module.path}")

    def _persist_progress(self, spec_id: str, completed: set[str]) -> None:
        if self._state_store is None:
            return
        self._state_store.update(
            "drafting",
            spec_id,
            {"completed_modules": sorted(completed)},
        )

    def _handle_failure(self, spec_id: str, completed: set[str], error: Exception) -> None:
        if self._state_store is not None:
            self._state_store.update(
                "drafting",
                spec_id,
                {"completed_modules": sorted(completed)},
            )
        raise WorkflowExecutionError(
            "drafting",
            spec_id,
            f"Draft generation failed for spec {spec_id}",
            resume_available=self._state_store is not None,
            cause=error,
        ) from error

    def _combine_modules(
        self,
        order: list[str],
        new_modules: list[DraftModule],
        preserved_modules: dict[str, DraftModule],
    ) -> list[DraftModule]:
        mapping = {module.id: module for module in new_modules}
        combined: list[DraftModule] = []
        for module_id in order:
            if module_id in mapping:
                combined.append(mapping[module_id])
            elif module_id in preserved_modules:
                combined.append(preserved_modules[module_id])
        return combined

    def _latest_draft(self, spec_id: str) -> DraftArtifact | None:
        latest: DraftArtifact | None = None
        for artifact in self._repository.list_by_spec(spec_id):
            if latest is None or artifact.metadata.version > latest.metadata.version:
                latest = artifact
        return latest

    def _build_summary(
        self,
        spec_id: str,
        modules: Sequence[DraftModule],
        resume: bool,
    ) -> str:
        summary = f"Draft for spec {spec_id} covering modules: {', '.join(module.id for module in modules)}"
        if resume:
            summary += " (resumed)"
        return summary


__all__ = ["DraftingService", "StreamCallback"]

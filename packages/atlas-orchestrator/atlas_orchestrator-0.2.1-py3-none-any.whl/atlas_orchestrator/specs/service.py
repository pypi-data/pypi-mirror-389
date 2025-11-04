"""Specification service orchestrating context and generation."""

from __future__ import annotations

import difflib
from datetime import datetime
from typing import Callable, Iterable, Sequence
from uuid import uuid4

from atlas_orchestrator.context import ContextBuilder
from atlas_orchestrator.planning import PlanRepository

from .generator import SpecificationGenerator
from .models import SpecificationArtifact, SpecificationDocument, SpecificationMetadata
from .repository import SpecificationRepository

StreamCallback = Callable[[str], None]


class SpecificationCoverageError(RuntimeError):
    """Raised when specification generation lacks required PRD coverage."""

    def __init__(self, missing_modules: Sequence[str]) -> None:
        message = "Missing PRD coverage for modules: " + ", ".join(sorted(missing_modules))
        super().__init__(message)
        self.missing_modules = list(missing_modules)


class SpecificationService:
    """Generates, persists, and inspects specification artifacts."""

    def __init__(
        self,
        *,
        plan_repository: PlanRepository,
        repository: SpecificationRepository,
        context_builder: ContextBuilder,
        generator: SpecificationGenerator,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._plan_repository = plan_repository
        self._repository = repository
        self._context_builder = context_builder
        self._generator = generator
        self._clock = clock or datetime.utcnow

    def generate(
        self,
        plan_id: str,
        *,
        module_id: str | None = None,
        stream: StreamCallback | None = None,
        force_refresh: bool = False,
    ) -> SpecificationArtifact:
        plan = self._plan_repository.load(plan_id)
        context = self._context_builder.build(plan_id, force_refresh=force_refresh)
        document = self._generator.generate_document(plan, context, module_id)
        gaps = [entry.module_id for entry in document.coverage if entry.status == "gap"]
        if gaps:
            raise SpecificationCoverageError(gaps)
        self._emit_stream(document, stream)
        spec_id = uuid4().hex
        version = self._next_version(plan_id)
        metadata = SpecificationMetadata(
            spec_id=spec_id,
            plan_id=plan.metadata.plan_id,
            version=version,
            provider=self._generator.name,
            created_at=self._clock(),
            modules=[module.id for module in document.modules],
        )
        artifact = SpecificationArtifact(document=document, metadata=metadata)
        self._repository.save(artifact)
        return artifact

    def load(
        self,
        spec_id: str,
        *,
        sections: Iterable[str] | None = None,
    ) -> SpecificationArtifact:
        artifact = self._repository.load(spec_id)
        if sections:
            filtered = _filter_document_sections(artifact.document, sections)
            return artifact.model_copy(update={"document": filtered})
        return artifact

    def list_ids(self) -> Iterable[str]:
        return self._repository.list_ids()

    def diff(
        self,
        first_spec: str,
        second_spec: str,
        *,
        sections: Iterable[str] | None = None,
    ) -> list[str]:
        first = self._repository.load(first_spec)
        second = self._repository.load(second_spec)
        first_doc = first.document
        second_doc = second.document
        if sections:
            first_doc = _filter_document_sections(first_doc, sections)
            second_doc = _filter_document_sections(second_doc, sections)
        first_payload = first_doc.model_dump()
        second_payload = second_doc.model_dump()
        first_lines = _to_lines(first_payload)
        second_lines = _to_lines(second_payload)
        return list(
            difflib.unified_diff(
                first_lines,
                second_lines,
                fromfile=f"spec:{first_spec}",
                tofile=f"spec:{second_spec}",
                lineterm="",
            )
        )

    def _next_version(self, plan_id: str) -> int:
        existing = list(self._repository.list_by_plan(plan_id))
        if not existing:
            return 1
        return max(artifact.metadata.version for artifact in existing) + 1

    def _emit_stream(
        self,
        document: SpecificationDocument,
        stream: StreamCallback | None,
    ) -> None:
        if stream is None:
            return
        stream(document.summary)
        for module in document.modules:
            stream(
                "module="
                f"{module.id} title={module.title} sections="
                f"{','.join(sorted({trace.section or 'task' for trace in module.traces if trace.section})) or 'n/a'}"
            )


def _filter_document_sections(
    document: SpecificationDocument,
    sections: Iterable[str],
) -> SpecificationDocument:
    normalized = {section.lower() for section in sections if section}
    if not normalized:
        return document
    modules = []
    for module in document.modules:
        filtered_traces = [
            trace
            for trace in module.traces
            if trace.section and trace.section.lower() in normalized
        ]
        if filtered_traces:
            modules.append(module.model_copy(update={"traces": filtered_traces}))
    coverage = [
        entry
        for entry in document.coverage
        if entry.sections
        and any(section.lower() in normalized for section in entry.sections)
    ]
    return document.model_copy(update={"modules": modules, "coverage": coverage})


def _to_lines(payload: dict[str, object]) -> list[str]:
    import json

    return json.dumps(payload, indent=2, sort_keys=True).splitlines()


__all__ = [
    "SpecificationCoverageError",
    "SpecificationService",
    "StreamCallback",
]

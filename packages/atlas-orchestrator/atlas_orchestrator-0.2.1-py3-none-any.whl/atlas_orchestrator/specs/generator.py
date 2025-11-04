"""Deterministic specification generator with requirement enrichment."""

from __future__ import annotations

from collections.abc import Iterable

from atlas_orchestrator.context import ContextBundle
from atlas_orchestrator.planning import PlanArtifact
from atlas_orchestrator.planning.models import PlanTask

from .models import ModuleCoverage, RequirementTrace, SpecificationDocument, SpecModule
from .requirements import Requirement, RequirementsCatalog


class SpecificationGenerator:
    """Produce structured specification modules from plan artifacts."""

    name = "openrouter-spec"

    def __init__(
        self,
        *,
        requirements: RequirementsCatalog | None = None,
    ) -> None:
        self._requirements = requirements

    def generate_document(
        self,
        plan: PlanArtifact,
        context: ContextBundle,
        module_id: str | None = None,
    ) -> SpecificationDocument:
        milestones = plan.plan.milestones
        modules: list[SpecModule] = []
        coverage: list[ModuleCoverage] = []
        for milestone in milestones:
            if module_id and milestone.id != module_id:
                continue
            task_traces = [
                RequirementTrace(
                    requirement_id=f"REQ-{task.id}",
                    description=task.description,
                    source_task_id=task.id,
                )
                for task in milestone.tasks
            ]
            requirements = self._select_requirements(
                milestone.title,
                milestone.description,
                milestone.tasks,
            )
            requirement_traces = [
                RequirementTrace(
                    requirement_id=requirement.id,
                    description=requirement.text,
                    source_task_id=f"doc:{_slugify(requirement.section)}",
                    section=requirement.section,
                )
                for requirement in requirements
            ]
            acceptance = [
                (
                    f"{task.title} produces verifiable output aligned with "
                    f"{task.definition_of_done.lower()}"
                )
                for task in milestone.tasks
            ]
            modules.append(
                SpecModule(
                    id=milestone.id,
                    title=milestone.title,
                    overview=(
                        "Module for "
                        f"{milestone.title} derived from objective '{plan.plan.objective}'. "
                        f"Context summary: {context.summary}"
                    ),
                    acceptance_criteria=acceptance,
                    traces=task_traces + requirement_traces,
                )
            )
            coverage.append(
                ModuleCoverage(
                    module_id=milestone.id,
                    requirement_ids=[requirement.id for requirement in requirements],
                    sections=sorted({
                        requirement.section
                        for requirement in requirements
                        if requirement.section
                    }),
                    total_requirements=len(requirements),
                    status="covered" if requirements else "gap",
                )
            )
        summary = (
            f"Specification for plan '{plan.plan.objective}' covering modules: "
            f"{', '.join(module.id for module in modules)}"
        )
        return SpecificationDocument(
            plan_id=plan.metadata.plan_id,
            summary=summary,
            modules=modules,
            coverage=coverage,
        )

    def _select_requirements(
        self,
        title: str,
        description: str,
        tasks: Iterable[PlanTask],
    ) -> list[Requirement]:
        if self._requirements is None:
            return []
        keywords = [title, description] + [task.title for task in tasks]
        return self._requirements.find_related(keywords, limit=None)


def _slugify(text: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


__all__ = ["SpecificationGenerator"]

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from atlas_orchestrator.ai.openrouter import OpenRouterConnector
from atlas_orchestrator.context import ContextBuilder, ContextCache
from atlas_orchestrator.planning import PlanRepository
from atlas_orchestrator.planning.service import PlanningService
from atlas_orchestrator.specs.generator import SpecificationGenerator
from atlas_orchestrator.specs.repository import SpecificationRepository
from atlas_orchestrator.specs.requirements import Requirement, RequirementsCatalog
from atlas_orchestrator.specs.service import SpecificationCoverageError, SpecificationService


def _build_spec_service(
    tmp_path: Path,
    requirements: RequirementsCatalog | None = None,
) -> tuple[SpecificationService, str, Path]:
    workspace = ".atlas_orchestrator"
    plan_repo = PlanRepository(project_root=tmp_path, workspace=workspace)
    planning_service = PlanningService(connector=OpenRouterConnector(), repository=plan_repo)
    plan_artifact = planning_service.generate_plan("Deliver automation")

    cache = ContextCache(tmp_path / workspace / "cache" / "context")
    context_builder = ContextBuilder(repository=plan_repo, cache=cache)
    spec_repo = SpecificationRepository(project_root=tmp_path, workspace=workspace)
    requirements_catalog = requirements or RequirementsCatalog(
        [
            Requirement(
                id="PRD::analysis::1",
                section="Analysis",
                text="Include telemetry instrumentation for automation workflows.",
            ),
            Requirement(
                id="PRD::design::1",
                section="Design",
                text="Provide modular architecture guidance for automation milestones.",
            ),
            Requirement(
                id="PRD::implementation::1",
                section="Implementation",
                text="Embed validation harnesses for generated automation code.",
            ),
        ]
    )
    spec_service = SpecificationService(
        plan_repository=plan_repo,
        repository=spec_repo,
        context_builder=context_builder,
        generator=SpecificationGenerator(requirements=requirements_catalog),
        clock=lambda: datetime(2025, 1, 1),
    )
    specs_dir = tmp_path / workspace / "specs"
    return spec_service, plan_artifact.metadata.plan_id, specs_dir


def test_generate_specification_persists_artifact(tmp_path: Path) -> None:
    spec_service, plan_id, specs_dir = _build_spec_service(tmp_path)

    streamed: list[str] = []
    artifact = spec_service.generate(plan_id, stream=streamed.append)

    assert streamed[0].startswith("Specification for plan")
    assert (specs_dir / f"{artifact.metadata.spec_id}.json").exists()
    assert artifact.metadata.version == 1
    assert artifact.document.modules
    coverage = {entry.module_id: entry for entry in artifact.document.coverage}
    assert set(coverage) == set(artifact.metadata.modules)
    assert all(entry.status == "covered" for entry in coverage.values())
    doc_traces = [
        trace
        for trace in artifact.document.modules[0].traces
        if trace.source_task_id.startswith("doc:")
    ]
    assert doc_traces


def test_generate_specification_fails_when_prd_gaps_exist(tmp_path: Path) -> None:
    gap_catalog = RequirementsCatalog([])
    spec_service, plan_id, _ = _build_spec_service(tmp_path, requirements=gap_catalog)

    with pytest.raises(SpecificationCoverageError) as excinfo:
        spec_service.generate(plan_id)

    assert "Missing PRD coverage" in str(excinfo.value)
    assert "analysis" in ",".join(excinfo.value.missing_modules)


def test_diff_between_spec_versions(tmp_path: Path) -> None:
    spec_service, plan_id, _ = _build_spec_service(tmp_path)
    first = spec_service.generate(plan_id)
    second = spec_service.generate(plan_id, module_id=first.metadata.modules[0])

    assert second.metadata.version == first.metadata.version + 1

    diff = spec_service.diff(first.metadata.spec_id, second.metadata.spec_id)
    assert diff

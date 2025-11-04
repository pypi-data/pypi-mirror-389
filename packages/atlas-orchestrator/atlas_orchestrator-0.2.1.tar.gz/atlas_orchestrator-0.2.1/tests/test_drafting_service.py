from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from atlas_orchestrator.ai import OpenRouterConnector
from atlas_orchestrator.context import ContextBuilder, ContextCache
from atlas_orchestrator.drafting import (
    DraftGenerator,
    DraftRepository,
    DraftingService,
    FormatterToolRunner,
    LinterToolRunner,
    ToolResult,
    ToolRunner,
)
from atlas_orchestrator.planning import PlanRepository
from atlas_orchestrator.planning.service import PlanningService
from atlas_orchestrator.specs.generator import SpecificationGenerator
from atlas_orchestrator.specs.repository import SpecificationRepository
from atlas_orchestrator.specs.requirements import Requirement, RequirementsCatalog
from atlas_orchestrator.specs.service import SpecificationService
from atlas_orchestrator.workflows import WorkflowExecutionError, WorkflowStateStore

WORKSPACE = ".atlas_orchestrator"


def _build_spec_infrastructure(tmp_path: Path) -> tuple[SpecificationRepository, SpecificationService, str]:
    plan_repo = PlanRepository(project_root=tmp_path, workspace=WORKSPACE)
    planning_service = PlanningService(connector=OpenRouterConnector(), repository=plan_repo)
    plan_artifact = planning_service.generate_plan("Deliver analytics platform")

    cache = ContextCache(tmp_path / WORKSPACE / "cache" / "context")
    context_builder = ContextBuilder(repository=plan_repo, cache=cache)
    spec_repo = SpecificationRepository(project_root=tmp_path, workspace=WORKSPACE)
    requirements = RequirementsCatalog(
        [
            Requirement(
                id="PRD::analysis::1",
                section="Analysis",
                text="Cover discovery activities with traceability to analytics objectives.",
            ),
            Requirement(
                id="PRD::design::1",
                section="Design",
                text="Document architecture decisions for analytics modules.",
            ),
            Requirement(
                id="PRD::implementation::1",
                section="Implementation",
                text="Include validation checkpoints for generated analytics code.",
            ),
        ]
    )
    generator = SpecificationGenerator(requirements=requirements)
    spec_service = SpecificationService(
        plan_repository=plan_repo,
        repository=spec_repo,
        context_builder=context_builder,
        generator=generator,
        clock=lambda: datetime(2025, 1, 1),
    )
    spec_artifact = spec_service.generate(plan_artifact.metadata.plan_id)
    return spec_repo, spec_service, spec_artifact.metadata.spec_id


def _build_drafting_service(
    tmp_path: Path,
    spec_repo: SpecificationRepository,
    *,
    tools: list[ToolRunner] | None = None,
) -> DraftingService:
    draft_repo = DraftRepository(project_root=tmp_path, workspace=WORKSPACE)
    generator = DraftGenerator()
    tool_runners = tools or [FormatterToolRunner(), LinterToolRunner()]
    state_store = WorkflowStateStore(tmp_path / WORKSPACE / "state")
    return DraftingService(
        specification_repository=spec_repo,
        repository=draft_repo,
        generator=generator,
        tool_runners=tool_runners,
        state_store=state_store,
        clock=lambda: datetime(2025, 1, 2),
    )


def test_generate_draft_persists_and_runs_tooling(tmp_path: Path) -> None:
    spec_repo, _, spec_id = _build_spec_infrastructure(tmp_path)
    drafting_service = _build_drafting_service(tmp_path, spec_repo)

    artifact = drafting_service.generate(spec_id)

    assert artifact.metadata.draft_id
    assert artifact.metadata.version == 1
    assert artifact.metadata.modules
    assert len(artifact.metadata.tool_results) == len(artifact.metadata.modules) * 2
    generated_dir = tmp_path / "generated" / artifact.metadata.draft_id
    for module in artifact.document.modules:
        file_path = generated_dir / module.path
        assert file_path.exists()
        payload = file_path.read_text(encoding="utf-8")
        assert "=== Atlas Orchestrator GENERATED CODE ===" in payload
        assert "# Requirements Context:" in payload
        assert "trace_ids = [" in payload


def test_generate_draft_supports_targeted_modules(tmp_path: Path) -> None:
    spec_repo, _, spec_id = _build_spec_infrastructure(tmp_path)
    drafting_service = _build_drafting_service(tmp_path, spec_repo)
    first = drafting_service.generate(spec_id)

    target_module = first.metadata.modules[0]
    second = drafting_service.generate(spec_id, module_ids=[target_module])

    assert second.metadata.version == first.metadata.version + 1
    assert second.metadata.modules == [target_module]
    assert second.metadata.target_modules == [target_module]


def test_generate_draft_with_unknown_module(tmp_path: Path) -> None:
    spec_repo, _, spec_id = _build_spec_infrastructure(tmp_path)
    drafting_service = _build_drafting_service(tmp_path, spec_repo)

    with pytest.raises(ValueError):
        drafting_service.generate(spec_id, module_ids=["unknown"])


def test_generate_draft_resume_after_failure(tmp_path: Path) -> None:
    spec_repo, _, spec_id = _build_spec_infrastructure(tmp_path)
    spec_artifact = spec_repo.load(spec_id)
    modules = DraftGenerator().generate_modules(spec_artifact.document)
    fail_module = modules[1].id if len(modules) > 1 else modules[0].id

    class FlakyTool(ToolRunner):
        name = "flaky"

        def __init__(self, fail_on: str) -> None:
            self._fail_on = fail_on
            self._failed = False

        def run(self, module):  # type: ignore[override]
            if module.id == self._fail_on and not self._failed:
                self._failed = True
                raise RuntimeError("simulated failure")
            return module, ToolResult(tool=self.name, module_id=module.id, status="ok", output="ok")

    flaky = FlakyTool(fail_on=fail_module)
    tools = [FormatterToolRunner(), flaky, LinterToolRunner()]
    drafting_service = _build_drafting_service(tmp_path, spec_repo, tools=tools)

    with pytest.raises(WorkflowExecutionError) as exc:
        drafting_service.generate(spec_id)
    assert exc.value.resume_available is True

    state_store = WorkflowStateStore(tmp_path / WORKSPACE / "state")
    state = state_store.load("drafting", spec_id)
    assert state.get("completed_modules")
    assert fail_module not in state.get("completed_modules", [])

    resumed = drafting_service.generate(spec_id, resume=True)

    assert resumed.metadata.version == 1
    assert "(resumed)" in resumed.document.summary
    assert state_store.load("drafting", spec_id) == {}
    assert len(resumed.metadata.tool_results) == len(resumed.metadata.modules) * 3

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from atlas_orchestrator.ai import AnthropicConnector, FallbackConnector, OpenRouterConnector
from atlas_orchestrator.planning.repository import PlanRepository
from atlas_orchestrator.planning.service import PlanningService


def test_generate_plan_persists_artifact(tmp_path: Path) -> None:
    repo = PlanRepository(project_root=tmp_path, workspace=".atlas_orchestrator")
    connector = OpenRouterConnector()
    service = PlanningService(
        connector=connector,
        repository=repo,
        clock=lambda: datetime(2025, 1, 1),
    )

    streamed: list[str] = []
    artifact = service.generate_plan("Deliver feature", stream=streamed.append)

    assert streamed
    assert artifact.metadata.plan_id in list(repo.list_ids())
    path = repo.plans_dir / f"{artifact.metadata.plan_id}.json"
    assert path.exists()


def test_refine_plan_creates_new_version(tmp_path: Path) -> None:
    repo = PlanRepository(project_root=tmp_path, workspace=".atlas_orchestrator")
    connector = OpenRouterConnector()
    service = PlanningService(
        connector=connector,
        repository=repo,
        clock=lambda: datetime(2025, 1, 1),
    )

    original = service.generate_plan("Improve reliability")
    refined = service.refine_plan(original.metadata.plan_id, "Add chaos testing")

    assert refined.metadata.parent_plan_id == original.metadata.plan_id
    assert refined.metadata.version == original.metadata.version + 1
    assert refined.metadata.plan_id in list(repo.list_ids())
    assert original.metadata.plan_id in list(repo.list_ids())
    assert refined.plan.milestones[0].tasks[-1].title == "Integrate feedback"


def test_planning_service_records_fallback_provider(tmp_path: Path) -> None:
    repo = PlanRepository(project_root=tmp_path, workspace=".atlas_orchestrator")
    fallback = FallbackConnector([AnthropicConnector(inject_failure=True), OpenRouterConnector()])
    service = PlanningService(
        connector=fallback,
        repository=repo,
        clock=lambda: datetime(2025, 1, 1),
    )

    artifact = service.generate_plan("Handle fallback")
    assert artifact.metadata.provider == "openrouter"

    refined = service.refine_plan(artifact.metadata.plan_id, "Iterate")
    assert refined.metadata.provider == "openrouter"

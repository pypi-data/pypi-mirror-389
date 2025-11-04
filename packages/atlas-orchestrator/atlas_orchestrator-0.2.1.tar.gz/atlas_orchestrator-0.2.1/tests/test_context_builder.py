from __future__ import annotations

import json
from pathlib import Path

from atlas_orchestrator.ai.openrouter import OpenRouterConnector
from atlas_orchestrator.context import ContextBuilder, ContextCache
from atlas_orchestrator.planning import PlanRepository
from atlas_orchestrator.planning.service import PlanningService


def test_context_builder_caches_results(tmp_path: Path) -> None:
    plan_repo = PlanRepository(project_root=tmp_path, workspace=".atlas_orchestrator")
    service = PlanningService(connector=OpenRouterConnector(), repository=plan_repo)
    artifact = service.generate_plan("Launch analytics")

    cache = ContextCache(tmp_path / ".atlas_orchestrator" / "cache" / "context")
    builder = ContextBuilder(repository=plan_repo, cache=cache)

    first = builder.build(artifact.metadata.plan_id)
    assert first.plan_id == artifact.metadata.plan_id
    plan_path = plan_repo.plans_dir / f"{artifact.metadata.plan_id}.json"
    plan_path.unlink()

    second = builder.build(artifact.metadata.plan_id)
    assert second.plan_id == first.plan_id
    assert second.summary == first.summary


def test_context_builder_refreshes_when_plan_changes(tmp_path: Path) -> None:
    plan_repo = PlanRepository(project_root=tmp_path, workspace=".atlas_orchestrator")
    service = PlanningService(connector=OpenRouterConnector(), repository=plan_repo)
    artifact = service.generate_plan("Launch analytics")

    cache = ContextCache(tmp_path / ".atlas_orchestrator" / "cache" / "context")
    builder = ContextBuilder(repository=plan_repo, cache=cache)

    first = builder.build(artifact.metadata.plan_id)

    plan_path = plan_repo.path_for(artifact.metadata.plan_id)
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    data["plan"]["summary"] = "Updated summary for cache invalidation"
    plan_path.write_text(json.dumps(data), encoding="utf-8")

    second = builder.build(artifact.metadata.plan_id)
    assert second.summary == "Updated summary for cache invalidation"
    assert second.plan_revision is not None
    assert second.plan_revision >= first.plan_revision or first.plan_revision is None



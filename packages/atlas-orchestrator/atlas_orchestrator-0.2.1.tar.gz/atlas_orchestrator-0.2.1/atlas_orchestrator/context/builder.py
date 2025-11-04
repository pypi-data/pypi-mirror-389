"""Context builder that assembles summaries for specification workflows."""

from __future__ import annotations

from atlas_orchestrator.planning import PlanRepository

from .cache import ContextCache
from .models import ContextBundle


class ContextBuilder:
    """Builds and caches contextual summaries derived from plan artifacts."""

    def __init__(self, *, repository: PlanRepository, cache: ContextCache) -> None:
        self._repository = repository
        self._cache = cache

    def build(self, plan_id: str, *, force_refresh: bool = False) -> ContextBundle:
        plan_path = self._repository.path_for(plan_id)
        plan_revision = plan_path.stat().st_mtime if plan_path.exists() else None
        if force_refresh:
            self._cache.invalidate(plan_id)
        if not force_refresh:
            cached = self._cache.get(plan_id)
            if cached and plan_revision is not None and cached.plan_revision is not None:
                if cached.plan_revision >= plan_revision:
                    return cached
            elif cached and plan_revision is None:
                return cached
        artifact = self._repository.load(plan_id)
        summary = artifact.plan.summary
        modules = [milestone.title for milestone in artifact.plan.milestones]
        if plan_revision is None and plan_path.exists():
            plan_revision = plan_path.stat().st_mtime
        bundle = ContextBundle(
            plan_id=plan_id,
            summary=summary,
            modules=modules,
            plan_revision=plan_revision,
        )
        self._cache.set(bundle)
        return bundle


__all__ = ["ContextBuilder"]

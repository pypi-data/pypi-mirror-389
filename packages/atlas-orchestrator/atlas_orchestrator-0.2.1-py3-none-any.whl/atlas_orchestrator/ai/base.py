"""Base interfaces for AI connectors."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from atlas_orchestrator.planning.models import PlanDraft


@runtime_checkable
class AIConnector(Protocol):
    """Protocol all AI planning connectors must implement."""

    name: str

    def generate_plan(self, objective: str, context: str | None = None) -> "PlanDraft":
        """Generate an initial plan for the supplied objective."""

    def refine_plan(self, draft: "PlanDraft", feedback: str) -> "PlanDraft":
        """Return a refined draft by applying human feedback."""

    def summarize_for_stream(self, draft: "PlanDraft") -> Iterable[str]:
        """Yield human readable chunks for CLI streaming."""


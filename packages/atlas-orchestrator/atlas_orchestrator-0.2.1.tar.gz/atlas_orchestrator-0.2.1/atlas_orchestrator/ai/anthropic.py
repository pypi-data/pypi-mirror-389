"""Anthropic AI connector stub for planning workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from atlas_orchestrator.ai.exceptions import AIProviderError
from atlas_orchestrator.planning.models import PlanDraft, PlanMilestone, PlanTask


@dataclass(frozen=True)
class _AnthropicMilestone:
    identifier: str
    title: str
    emphasis: str


class AnthropicConnector:
    """Deterministic stub emulating an Anthropic planning connector."""

    name = "anthropic"
    _MILESTONES = (
        _AnthropicMilestone(
            identifier="context",
            title="Context Framing",
            emphasis="stakeholder alignment and context capture",
        ),
        _AnthropicMilestone(
            identifier="strategy",
            title="Strategic Blueprint",
            emphasis="system design boundaries and API contracts",
        ),
        _AnthropicMilestone(
            identifier="execution",
            title="Execution Path",
            emphasis="risk-driven implementation tactics",
        ),
    )

    def __init__(self, *, model: str = "claude-3-sonnet", inject_failure: bool = False) -> None:
        self.model = model
        self._inject_failure = inject_failure

    def generate_plan(self, objective: str, context: str | None = None) -> PlanDraft:
        self._maybe_fail("generate", objective)
        milestones = [self._build_milestone(template, objective) for template in self._MILESTONES]
        summary = self._build_summary(objective, context)
        return PlanDraft(objective=objective, summary=summary, milestones=milestones, context=context)

    def refine_plan(self, draft: PlanDraft, feedback: str) -> PlanDraft:
        self._maybe_fail("refine", feedback)
        refined_milestones = []
        for milestone in draft.milestones:
            refined_milestones.append(
                PlanMilestone(
                    id=milestone.id,
                    title=milestone.title,
                    description=f"{milestone.description} Feedback: {feedback.strip()}.",
                    tasks=[
                        *milestone.tasks,
                        PlanTask(
                            id=f"{milestone.id}-alignment",
                            title="Feedback alignment",
                            description=f"Incorporate feedback '{feedback.strip()}' into {milestone.title} decisions.",
                            definition_of_done="Feedback addressed in acceptance notes.",
                        ),
                    ],
                )
            )
        return PlanDraft(
            objective=draft.objective,
            summary=f"{draft.summary} Updated with: {feedback.strip()}.",
            milestones=refined_milestones,
            context=draft.context,
        )

    def summarize_for_stream(self, draft: PlanDraft) -> Iterable[str]:
        yield f"objective={draft.objective} model={self.model}"
        for milestone in draft.milestones:
            yield f"milestone={milestone.id} tasks={len(milestone.tasks)}"

    def _maybe_fail(self, operation: str, trigger: str) -> None:
        if self._inject_failure:
            raise AIProviderError(self.name, f"Anthropic simulated failure during {operation} for '{trigger}'")

    def _build_milestone(self, template: _AnthropicMilestone, objective: str) -> PlanMilestone:
        tasks = [
            PlanTask(
                id=f"{template.identifier}-{index}",
                title=f"Frame {template.emphasis.split()[0]} #{index}",
                description=(
                    f"{template.title} task {index} for {objective} focusing on {template.emphasis}."
                ),
                definition_of_done="Reviewed with wider program team.",
            )
            for index in range(1, 3)
        ]
        return PlanMilestone(
            id=template.identifier,
            title=template.title,
            description=f"{template.title} emphasises {template.emphasis}.",
            tasks=tasks,
        )

    def _build_summary(self, objective: str, context: str | None) -> str:
        base = f"Deliver an actionable programme for '{objective}' using deliberate alignment."
        if context:
            return f"{base} Context notes: {context.strip()}"
        return base


__all__ = ["AnthropicConnector"]

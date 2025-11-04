"""OpenRouter AI connector stub for planning workflows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, Mapping

from atlas_orchestrator.planning.models import PlanDraft, PlanMilestone, PlanTask


@dataclass(frozen=True)
class _MilestoneTemplate:
    identifier: str
    title: str
    focus: str


class OpenRouterConnector:
    """Deterministic stub emulating an OpenRouter planning connector."""

    name = "openrouter"
    _TEMPLATES = (
        _MilestoneTemplate(
            "analysis",
            "Discovery & Analysis",
            "understanding requirements and constraints",
        ),
        _MilestoneTemplate(
            "design",
            "Design & Architecture",
            "framing the solution and interfaces",
        ),
        _MilestoneTemplate(
            "implementation",
            "Implementation & Validation",
            "drafting code and validating behaviour",
        ),
    )

    def __init__(
        self,
        *,
        temperature: float = 0.2,
        model: str = 'gpt-4.1-mini',
        api_key: str | None = None,
        api_key_env: str | None = None,
        pricing: Mapping[str, float] | None = None,
    ) -> None:
        self.temperature = temperature
        self.model = model
        self.api_key_env = api_key_env or 'OPENROUTER_API_KEY'
        self.api_key = api_key if api_key is not None else os.getenv(self.api_key_env)
        self.pricing = dict(pricing or {})

    def generate_plan(self, objective: str, context: str | None = None) -> PlanDraft:
        summary = self._build_summary(objective)
        milestones = [self._build_milestone(template, objective) for template in self._TEMPLATES]
        return PlanDraft(
            objective=objective,
            summary=summary,
            milestones=milestones,
            context=context,
        )

    def refine_plan(self, draft: PlanDraft, feedback: str) -> PlanDraft:
        summary = f"{draft.summary} Incorporate feedback: {feedback.strip()}."
        refined_milestones = []
        for milestone in draft.milestones:
            extra_task = PlanTask(
                id=f"{milestone.id}-feedback",
                title="Integrate feedback",
                description=(
                    f"Address feedback: {feedback.strip()} for milestone '{milestone.title}'."
                ),
                definition_of_done="Feedback items are resolved and acknowledged in the artifact.",
            )
            refined_milestones.append(
                PlanMilestone(
                    id=milestone.id,
                    title=milestone.title,
                    description=milestone.description,
                    tasks=milestone.tasks + [extra_task],
                )
            )
        return PlanDraft(
            objective=draft.objective,
            summary=summary,
            milestones=refined_milestones,
            context=draft.context,
        )

    def summarize_for_stream(self, draft: PlanDraft) -> Iterable[str]:
        header = {
            "objective": draft.objective,
            "summary": draft.summary,
            "milestones": [m.title for m in draft.milestones],
            "model": self.model,
        }
        yield json.dumps(header)
        for milestone in draft.milestones:
            tasks = " | ".join(task.title for task in milestone.tasks)
            yield f"{milestone.title}: {milestone.description} -> {tasks}"

    def _build_summary(self, objective: str) -> str:
        return (
            f"Deliver a structured plan for '{objective}'. Focus on de-risking discovery, "
            "solid design, and validated implementation."
        )

    def _build_milestone(self, template: _MilestoneTemplate, objective: str) -> PlanMilestone:
        tasks = [
            self._build_task(template.identifier, index, template.focus, objective)
            for index in range(1, 3 + 1)
        ]
        description = f"{template.title} for {objective} emphasising {template.focus}."
        return PlanMilestone(
            id=template.identifier,
            title=template.title,
            description=description,
            tasks=tasks,
        )

    def _build_task(self, milestone_id: str, index: int, focus: str, objective: str) -> PlanTask:
        verbs = ("Survey", "Outline", "Validate")
        verb = verbs[(index - 1) % len(verbs)]
        title = f"{verb} {focus}"
        description = (
            f"{verb} activities for {objective} with focus on {focus}. "
            "Capture insights for downstream phases."
        )
        dod = "Evidence captured in shared repository; stakeholders sign-off recorded."
        return PlanTask(
            id=f"{milestone_id}-{index}",
            title=title,
            description=description,
            definition_of_done=dod,
        )


__all__ = ["OpenRouterConnector"]


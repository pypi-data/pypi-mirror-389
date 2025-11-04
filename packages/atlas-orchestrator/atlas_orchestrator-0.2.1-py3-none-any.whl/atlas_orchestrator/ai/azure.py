"""Azure OpenAI connector stub for planning workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from atlas_orchestrator.ai.exceptions import AIProviderError
from atlas_orchestrator.planning.models import PlanDraft, PlanMilestone, PlanTask


class AzureOpenAIConnector:
    """Deterministic stub emulating Azure-hosted OpenAI deployment."""

    name = "azure-openai"

    def __init__(
        self,
        *,
        deployment: str = "gpt-4o-mini",
        api_version: str = "2024-05-01",
        outage_window: tuple[int, int] | None = None,
    ) -> None:
        self.deployment = deployment
        self.api_version = api_version
        self._outage_window = outage_window

    def generate_plan(self, objective: str, context: str | None = None) -> PlanDraft:
        self._guard_outage()
        milestones = self._milestones(objective)
        summary = self._summary(objective, context)
        return PlanDraft(objective=objective, summary=summary, milestones=milestones, context=context)

    def refine_plan(self, draft: PlanDraft, feedback: str) -> PlanDraft:
        self._guard_outage()
        suffix = f" Refinement captured at {datetime.utcnow().isoformat()}"
        return PlanDraft(
            objective=draft.objective,
            summary=f"{draft.summary} Feedback: {feedback.strip()}.{suffix}",
            milestones=[
                PlanMilestone(
                    id=milestone.id,
                    title=milestone.title,
                    description=f"{milestone.description} Feedback={feedback.strip()}.",
                    tasks=[
                        *milestone.tasks,
                        PlanTask(
                            id=f"{milestone.id}-qa",
                            title="Quality review",
                            description="Run validation checklist for updated scope.",
                            definition_of_done="QA sign-off recorded.",
                        ),
                    ],
                )
                for milestone in draft.milestones
            ],
            context=draft.context,
        )

    def summarize_for_stream(self, draft: PlanDraft) -> Iterable[str]:
        yield f"deployment={self.deployment} objective={draft.objective}"
        for milestone in draft.milestones:
            task_titles = ":".join(task.title for task in milestone.tasks)
            yield f"{milestone.title}::{task_titles}"

    def _milestones(self, objective: str) -> list[PlanMilestone]:
        ids = ("plan", "build", "verify")
        titles = (
            "Plan Alignment",
            "Build Iterations",
            "Verification & Launch",
        )
        descriptions = (
            "Shape roadmap, stakeholders, and milestones",
            "Execute development cycles and integrations",
            "Validate, measure, and launch",
        )
        return [
            PlanMilestone(
                id=ident,
                title=title,
                description=f"{desc} for {objective}.",
                tasks=[
                    PlanTask(
                        id=f"{ident}-{index}",
                        title=f"{title} task {index}",
                        description=f"{desc} step {index} covering {objective}.",
                        definition_of_done="Documented in release journal.",
                    )
                    for index in range(1, 4)
                ],
            )
            for ident, title, desc in zip(ids, titles, descriptions, strict=True)
        ]

    def _summary(self, objective: str, context: str | None) -> str:
        base = f"Azure deployment '{self.deployment}' plan for {objective}."
        if context:
            return f"{base} Context: {context.strip()}"
        return base

    def _guard_outage(self) -> None:
        if not self._outage_window:
            return
        start, end = self._outage_window
        current_minute = datetime.utcnow().minute
        if start <= current_minute <= end:
            raise AIProviderError(self.name, "Azure OpenAI deployment is temporarily unavailable")


__all__ = ["AzureOpenAIConnector"]

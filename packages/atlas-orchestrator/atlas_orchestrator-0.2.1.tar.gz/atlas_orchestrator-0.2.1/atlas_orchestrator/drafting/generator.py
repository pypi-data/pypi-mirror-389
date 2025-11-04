"""Draft generator turning specifications into code bundles."""

from __future__ import annotations

from collections.abc import Iterable

from atlas_orchestrator.specs import RequirementTrace, SpecificationDocument, SpecModule

from .models import DraftModule


class DraftGenerator:
    """Create draft modules from specification modules."""

    name = "openrouter-draft"

    def generate_modules(
        self,
        document: SpecificationDocument,
        target_module_ids: Iterable[str] | None = None,
    ) -> list[DraftModule]:
        target = {module_id for module_id in target_module_ids} if target_module_ids else None
        modules: list[DraftModule] = []
        for module in document.modules:
            if target and module.id not in target:
                continue
            content = self._render_module(module, document.summary, document.plan_id)
            path = f"{module.id}.py"
            modules.append(
                DraftModule(
                    id=module.id,
                    title=module.title,
                    path=path,
                    language="python",
                    content=content,
                )
            )
        return modules

    def _render_module(
        self,
        module: SpecModule,
        spec_summary: str,
        plan_id: str,
    ) -> str:
        """Return deterministic python content enriched with trace context."""

        header = [
            "# === Atlas Orchestrator GENERATED MODULE ===",
            f"# Plan: {plan_id}",
            f"# Module: {module.id} - {module.title}",
            f"# Overview: {module.overview}",
            f"# Spec summary: {spec_summary}",
        ]

        requirement_traces, task_traces = _split_traces(module.traces)
        requirements_block = ["# Requirements Context:"]
        if requirement_traces:
            for trace in requirement_traces:
                section = trace.section or "unspecified"
                requirements_block.append(
                    f"# - {trace.requirement_id} [{section}]: {trace.description}"
                )
        else:
            requirements_block.append("# - None linked")

        task_block = ["# Plan Tasks Context:"]
        if task_traces:
            for trace in task_traces:
                task_block.append(f"# - {trace.source_task_id}: {trace.description}")
        else:
            task_block.append("# - No originating tasks recorded")

        acceptance_block = [
            f"# Acceptance -> {criterion}"
            for criterion in module.acceptance_criteria
        ]

        body_lines = [
            "def execute() -> None:",
            "    \"\"\"Placeholder implementation derived from specification context.\"\"\"",
            "    trace_ids = [",
        ]
        for trace in module.traces:
            body_lines.append(f'        "{trace.requirement_id}",')
        body_lines.append("    ]")
        body_lines.extend(
            [
                "    steps = [",
                f'        "{module.id}:{module.title}",',
                "    ]",
                "    # TODO: replace placeholder logic with generated implementation",
                "    for step in steps:",
                "        print(f'executing {step}')",
            ]
        )

        return "\n".join(
            header
            + [""]
            + requirements_block
            + task_block
            + acceptance_block
            + [""]
            + body_lines
        ) + "\n"


def _split_traces(traces: Iterable[RequirementTrace]) -> tuple[list[RequirementTrace], list[RequirementTrace]]:
    requirement_traces: list[RequirementTrace] = []
    task_traces: list[RequirementTrace] = []
    for trace in traces:
        if trace.source_task_id.startswith("doc:"):
            requirement_traces.append(trace)
        else:
            task_traces.append(trace)
    return requirement_traces, task_traces


__all__ = ["DraftGenerator"]

"""Tool runner adapters for formatting and linting."""

from __future__ import annotations

from dataclasses import dataclass

from .models import DraftModule, ToolResult


class ToolRunner:
    """Protocol-like base class for tool runners."""

    name = "tool"

    def run(self, module: DraftModule) -> tuple[DraftModule, ToolResult]:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class FormatterToolRunner(ToolRunner):
    """Lightweight formatter ensuring deterministic whitespace."""

    name: str = "formatter"

    def run(self, module: DraftModule) -> tuple[DraftModule, ToolResult]:
        lines = [line.rstrip() for line in module.content.splitlines()]
        formatted = "\n".join(lines).strip("\n") + "\n"
        updated = module.model_copy(update={"content": formatted})
        result = ToolResult(tool=self.name, module_id=module.id, status="ok", output="normalized whitespace")
        return updated, result


@dataclass
class LinterToolRunner(ToolRunner):
    """Static lint checker highlighting obvious issues."""

    name: str = "linter"

    def run(self, module: DraftModule) -> tuple[DraftModule, ToolResult]:
        warnings: list[str] = []
        if "TODO" in module.content:
            warnings.append("found TODO placeholder")
        if "pass" in module.content:
            warnings.append("found pass statement")
        status = "ok" if not warnings else "warning"
        output = "; ".join(warnings) if warnings else "lint clean"
        result = ToolResult(tool=self.name, module_id=module.id, status=status, output=output)
        return module, result


__all__ = ["FormatterToolRunner", "LinterToolRunner", "ToolRunner"]

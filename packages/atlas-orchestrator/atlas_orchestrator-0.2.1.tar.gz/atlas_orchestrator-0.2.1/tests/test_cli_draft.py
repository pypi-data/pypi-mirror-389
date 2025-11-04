from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atlas_orchestrator.cli import app


def _extract_table_value(output: str, field: str) -> str:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(field):
            parts = line.split("  ", 1)
            if len(parts) == 2:
                return parts[1].strip()
    raise AssertionError(f"{field!r} not found in output:\n{output}")


def _load_json_from_output(output: str) -> dict[str, object]:
    start = output.find("{")
    if start == -1:
        raise AssertionError("JSON blob not found in output")
    return json.loads(output[start:])


def test_draft_cli_generate_show_list() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        config_path = Path("atlas_orchestrator.yaml")
        config_path.write_text("project:\n  workspace: .atlas_orchestrator\n", encoding="utf-8")
        docs_dir = Path("docs")
        docs_dir.mkdir()
        prd_path = docs_dir / "PRODUCT_REQUIREMENTS.md"
        prd_path.write_text(
            """
## Analysis
- Ensure discovery milestones capture analysis outcomes for MVP delivery.
## Design
- Provide design guidance covering architecture and interfaces for MVP.
## Implementation
- Validate implementation tasks include verification hooks and automation.
""".strip(),
            encoding="utf-8",
        )

        plan_result = runner.invoke(
            app,
            ["--config", str(config_path), "plan", "create", "Ship MVP"],
        )
        assert plan_result.exit_code == 0
        plan_id = _extract_table_value(plan_result.stdout, "Plan ID")

        spec_result = runner.invoke(
            app,
            ["--config", str(config_path), "spec", "generate", plan_id],
        )
        assert spec_result.exit_code == 0
        spec_id = _extract_table_value(spec_result.stdout, "Spec ID")

        draft_result = runner.invoke(
            app,
            ["--config", str(config_path), "draft", "generate", spec_id],
        )
        assert draft_result.exit_code == 0
        draft_id = _extract_table_value(draft_result.stdout, "Draft ID")
        assert "Draft Summary" in draft_result.stdout

        show_result = runner.invoke(
            app,
            ["--config", str(config_path), "draft", "show", draft_id],
        )
        assert show_result.exit_code == 0
        assert "tooling:" in show_result.stdout
        payload = _load_json_from_output(show_result.stdout)
        assert "modules" in payload
        assert payload["modules"]
        assert "Requirements Context" in payload["modules"][0]["content"]

        list_result = runner.invoke(
            app,
            ["--config", str(config_path), "draft", "list"],
        )
        assert list_result.exit_code == 0
        assert draft_id in list_result.stdout

        targeted_result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "draft",
                "generate",
                spec_id,
                "--module",
                "analysis",
            ],
        )
        assert targeted_result.exit_code == 0
        targeted_id = _extract_table_value(targeted_result.stdout, "Draft ID")
        assert targeted_id != draft_id

        draft_json = runner.invoke(
            app,
            ["--config", str(config_path), "draft", "generate", spec_id, "--output", "json"],
        )
        assert draft_json.exit_code == 0
        draft_payload = json.loads(draft_json.stdout)
        assert draft_payload["metadata"]["spec_id"] == spec_id
        assert draft_payload["metadata"]["draft_id"]

        resume_result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "draft",
                "generate",
                spec_id,
                "--resume",
            ],
        )
        assert resume_result.exit_code == 0

        usage_result = runner.invoke(
            app,
            ["--config", str(config_path), "observe", "usage"],
        )
        assert usage_result.exit_code == 0
        summary = json.loads(usage_result.stdout)
        assert summary["events"]["cli.draft.generate"]["count"] >= 3
        assert summary["events"]["cli.observe.usage"]["count"] == 1

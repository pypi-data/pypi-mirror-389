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


def test_spec_cli_generate_show_diff() -> None:
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
        plans_dir = Path(".atlas_orchestrator") / "plans"
        specs_dir = Path(".atlas_orchestrator") / "specs"

        plan_result = runner.invoke(
            app,
            ["--config", str(config_path), "plan", "create", "Ship MVP"],
        )
        assert plan_result.exit_code == 0
        plan_id = _extract_table_value(plan_result.stdout, "Plan ID")
        assert (plans_dir / f"{plan_id}.json").exists()

        spec_result = runner.invoke(
            app,
            ["--config", str(config_path), "spec", "generate", plan_id],
        )
        assert spec_result.exit_code == 0
        assert "Spec Summary" in spec_result.stdout
        spec_id = _extract_table_value(spec_result.stdout, "Spec ID")
        assert (specs_dir / f"{spec_id}.json").exists()

        spec_json = runner.invoke(
            app,
            ["--config", str(config_path), "spec", "generate", plan_id, "--output", "json"],
        )
        assert spec_json.exit_code == 0
        spec_payload = json.loads(spec_json.stdout)
        assert spec_payload["metadata"]["spec_id"]
        assert spec_payload["metadata"]["plan_id"] == plan_id

        show_result = runner.invoke(
            app,
            ["--config", str(config_path), "spec", "show", spec_id],
        )
        assert show_result.exit_code == 0
        assert "coverage:" in show_result.stdout
        parsed = _load_json_from_output(show_result.stdout)
        assert "coverage" in parsed
        assert len(parsed["coverage"]) >= 1

        section_result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "spec",
                "show",
                spec_id,
                "--section",
                "Design",
            ],
        )
        assert section_result.exit_code == 0
        filtered = _load_json_from_output(section_result.stdout)
        assert filtered["modules"]
        for module in filtered["modules"]:
            assert all(trace.get("section") == "Design" for trace in module["traces"])

        spec_result_two = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "spec",
                "generate",
                plan_id,
                "--module",
                "analysis",
            ],
        )
        assert spec_result_two.exit_code == 0
        spec_id_two = _extract_table_value(spec_result_two.stdout, "Spec ID")
        assert spec_id_two != spec_id

        diff_result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "spec",
                "diff",
                spec_id,
                spec_id_two,
                "--section",
                "Analysis",
            ],
        )
        assert diff_result.exit_code == 0
        assert "spec:" in diff_result.stdout

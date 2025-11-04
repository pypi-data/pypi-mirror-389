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


def test_plan_create_and_refine(tmp_path: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        config_path = Path("atlas_orchestrator.yaml")
        config_path.write_text("project:\n  workspace: .atlas_orchestrator\n", encoding="utf-8")
        plans_dir = Path(".atlas_orchestrator") / "plans"

        create_args = ["--config", str(config_path), "plan", "create", "Ship MVP"]
        create_result = runner.invoke(app, create_args)
        assert create_result.exit_code == 0
        assert "Plan Summary" in create_result.stdout
        plan_id = _extract_table_value(create_result.stdout, "Plan ID")
        milestones = _extract_table_value(create_result.stdout, "Milestones")
        assert milestones.endswith("total")

        artifact_path = plans_dir / f"{plan_id}.json"
        assert artifact_path.exists()

        json_args = [
            "--config",
            str(config_path),
            "plan",
            "create",
            "Ship MVP JSON",
            "--output",
            "json",
        ]
        json_result = runner.invoke(app, json_args)
        assert json_result.exit_code == 0
        payload = json.loads(json_result.stdout)
        assert payload["metadata"]["plan_id"]
        assert payload["metadata"]["provider"]
        assert payload["plan"]["objective"] == "Ship MVP JSON"

        refine_args = [
            "--config",
            str(config_path),
            "plan",
            "refine",
            plan_id,
            "--feedback",
            "Tighten QA coverage",
        ]
        refine_result = runner.invoke(app, refine_args)
        assert refine_result.exit_code == 0
        refine_lines = [line.strip() for line in refine_result.stdout.splitlines() if line.strip()]
        final_line = refine_lines[-1]
        assert final_line.startswith("plan_id=")
        assert f"parent={plan_id}" in final_line

        new_plan_id = final_line.split()[0].split("=")[1]
        assert new_plan_id != plan_id
        assert (plans_dir / f"{new_plan_id}.json").exists()


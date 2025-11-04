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


def _load_draft_metadata(draft_id: str) -> dict[str, object]:
    draft_path = Path(".atlas_orchestrator") / "drafts" / f"{draft_id}.json"
    return json.loads(draft_path.read_text(encoding="utf-8"))


def test_validate_cli_run_and_publish() -> None:
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

        env = {"ATLAS_ORCHESTRATOR_VALIDATION_DRY_RUN": "1"}

        plan_result = runner.invoke(
            app,
            ["--config", str(config_path), "plan", "create", "Ship MVP"],
            env=env,
        )
        assert plan_result.exit_code == 0
        plan_id = _extract_table_value(plan_result.stdout, "Plan ID")

        spec_result = runner.invoke(
            app,
            ["--config", str(config_path), "spec", "generate", plan_id],
            env=env,
        )
        assert spec_result.exit_code == 0
        spec_id = _extract_table_value(spec_result.stdout, "Spec ID")

        draft_result = runner.invoke(
            app,
            ["--config", str(config_path), "draft", "generate", spec_id],
            env=env,
        )
        assert draft_result.exit_code == 0
        draft_id = _extract_table_value(draft_result.stdout, "Draft ID")

        validate_result = runner.invoke(
            app,
            ["--config", str(config_path), "validate", "run", draft_id],
            env=env,
        )
        assert validate_result.exit_code == 0
        assert "status=passed" in validate_result.stdout

        publish_result = runner.invoke(
            app,
            ["--config", str(config_path), "validate", "publish", draft_id],
            env=env,
        )
        assert publish_result.exit_code == 0
        assert "publishable=true" in publish_result.stdout

        metadata = _load_draft_metadata(draft_id)
        module_id = metadata["document"]["modules"][0]["id"]
        module_path = Path("generated") / draft_id / f"{module_id}.py"
        module_path.write_text("# mutated module\n", encoding="utf-8")

        failed_validation = runner.invoke(
            app,
            ["--config", str(config_path), "validate", "run", draft_id],
            env=env,
        )
        assert failed_validation.exit_code == 0
        assert "status=failed" in failed_validation.stdout
        assert "remediation:" in failed_validation.stdout

        publish_blocked = runner.invoke(
            app,
            ["--config", str(config_path), "validate", "publish", draft_id],
            env=env,
        )
        assert publish_blocked.exit_code == 1

        publish_override = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "validate",
                "publish",
                draft_id,
                "--override",
                "--reason",
                "Risk accepted",
            ],
            env=env,
        )
        assert publish_override.exit_code == 0
        assert "publishable=true" in publish_override.stdout

from __future__ import annotations

from typer.testing import CliRunner

from atlas_orchestrator import __version__
from atlas_orchestrator.cli import app

runner = CliRunner()


def test_cli_version_option() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_health_option() -> None:
    result = runner.invoke(app, ["--health"])
    assert result.exit_code == 0
    assert "status=healthy" in result.stdout


def test_cli_health_command() -> None:
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "status=healthy" in result.stdout


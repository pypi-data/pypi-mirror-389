"""Tests for the premium API server entrypoint helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_orchestrator.premium_api.server import build_application


def test_build_application_requires_premium_api_enabled(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("premium_api:\n  enabled: false\n")

    with pytest.raises(RuntimeError, match="Premium API is disabled"):
        build_application(config_path=config_path, project_root=tmp_path)


def test_build_application_constructs_app(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("premium_api:\n  enabled: true\n")

    app = build_application(config_path=config_path, project_root=tmp_path)

    assert app.title == "Atlas Orchestrator Premium API"
    assert hasattr(app.state, "container")
    assert hasattr(app.state, "config")


def test_workspace_override_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("premium_api:\n  enabled: true\n")

    override_root = tmp_path / "workspace"
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_PREMIUM_API_WORKSPACE", str(override_root))

    app = build_application(config_path=config_path, project_root=tmp_path)

    settings = app.state.container.resolve("premium_api.settings")
    assert str(settings.base_dir).startswith(str(override_root))

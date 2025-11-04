from __future__ import annotations

from pathlib import Path

import pytest

from atlas_orchestrator.config import AppConfig, ConfigError, ConfigLoader


def test_loads_defaults_when_no_project_file(tmp_path: Path) -> None:
    loader = ConfigLoader(project_root=tmp_path)
    config = loader.load(env={})

    assert isinstance(config, AppConfig)
    assert config.project.name == "atlas-orchestrator-project"
    assert config.ai.default_provider == "openrouter"
    assert config.ai.fallback_providers == []
    assert "openrouter" in config.ai.providers


def test_merges_project_file_over_defaults(tmp_path: Path) -> None:
    project_config = tmp_path / "atlas_orchestrator.yaml"
    project_config.write_text(
        """
logging:
  level: DEBUG
ai:
  providers:
    openrouter:
      model: gpt-4.1
""",
        encoding="utf-8",
    )

    loader = ConfigLoader(project_root=tmp_path)
    config = loader.load(env={})

    assert config.logging.level == "DEBUG"
    assert config.ai.providers["openrouter"].model == "gpt-4.1"


def test_environment_overrides_take_precedence(tmp_path: Path) -> None:
    loader = ConfigLoader(project_root=tmp_path)
    env = {
        "ATLAS_ORCHESTRATOR__LOGGING__LEVEL": "WARNING",
        "ATLAS_ORCHESTRATOR__FEATURES__EXPERIMENTAL": "true",
    }
    config = loader.load(env=env)

    assert config.logging.level == "WARNING"
    assert config.features.experimental is True


def test_missing_config_file_raises(tmp_path: Path) -> None:
    loader = ConfigLoader(project_root=tmp_path)
    with pytest.raises(ConfigError):
        loader.load(config_file=tmp_path / "missing.yaml", env={})

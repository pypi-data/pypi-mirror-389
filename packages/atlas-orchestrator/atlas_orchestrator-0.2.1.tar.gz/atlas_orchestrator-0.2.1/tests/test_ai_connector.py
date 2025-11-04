from __future__ import annotations

from atlas_orchestrator.ai import AnthropicConnector, FallbackConnector, OpenRouterConnector
from atlas_orchestrator.ai.factory import build_connector, get_connector_registry
from atlas_orchestrator.planning.models import PlanDraft
from atlas_orchestrator.config import ProviderSettings
from atlas_orchestrator.sdk import AtlasOrchestratorClient


def sample_factory(settings: ProviderSettings) -> OpenRouterConnector:
    return OpenRouterConnector(model=settings.model)


def test_openrouter_generate_plan_structure() -> None:
    connector = OpenRouterConnector()
    draft = connector.generate_plan("Launch new reporting dashboard")

    assert isinstance(draft, PlanDraft)
    assert draft.objective == "Launch new reporting dashboard"
    assert draft.milestones
    assert draft.milestones[0].tasks


def test_openrouter_refine_plan_adds_feedback_task() -> None:
    connector = OpenRouterConnector()
    draft = connector.generate_plan("Improve onboarding")
    refined = connector.refine_plan(draft, "Add telemetry focus")

    for milestone in refined.milestones:
        titles = [task.title for task in milestone.tasks]
        assert "Integrate feedback" in titles


def test_openrouter_streaming_chunks() -> None:
    connector = OpenRouterConnector()
    draft = connector.generate_plan("Enhance CI pipeline")
    chunks = list(connector.summarize_for_stream(draft))

    assert chunks
    assert any("Enhance CI pipeline" in chunk for chunk in chunks)


def test_fallback_connector_uses_secondary_when_primary_fails() -> None:
    primary = AnthropicConnector(inject_failure=True)
    secondary = OpenRouterConnector()
    fallback = FallbackConnector([primary, secondary])

    draft = fallback.generate_plan("Ship fallback feature")

    assert isinstance(draft, PlanDraft)
    assert fallback.current_provider_name == secondary.name


def test_build_connector_supports_dynamic_factory() -> None:
    settings = ProviderSettings(
        type="tests.test_ai_connector:sample_factory",
        model="gpt-4.1-mini",
    )
    registry = get_connector_registry()
    if settings.type in registry:
        registry.unregister(settings.type)

    connector = build_connector(settings)

    assert isinstance(connector, OpenRouterConnector)

    registry.unregister(settings.type)


def test_openrouter_connector_prefers_explicit_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-token")
    connector = OpenRouterConnector(api_key="override-token")

    assert connector.api_key == "override-token"

def test_openrouter_connector_reads_env_when_missing(monkeypatch) -> None:
    monkeypatch.setenv("CUSTOM_OPENROUTER_KEY", "from-env")
    connector = OpenRouterConnector(api_key_env="CUSTOM_OPENROUTER_KEY")

    assert connector.api_key == "from-env"


def test_client_initialises_with_api_key(tmp_path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "PRODUCT_REQUIREMENTS.md").write_text("# Requirements\n- Sample", encoding="utf-8")

    client = AtlasOrchestratorClient(project_root=tmp_path, api_key="sdk-token")
    connector = client.planning._connector

    assert isinstance(connector, OpenRouterConnector)
    assert connector.api_key == "sdk-token"
    assert client.config.ai.providers["openrouter"].api_key == "sdk-token"

def _prepare_product_requirements(tmp_path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "PRODUCT_REQUIREMENTS.md").write_text(
        """# Requirements
- Discovery ensures alignment
- Design supports scale
- Implementation validates behaviour
""",
        encoding="utf-8",
    )


def test_client_create_plan_reports_usage(tmp_path) -> None:
    _prepare_product_requirements(tmp_path)
    client = AtlasOrchestratorClient(project_root=tmp_path, api_key="sdk-token", model="openai/gpt-5")

    plan = client.create_plan("Improve search relevance", context="Focus on ranking signals")

    assert plan.metadata.usage is not None
    assert plan.metadata.usage.model == "openai/gpt-5"
    assert plan.metadata.usage.input_tokens > 0
    assert plan.metadata.usage.output_tokens > 0
    assert plan.metadata.usage.total_cost >= 0.0
    assert client.config.ai.providers["openrouter"].model == "openai/gpt-5"

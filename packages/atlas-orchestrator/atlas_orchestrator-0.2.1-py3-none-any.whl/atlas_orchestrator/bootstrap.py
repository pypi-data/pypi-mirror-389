"""Application service wiring helpers."""

from __future__ import annotations

from pathlib import Path

from .ai import FallbackConnector
from .ai.factory import build_connector
from .analytics import UsageAnalytics
from .config import AppConfig
from .container import DependencyContainer
from .context import ContextBuilder, ContextCache
from .drafting import (
    DraftGenerator,
    DraftRepository,
    DraftingService,
    FormatterToolRunner,
    LinterToolRunner,
)
from .planning import PlanningService, PlanRepository
from .specs import (
    RequirementsCatalog,
    SpecificationGenerator,
    SpecificationRepository,
    SpecificationService,
)
from .validation import (
    PytestRunner,
    ValidationRepository,
    ValidationService,
)
from .premium_api.bootstrap import register_premium_api_services
from .workflows import WorkflowStateStore


def register_services(
    container: DependencyContainer,
    config: AppConfig,
    project_root: Path,
) -> None:
    """Register core services for the application lifecycle."""

    workspace_root = project_root / config.project.workspace

    analytics = UsageAnalytics(workspace_root / "metrics", enabled=config.features.telemetry)
    state_store = WorkflowStateStore(workspace_root / "state")
    container.register_instance("analytics.usage", analytics)
    container.register_instance("workflows.state", state_store)

    provider_chain = config.ai.provider_chain()
    connectors = [build_connector(settings) for settings in provider_chain]
    if len(connectors) == 1:
        connector_instance = connectors[0]
    else:
        connector_instance = FallbackConnector(connectors)
    container.register_singleton("ai.connector", lambda _: connector_instance)

    container.register_singleton(
        "planning.repository",
        lambda _: PlanRepository(project_root=project_root, workspace=config.project.workspace),
    )

    container.register_singleton(
        "context.cache",
        lambda _: ContextCache(workspace_root / "cache" / "context"),
    )

    def _context_builder(_: DependencyContainer) -> ContextBuilder:
        plan_repo = container.resolve("planning.repository")
        cache = container.resolve("context.cache")
        return ContextBuilder(repository=plan_repo, cache=cache)

    container.register_singleton("context.builder", _context_builder)

    requirements_path = project_root / "docs" / "PRODUCT_REQUIREMENTS.md"
    requirements_catalog = RequirementsCatalog.from_markdown(requirements_path)

    container.register_singleton(
        "specification.repository",
        lambda _: SpecificationRepository(
            project_root=project_root,
            workspace=config.project.workspace,
        ),
    )

    container.register_singleton(
        "specification.generator",
        lambda _: SpecificationGenerator(requirements=requirements_catalog),
    )

    container.register_singleton("drafting.repository", lambda _: DraftRepository(project_root=project_root, workspace=config.project.workspace))
    container.register_singleton("drafting.generator", lambda _: DraftGenerator())
    container.register_singleton(
        "drafting.tools",
        lambda _: [FormatterToolRunner(), LinterToolRunner()],
    )

    def _planning(_: DependencyContainer) -> PlanningService:
        connector = container.resolve("ai.connector")
        repository = container.resolve("planning.repository")
        return PlanningService(connector=connector, repository=repository)

    container.register_singleton("planning.service", _planning)

    def _specification(_: DependencyContainer) -> SpecificationService:
        plan_repo = container.resolve("planning.repository")
        repository = container.resolve("specification.repository")
        context_builder = container.resolve("context.builder")
        generator = container.resolve("specification.generator")
        return SpecificationService(
            plan_repository=plan_repo,
            repository=repository,
            context_builder=context_builder,
            generator=generator,
        )

    container.register_singleton("specification.service", _specification)

    def _drafting(_: DependencyContainer) -> DraftingService:
        spec_repo = container.resolve("specification.repository")
        repository = container.resolve("drafting.repository")
        generator = container.resolve("drafting.generator")
        tools = container.resolve("drafting.tools")
        state_store = container.resolve("workflows.state")
        return DraftingService(
            specification_repository=spec_repo,
            repository=repository,
            generator=generator,
            tool_runners=tools,
            state_store=state_store,
        )

    container.register_singleton("drafting.service", _drafting)

    container.register_singleton("validation.repository",
        lambda _: ValidationRepository(project_root=project_root, workspace=config.project.workspace),
    )
    container.register_singleton(
        "validation.pytest_runner",
        lambda _: PytestRunner(project_root=project_root),
    )

    def _validation(_: DependencyContainer) -> ValidationService:
        draft_repo = container.resolve("drafting.repository")
        spec_repo = container.resolve("specification.repository")
        repository = container.resolve("validation.repository")
        pytest_runner = container.resolve("validation.pytest_runner")
        try:
            analytics = container.resolve("analytics.usage")
        except KeyError:
            analytics = None
        return ValidationService(
            draft_repository=draft_repo,
            specification_repository=spec_repo,
            validation_repository=repository,
            pytest_runner=pytest_runner,
            analytics=analytics,
        )

    container.register_singleton("validation.service", _validation)

    register_premium_api_services(container, config, workspace_root)


__all__ = ["register_services"]



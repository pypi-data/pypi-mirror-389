"""Python SDK facade for interacting with the Atlas Orchestrator platform."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, cast

from . import __version__
from .analytics import UsageAnalytics
from .bootstrap import register_services
from .config import AppConfig, ConfigLoader, ProviderSettings
from .workflows import WorkflowExecutionError
from .ai.usage import LLMUsage, default_pricing_for, estimate_usage
from .container import DependencyContainer
from .drafting import DraftArtifact, DraftDocument, DraftingService
from .logging import configure_logging
from .planning import PlanArtifact, PlanDraft, PlanningService
from .premium_api.client import PremiumApiClient
from .specs import SpecificationArtifact, SpecificationDocument, SpecificationService
from .validation import ValidationArtifact, ValidationGateError, ValidationService

StreamCallback = Callable[[str], None]


class AtlasOrchestratorClient:
    """Thin SDK surface exposing health, planning, specification, and drafting operations."""

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        config_file: str | None = None,
        project_root: Path | None = None,
        container: DependencyContainer | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._project_root = Path(project_root or Path.cwd()).resolve()
        self._loader = ConfigLoader(project_root=self._project_root)
        loaded_config = config or self._loader.load(
            config_file=Path(config_file).expanduser() if config_file else None
        )
        loaded_config = self._override_openrouter_settings(loaded_config, api_key, model)
        self._config = loaded_config
        provider_settings = self._config.ai.get(self._config.ai.default_provider)
        self._api_key = provider_settings.api_key
        self._model_name = provider_settings.model
        self._pricing = dict(provider_settings.pricing or {})
        configure_logging(self._config.logging, force=False)
        self._container = container or DependencyContainer()
        self._container.register_instance("config", self._config)
        register_services(self._container, self._config, self._project_root)
        try:
            self._analytics = cast(UsageAnalytics, self._container.resolve("analytics.usage"))
        except KeyError:
            self._analytics = None

    @property
    def validation(self) -> ValidationService:
        return cast(ValidationService, self._container.resolve("validation.service"))

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def project_root(self) -> Path:
        return self._project_root

    def _override_openrouter_settings(
        self,
        config: AppConfig,
        api_key: str | None,
        model: str | None,
    ) -> AppConfig:
        providers = config.ai.providers
        updated: dict[str, ProviderSettings] = {}
        changed = False
        for name, settings in providers.items():
            if settings.type != "openrouter":
                updated[name] = settings
                continue
            new_fields: dict[str, object] = {}
            if api_key is not None:
                new_fields["api_key"] = api_key
            if model is not None:
                new_fields["model"] = model
                pricing_override = default_pricing_for(model)
                if pricing_override is not None:
                    new_fields["pricing"] = pricing_override
            if new_fields:
                updated[name] = settings.model_copy(update=new_fields)
                changed = True
            else:
                updated[name] = settings
        if not changed:
            return config
        ai_config = config.ai.model_copy(update={"providers": updated}, deep=True)
        return config.model_copy(update={"ai": ai_config}, deep=True)

    def _authenticate_request(self, operation: str) -> None:
        """Placeholder for credit-based authentication and quota checks."""

        _ = (operation, self._api_key)

    def _calculate_usage(self, *, prompt: str, completion: str) -> LLMUsage:
        return estimate_usage(
            model=self._model_name,
            prompt_text=prompt,
            completion_text=completion,
            pricing=self._pricing,
        )

    def _attach_usage(self, artifact: Any, usage: LLMUsage):
        metadata = artifact.metadata.model_copy(update={"usage": usage})
        return artifact.model_copy(update={"metadata": metadata})

    def _compose_plan_prompt(self, objective: str, context: str | None) -> str:
        parts = [f"objective:{objective.strip()}"] if objective else []
        if context:
            parts.append(f"context:{context.strip()}")
        return "\\n".join(parts)

    def _compose_refine_prompt(self, feedback: str, plan: PlanDraft) -> str:
        prefix = f"feedback:{feedback.strip()}" if feedback else "feedback:"
        return "\\n".join([prefix, self._plan_to_text(plan)])

    def _compose_spec_prompt(
        self,
        plan_id: str,
        module_id: str | None,
        force_refresh: bool,
    ) -> str:
        parts = [f"plan:{plan_id}"]
        if module_id:
            parts.append(f"module:{module_id}")
        parts.append(f"force_refresh:{force_refresh}")
        return " ".join(parts)

    def _compose_draft_prompt(
        self,
        spec_id: str,
        module_ids: list[str] | None,
        resume: bool,
    ) -> str:
        modules = ",".join(module_ids) if module_ids else "all"
        return f"spec:{spec_id} modules:{modules} resume:{resume}"

    def _plan_to_text(self, plan: PlanDraft) -> str:
        lines = [plan.summary]
        for milestone in plan.milestones:
            lines.append(f"{milestone.title}: {milestone.description}")
            for task in milestone.tasks:
                lines.append(f"- {task.title}: {task.description}")
        return "\\n".join(lines)

    def _spec_to_text(self, document: SpecificationDocument) -> str:
        lines = [document.summary]
        for module in document.modules:
            lines.append(f"{module.id}:{module.title}")
            lines.extend(f"- {criterion}" for criterion in module.acceptance_criteria)
            lines.extend(
                f"trace:{trace.requirement_id}:{trace.description}"
                for trace in module.traces
            )
        return "\\n".join(lines)

    def _draft_to_text(self, document: DraftDocument) -> str:
        lines = [document.summary]
        for module in document.modules:
            lines.append(f"{module.id}:{module.title}@{module.path}")
            lines.append(module.content)
        return "\\n".join(lines)

    def _record_usage(self, event: str, metadata: Mapping[str, Any]) -> None:
        if getattr(self, "_analytics", None) is None:
            return
        self._analytics.record(event, metadata)

    @property
    def planning(self) -> PlanningService:
        return cast(PlanningService, self._container.resolve("planning.service"))

    @property
    def specification(self) -> SpecificationService:
        return cast(SpecificationService, self._container.resolve("specification.service"))

    @property
    def drafting(self) -> DraftingService:
        return cast(DraftingService, self._container.resolve("drafting.service"))

    def health(self) -> dict[str, Any]:
        """Return a health summary including environment and version info."""

        return {
            "status": "healthy",
            "version": __version__,
            "environment": self._config.project.environment,
            "workspace": self._config.project.workspace,
        }

    def premium_api_client(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float | None = None,
    ) -> PremiumApiClient:
        """Return an async premium API client bound to the supplied endpoint."""

        return PremiumApiClient(base_url=base_url, api_key=api_key, timeout=timeout)

    def version(self) -> str:
        return __version__

    def create_plan(
        self,
        objective: str,
        *,
        context: str | None = None,
        stream: StreamCallback | None = None,
    ) -> PlanArtifact:
        self._authenticate_request("create_plan")
        try:
            artifact = self.planning.generate_plan(objective, context=context, stream=stream)
        except Exception as exc:
            self._record_usage(
                "sdk.plan.create",
                {"status": "failure", "error": exc.__class__.__name__},
            )
            raise
        usage = self._calculate_usage(
            prompt=self._compose_plan_prompt(objective, context),
            completion=self._plan_to_text(artifact.plan),
        )
        artifact = self._attach_usage(artifact, usage)
        self._record_usage(
            "sdk.plan.create",
            {
                "status": "success",
                "plan_id": artifact.metadata.plan_id,
                "provider": artifact.metadata.provider,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_cost": usage.total_cost,
            },
        )
        return artifact

    def refine_plan(
        self,
        plan_id: str,
        feedback: str,
        *,
        stream: StreamCallback | None = None,
    ) -> PlanArtifact:
        self._authenticate_request("refine_plan")
        try:
            artifact = self.planning.refine_plan(plan_id, feedback, stream=stream)
        except Exception as exc:
            self._record_usage(
                "sdk.plan.refine",
                {"status": "failure", "plan_id": plan_id, "error": exc.__class__.__name__},
            )
            raise
        usage = self._calculate_usage(
            prompt=self._compose_refine_prompt(feedback, artifact.plan),
            completion=self._plan_to_text(artifact.plan),
        )
        artifact = self._attach_usage(artifact, usage)
        self._record_usage(
            "sdk.plan.refine",
            {
                "status": "success",
                "plan_id": artifact.metadata.plan_id,
                "parent": plan_id,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_cost": usage.total_cost,
            },
        )
        return artifact

    def generate_spec(
        self,
        plan_id: str,
        *,
        module_id: str | None = None,
        stream: StreamCallback | None = None,
        force_refresh: bool = False,
    ) -> SpecificationArtifact:
        self._authenticate_request("generate_spec")
        try:
            artifact = self.specification.generate(
                plan_id,
                module_id=module_id,
                stream=stream,
                force_refresh=force_refresh,
            )
        except Exception as exc:
            self._record_usage(
                "sdk.spec.generate",
                {"status": "failure", "plan_id": plan_id, "error": exc.__class__.__name__},
            )
            raise
        usage = self._calculate_usage(
            prompt=self._compose_spec_prompt(plan_id, module_id, force_refresh),
            completion=self._spec_to_text(artifact.document),
        )
        artifact = self._attach_usage(artifact, usage)
        self._record_usage(
            "sdk.spec.generate",
            {
                "status": "success",
                "plan_id": plan_id,
                "spec_id": artifact.metadata.spec_id,
                "modules": len(artifact.metadata.modules),
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_cost": usage.total_cost,
            },
        )
        return artifact

    def get_spec(
        self,
        spec_id: str,
        *,
        sections: Iterable[str] | None = None,
    ) -> SpecificationArtifact:
        return self.specification.load(spec_id, sections=sections)

    def list_specs(self) -> list[str]:
        return list(self.specification.list_ids())

    def diff_specs(
        self,
        first_spec: str,
        second_spec: str,
        *,
        sections: Iterable[str] | None = None,
    ) -> list[str]:
        return self.specification.diff(first_spec, second_spec, sections=sections)

    def generate_draft(
        self,
        spec_id: str,
        *,
        module_ids: Iterable[str] | None = None,
        resume: bool = False,
        stream: StreamCallback | None = None,
    ) -> DraftArtifact:
        self._authenticate_request("generate_draft")
        modules_argument = list(module_ids) if module_ids is not None else None
        try:
            artifact = self.drafting.generate(
                spec_id, module_ids=modules_argument, resume=resume, stream=stream
            )
        except WorkflowExecutionError as exc:
            self._record_usage(
                "sdk.draft.generate",
                {"status": "failure", "spec_id": spec_id, "error": "workflow", "resume_available": exc.resume_available},
            )
            raise
        except Exception as exc:
            self._record_usage(
                "sdk.draft.generate",
                {"status": "failure", "spec_id": spec_id, "error": exc.__class__.__name__},
            )
            raise
        usage = self._calculate_usage(
            prompt=self._compose_draft_prompt(spec_id, modules_argument, resume),
            completion=self._draft_to_text(artifact.document),
        )
        artifact = self._attach_usage(artifact, usage)
        self._record_usage(
            "sdk.draft.generate",
            {"status": "success", "spec_id": spec_id, "draft_id": artifact.metadata.draft_id, "modules": len(artifact.metadata.modules), "resume": resume, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "total_cost": usage.total_cost},
        )
        return artifact

    def run_validation(
        self,
        draft_id: str,
        *,
        override: bool = False,
        reason: str | None = None,
        stream: StreamCallback | None = None,
        pytest_args: Iterable[str] | None = None,
    ) -> ValidationArtifact:
        try:
            artifact = self.validation.run(
                draft_id,
                override=override,
                reason=reason,
                stream=stream,
                pytest_args=list(pytest_args) if pytest_args else None,
            )
        except Exception as exc:
            self._record_usage(
                "sdk.validation.run",
                {"status": "failure", "draft_id": draft_id, "error": exc.__class__.__name__},
            )
            raise
        self._record_usage(
            "sdk.validation.run",
            {
                "status": artifact.metadata.status,
                "draft_id": draft_id,
                "validation_id": artifact.metadata.validation_id,
            },
        )
        return artifact

    def ensure_draft_publishable(
        self,
        draft_id: str,
        *,
        override_reason: str | None = None,
    ) -> None:
        try:
            self.validation.ensure_publishable(draft_id, override_reason=override_reason)
        except ValidationGateError as exc:
            self._record_usage(
                "sdk.validation.publish",
                {"status": "blocked", "draft_id": draft_id, "error": exc.__class__.__name__},
            )
            raise
        self._record_usage(
            "sdk.validation.publish",
            {
                "status": "override" if override_reason else "allowed",
                "draft_id": draft_id,
            },
        )


    def get_draft(self, draft_id: str) -> DraftArtifact:
        return self.drafting.load(draft_id)

    def list_drafts(self) -> list[str]:
        return list(self.drafting.list_ids())


A4Client = AtlasOrchestratorClient  # Backward compatibility alias

__all__ = ["AtlasOrchestratorClient", "A4Client", "StreamCallback"]

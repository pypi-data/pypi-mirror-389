"""Fallback orchestration for AI connectors."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from atlas_orchestrator.ai.base import AIConnector
from atlas_orchestrator.ai.exceptions import AIProviderError, AINonRetryableError
from atlas_orchestrator.planning.models import PlanDraft


_MISSING = object()


class FallbackConnector:
    """Try multiple AI connectors sequentially with fallback semantics."""

    name = "fallback"

    def __init__(self, connectors: Sequence[AIConnector]) -> None:
        if not connectors:
            raise ValueError("At least one connector is required for fallback")
        self._connectors = list(connectors)
        self._current_provider = connectors[0].name
        self._preferred_provider: str | None = None
        self._plan_bindings: dict[str, str] = {}

    @property
    def current_provider_name(self) -> str:
        return self._current_provider

    def available_providers(self) -> list[str]:
        return [connector.name for connector in self._connectors]

    def prepare_for_plan(self, provider: str | None) -> None:
        """Hint at the preferred provider for subsequent operations."""

        self._preferred_provider = provider

    def remember_plan(self, plan_id: str, provider: str | None = None) -> None:
        resolved = provider or self._current_provider
        self._plan_bindings[plan_id] = resolved

    def generate_plan(self, objective: str, context: str | None = None) -> PlanDraft:
        draft = self._dispatch(lambda connector: connector.generate_plan(objective, context))
        return draft

    def refine_plan(self, draft: PlanDraft, feedback: str) -> PlanDraft:
        provider_hint = self._preferred_provider
        if provider_hint and provider_hint not in self.available_providers():
            provider_hint = None
        draft = self._dispatch(lambda connector: connector.refine_plan(draft, feedback), preferred=provider_hint)
        return draft

    def summarize_for_stream(self, draft: PlanDraft) -> Iterable[str]:
        connector = self._resolve_connector(self._preferred_provider or self._current_provider)
        yield from connector.summarize_for_stream(draft)

    def _dispatch(self, operation, preferred: str | None = None) -> PlanDraft:
        errors: list[AIProviderError] = []
        for connector in self._iter_candidates(preferred):
            try:
                draft = operation(connector)
            except AINonRetryableError as exc:
                self._current_provider = connector.name
                raise exc
            except AIProviderError as exc:
                errors.append(exc)
                continue
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(AIProviderError(connector.name, str(exc), recoverable=False))
                continue
            self._current_provider = connector.name
            self._preferred_provider = None
            return draft
        message = "; ".join(f"{error.provider}: {error}" for error in errors)
        raise AIProviderError(self.name, message or "All providers failed", recoverable=False)

    def _iter_candidates(self, preferred: str | None) -> Iterable[AIConnector]:
        yielded: set[str] = set()
        if preferred:
            connector = self._resolve_connector(preferred, default=None)
            if connector is not None:
                yielded.add(connector.name)
                yield connector
        for connector in self._connectors:
            if connector.name in yielded:
                continue
            yield connector

    def _resolve_connector(self, name: str, default=_MISSING):
        for connector in self._connectors:
            if connector.name == name:
                return connector
        if default is _MISSING:
            raise AIProviderError(self.name, f"Unknown provider '{name}'", recoverable=False)
        return default

__all__ = ["FallbackConnector"]

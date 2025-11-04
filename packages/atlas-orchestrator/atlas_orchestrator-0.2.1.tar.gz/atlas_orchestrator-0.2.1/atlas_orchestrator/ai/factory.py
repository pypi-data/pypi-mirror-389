"""Factory helpers for building AI connectors from configuration."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import TypedDict

from atlas_orchestrator.config import ConfigError, ProviderSettings
from atlas_orchestrator.plugins import PluginRegistry

from .anthropic import AnthropicConnector
from .azure import AzureOpenAIConnector
from .base import AIConnector
from .openrouter import OpenRouterConnector

ConnectorFactory = Callable[[ProviderSettings], AIConnector]
_connectors = PluginRegistry[ConnectorFactory]("atlas_orchestrator.ai.providers")


def _register_builtins() -> None:
    _connectors.register("openrouter", _build_openrouter)
    _connectors.register("anthropic", _build_anthropic)
    _connectors.register("azure-openai", _build_azure)


class _ConnectorContext(TypedDict, total=False):
    api_key_env: str | None
    endpoint: str | None


def _base_kwargs(settings: ProviderSettings) -> _ConnectorContext:
    return {
        "api_key_env": settings.api_key_env,
        "endpoint": settings.endpoint,
    }


def _build_openrouter(settings: ProviderSettings) -> AIConnector:
    extras = dict(getattr(settings, "model_extra", {}))
    temperature = float(extras.get("temperature", 0.2))
    connector = OpenRouterConnector(
        temperature=temperature,
        model=settings.model,
        api_key=settings.api_key,
        api_key_env=settings.api_key_env,
        pricing=settings.pricing,
    )
    _attach_context(connector, settings)
    return connector


def _build_anthropic(settings: ProviderSettings) -> AIConnector:
    extras = dict(getattr(settings, "model_extra", {}))
    inject_failure = bool(extras.get("inject_failure", False))
    connector = AnthropicConnector(model=settings.model, inject_failure=inject_failure)
    _attach_context(connector, settings)
    return connector


def _build_azure(settings: ProviderSettings) -> AIConnector:
    extras = dict(getattr(settings, "model_extra", {}))
    deployment = str(extras.get("deployment", settings.model))
    api_version = str(extras.get("api_version", "2024-05-01"))
    outage_window = extras.get("outage_window")
    if isinstance(outage_window, list) and len(outage_window) == 2:
        outage_tuple = (int(outage_window[0]), int(outage_window[1]))
    else:
        outage_tuple = None
    connector = AzureOpenAIConnector(
        deployment=deployment,
        api_version=api_version,
        outage_window=outage_tuple,
    )
    _attach_context(connector, settings)
    return connector


def _attach_context(connector: AIConnector, settings: ProviderSettings) -> None:
    context = _base_kwargs(settings)
    if hasattr(connector, "metadata") and isinstance(getattr(connector, "metadata"), dict):
        connector.metadata.update({k: v for k, v in context.items() if v is not None})
    else:
        setattr(connector, "metadata", {k: v for k, v in context.items() if v is not None})

def _load_dynamic_factory(reference: str) -> ConnectorFactory:
    if ':' in reference:
        module_name, attribute = reference.split(':', 1)
    elif '.' in reference:
        module_name, attribute = reference.rsplit('.', 1)
    else:
        raise ConfigError(f"Invalid connector reference '{reference}'")
    module = import_module(module_name)
    factory = getattr(module, attribute)
    if not callable(factory):
        raise ConfigError(f"Connector factory '{reference}' is not callable")
    return factory

def get_connector_registry() -> PluginRegistry[ConnectorFactory]:
    if not _connectors.available():
        _register_builtins()
    return _connectors


def build_connector(settings: ProviderSettings) -> AIConnector:
    registry = get_connector_registry()
    try:
        factory = registry.get(settings.type)
    except KeyError:
        factory = _load_dynamic_factory(settings.type)
        registry.register(settings.type, factory)
    return factory(settings)


_register_builtins()


__all__ = ["build_connector", "ConnectorFactory", "get_connector_registry"]

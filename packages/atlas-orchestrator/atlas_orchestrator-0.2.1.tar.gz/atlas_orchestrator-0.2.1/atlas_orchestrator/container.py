"""Simple dependency container for wiring application services."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from typing import Any, Iterator

Provider = Callable[["DependencyContainer"], Any]


@dataclass
class _Binding:
    provider: Provider
    singleton: bool


class DependencyContainer:
    """Lightweight service locator supporting singleton and factory bindings."""

    def __init__(self) -> None:
        self._bindings: dict[str, _Binding] = {}
        self._singletons: dict[str, Any] = {}
        self._override_stack: list[dict[str, Any]] = []
        self._lock = RLock()

    def register_factory(self, key: str, provider: Provider) -> None:
        """Register a factory that returns a new instance each time."""

        with self._lock:
            self._bindings[key] = _Binding(provider=provider, singleton=False)
            self._singletons.pop(key, None)

    def register_singleton(self, key: str, provider: Provider) -> None:
        """Register a provider whose result is cached after first resolution."""

        with self._lock:
            self._bindings[key] = _Binding(provider=provider, singleton=True)
            self._singletons.pop(key, None)

    def register_instance(self, key: str, instance: Any) -> None:
        """Register a precomputed instance."""

        with self._lock:
            self._bindings.pop(key, None)
            self._singletons[key] = instance

    def resolve(self, key: str) -> Any:
        """Resolve a dependency, applying overrides and singleton caching."""

        with self._lock:
            override = self._lookup_override(key)
            if override is not None:
                return override

            if key in self._singletons:
                return self._singletons[key]

            binding = self._bindings.get(key)
            if binding is None:
                raise KeyError(f"No provider registered for '{key}'")

            instance = binding.provider(self)
            if binding.singleton:
                self._singletons[key] = instance
            return instance

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key in self._bindings or key in self._singletons

    @contextmanager
    def override(self, key: str, value: Any) -> Iterator[None]:
        """Temporarily override a binding within a context."""

        with self._lock:
            self._override_stack.append({key: value})
        try:
            yield
        finally:
            with self._lock:
                self._override_stack.pop()

    def _lookup_override(self, key: str) -> Any | None:
        for scope in reversed(self._override_stack):
            if key in scope:
                return scope[key]
        return None


__all__ = ["DependencyContainer"]


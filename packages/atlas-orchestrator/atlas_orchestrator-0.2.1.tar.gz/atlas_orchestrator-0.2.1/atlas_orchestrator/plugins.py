"""Plugin registry utilities for dynamic integrations."""

from __future__ import annotations

from collections.abc import Callable
from importlib import metadata
from typing import Generic, TypeVar

T = TypeVar("T")


class PluginRegistry(Generic[T]):
    """Lightweight entry-point backed plugin registry."""

    def __init__(self, group: str) -> None:
        self._group = group
        self._factories: dict[str, Callable[..., T]] = {}
        self._load_entry_points()

    def register(self, name: str, factory: Callable[..., T]) -> None:
        self._factories[name] = factory

    def unregister(self, name: str) -> None:
        self._factories.pop(name, None)

    def create(self, name: str, *args, **kwargs) -> T:
        factory = self.get(name)
        return factory(*args, **kwargs)

    def get(self, name: str) -> Callable[..., T]:
        try:
            return self._factories[name]
        except KeyError as exc:
            raise KeyError(f"No plugin registered for '{name}' in group '{self._group}'") from exc

    def available(self) -> list[str]:
        return sorted(self._factories)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._factories

    def _load_entry_points(self) -> None:
        try:
            entries = metadata.entry_points()
        except Exception:  # pragma: no cover - importlib guard
            return

        selector = getattr(entries, "select", None)
        if callable(selector):
            candidates = selector(group=self._group)
        else:  # pragma: no cover - python <3.10 fallback
            candidates = [ep for ep in entries if ep.group == self._group]
        for entry in candidates:
            try:
                factory = entry.load()
            except Exception:  # pragma: no cover - third-party load guard
                continue
            self._factories.setdefault(entry.name, factory)


__all__ = ["PluginRegistry"]

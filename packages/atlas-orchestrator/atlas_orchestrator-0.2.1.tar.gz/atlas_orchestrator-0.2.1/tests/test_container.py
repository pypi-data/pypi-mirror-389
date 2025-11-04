from __future__ import annotations

from atlas_orchestrator.container import DependencyContainer


def test_singleton_registration() -> None:
    container = DependencyContainer()
    calls: list[int] = []

    def provider(_: DependencyContainer) -> dict[str, int]:
        calls.append(1)
        return {"count": len(calls)}

    container.register_singleton("counter", provider)

    first = container.resolve("counter")
    second = container.resolve("counter")

    assert first is second
    assert first["count"] == 1


def test_factory_registration() -> None:
    container = DependencyContainer()

    container.register_factory("value", lambda _: object())

    assert container.resolve("value") is not container.resolve("value")


def test_override_context() -> None:
    container = DependencyContainer()
    container.register_instance("feature", False)

    with container.override("feature", True):
        assert container.resolve("feature") is True

    assert container.resolve("feature") is False


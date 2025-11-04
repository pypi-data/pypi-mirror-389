"""Tests for premium API webhook persistence and dispatch."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from atlas_orchestrator.premium_api import webhooks as webhooks_module
from atlas_orchestrator.premium_api.audit import AuditLogger
from atlas_orchestrator.premium_api.webhooks import WebhookConfig, WebhookDispatcher, WebhookRepository


def test_webhook_repository_roundtrip(tmp_path: Path) -> None:
    repo = WebhookRepository(tmp_path / "webhooks.db")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    configs = [
        WebhookConfig(
            webhook_id="primary",
            url="https://example.com/hook",
            secret="secret",
            events=("job.succeeded",),
            active=True,
            updated_at=now,
        ),
        WebhookConfig(
            webhook_id="secondary",
            url="https://example.net/hook",
            secret=None,
            events=(),
            active=False,
            updated_at=now,
        ),
    ]

    repo.upsert_many("cust-1", configs)

    loaded = repo.get("cust-1", "primary")
    assert loaded == configs[0]
    assert repo.get("cust-1", "missing") is None


def test_webhook_dispatcher_requires_start(tmp_path: Path) -> None:
    audit = AuditLogger(tmp_path / "audit.log")
    dispatcher = WebhookDispatcher(audit=audit)

    with pytest.raises(RuntimeError):
        dispatcher.enqueue(url="https://example.com/hook", secret=None, payload={})


def test_webhook_dispatcher_delivers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def run() -> None:
        events: list[dict[str, object]] = []
        delivered = asyncio.Event()

        class DummyResponse:
            status_code = 204

            def json(self) -> dict:
                return {}

            def raise_for_status(self) -> None:  # pragma: no cover - stub
                return

        class DummyClient:
            def __init__(self, timeout: float) -> None:
                self.timeout = timeout
                self.closed = False

            async def __aenter__(self) -> "DummyClient":
                return self

            async def __aexit__(self, exc_type, exc, traceback) -> bool:
                return False

            async def post(self, url: str, content=None, headers=None) -> DummyResponse:  # type: ignore[override]
                events.append({"url": url, "content": content, "headers": headers})
                delivered.set()
                return DummyResponse()

            async def aclose(self) -> None:
                self.closed = True

        monkeypatch.setattr(webhooks_module.httpx, "AsyncClient", DummyClient)

        class InMemoryAudit:
            def __init__(self) -> None:
                self.events: list[tuple[str, dict[str, object]]] = []

            def record(self, event_type: str, payload: dict[str, object]) -> None:
                self.events.append((event_type, payload))

        audit = InMemoryAudit()
        dispatcher = WebhookDispatcher(audit=audit)

        await dispatcher.start()
        dispatcher.enqueue(
            url="https://example.com/hook",
            secret="shh",
            payload={"event": "job.succeeded", "job_id": "123"},
        )

        await asyncio.wait_for(delivered.wait(), timeout=1)
        await dispatcher.stop()

        assert audit.events and audit.events[0][0] == "webhook.delivered"
        call = events[0]
        headers = call["headers"]
        assert headers["Content-Type"] == "application/json"
        assert "X-AO-Signature" in headers
        body = json.loads(call["content"])
        assert body["event"] == "job.succeeded"

    asyncio.run(run())

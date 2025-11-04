"""Tests for premium API completion providers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from atlas_orchestrator.premium_api import providers as providers_module
from atlas_orchestrator.premium_api.models import (
    CustomerContext,
    JobRequestPayload,
    QueueJob,
    RateLimitSettings,
)
from atlas_orchestrator.premium_api.providers import OpenRouterCompletionProvider


def _make_queue_job(**payload_overrides) -> QueueJob:
    payload = JobRequestPayload(
        model="openrouter/gpt-5",
        messages=[{"role": "user", "content": "ping"}],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=256,
        **payload_overrides,
    )
    return QueueJob(
        job_id=uuid4(),
        customer_id="cust-123",
        payload=payload,
        submitted_at=datetime.now(timezone.utc),
        customer_context=CustomerContext(
            key_id="key-1",
            customer_id="cust-123",
            plan_tier="pro",
            rate_limit=RateLimitSettings(per_minute=10, burst=20),
            premium_rate=0.15,
        ),
    )


def test_openrouter_completion_provider_makes_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the provider forwards payload fields and shapes the response usage block."""

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self) -> dict:
            return {
                "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 24,
                    "total_tokens": 36,
                    "total_cost": "0.00123",
                },
                "pricing": {"prompt": 0.0001, "completion": 0.0002},
            }

        def raise_for_status(self) -> None:  # pragma: no cover - behaviour stubbed
            return

    class DummyAsyncClient:
        calls: list[dict[str, object]] = []

        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> bool:
            return False

        async def post(self, url: str, json=None, headers=None) -> DummyResponse:  # type: ignore[override]
            self.__class__.calls.append(
                {"url": url, "json": json, "headers": headers, "timeout": self.timeout}
            )
            return DummyResponse()

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", DummyAsyncClient)

    async def run() -> None:
        provider = OpenRouterCompletionProvider(
            api_key="sk-test",
            endpoint="https://example.com/chat",
        )
        job = _make_queue_job()
        result, usage = await provider.complete(job)

        assert DummyAsyncClient.calls, "expected HTTP call"
        call = DummyAsyncClient.calls[0]
        assert call["url"] == "https://example.com/chat"
        assert call["json"]["model"] == "openrouter/gpt-5"
        assert call["json"]["response_format"] == {"type": "json_object"}
        assert call["json"]["temperature"] == 0.2
        assert call["json"]["max_tokens"] == 256
        assert call["headers"]["Authorization"] == "Bearer sk-test"

        assert result["type"] == "chat.completion"
        assert result["messages"][0]["content"] == "pong"
        assert usage["prompt_tokens"] == 12
        assert usage["openrouter_cost"] == {"value": "0.001230", "currency": "USD"}
        assert usage["pricing"] == {"prompt": 0.0001, "completion": 0.0002}

    import asyncio

    asyncio.run(run())


def test_openrouter_build_usage_ignores_invalid_cost() -> None:
    """Non-numeric total_cost should be ignored gracefully."""

    provider = OpenRouterCompletionProvider(api_key="sk-test")
    report = provider._build_usage(  # type: ignore[attr-defined]
        {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12, "total_cost": "not-a-number"},
        pricing=None,
    )

    assert report["prompt_tokens"] == 5
    assert "openrouter_cost" not in report

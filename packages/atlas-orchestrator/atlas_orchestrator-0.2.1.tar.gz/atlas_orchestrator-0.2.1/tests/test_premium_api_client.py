from __future__ import annotations

import json
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx

from atlas_orchestrator.premium_api.client import (
    PremiumApiClient,
    WebhookDefinition,
)
from atlas_orchestrator.premium_api.models import JobStatus


def test_submit_and_wait_with_callbacks() -> None:
    job_id = "job-123"
    submitted_at = datetime.now(timezone.utc)
    started_at = submitted_at + timedelta(seconds=1)
    completed_at = submitted_at + timedelta(seconds=5)
    poll_count = {"value": 0}

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST" and request.url.path == "/v1/jobs":
                assert request.headers["authorization"] == "Bearer test-key"
                payload = json.loads(request.content)
                assert payload["model"] == "gpt-4o"
                assert payload["messages"][0]["role"] == "user"
                return httpx.Response(
                    status_code=202,
                    json={
                        "job_id": job_id,
                        "status": "pending",
                        "submitted_at": submitted_at.isoformat(),
                        "poll_after": (submitted_at + timedelta(seconds=1)).isoformat(),
                    },
                )
            if request.method == "GET" and request.url.path == f"/v1/jobs/{job_id}":
                poll_count["value"] += 1
                if poll_count["value"] == 1:
                    return httpx.Response(
                        status_code=202,
                        json={
                            "job_id": job_id,
                            "status": "running",
                            "submitted_at": submitted_at.isoformat(),
                            "started_at": started_at.isoformat(),
                        },
                    )
                return httpx.Response(
                    status_code=200,
                    json={
                        "job_id": job_id,
                        "status": "succeeded",
                        "submitted_at": submitted_at.isoformat(),
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "result": {"messages": [{"role": "assistant", "content": "done"}]},
                        "usage": {
                            "premium": {"rate": 0.10, "value": "0.001000"},
                            "total_billed": {"value": "0.011000", "currency": "USD"},
                            "openrouter_cost": {"value": "0.010000", "currency": "USD"},
                        },
                    },
                )
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        updates: list[JobStatus] = []
        final_status: list[JobStatus] = []

        async def on_update(details) -> None:
            updates.append(details.status)

        async def on_result(details) -> None:
            final_status.append(details.status)

        async with PremiumApiClient(
            base_url="https://premium.example.com",
            api_key="test-key",
            transport=transport,
            timeout=1.0,
        ) as client:
            details = await client.submit_and_wait(
                model="gpt-4o",
                messages=[{"role": "user", "content": "ping"}],
                poll_interval=0.0,
                respect_poll_after=False,
                on_update=on_update,
                on_result=on_result,
            )

        assert poll_count["value"] == 2
        assert updates == [JobStatus.running, JobStatus.succeeded]
        assert final_status == [JobStatus.succeeded]
        assert details.status is JobStatus.succeeded
        assert details.usage is not None
        assert details.usage.total_billed_value == Decimal("0.011000")
        assert details.usage.openrouter_cost == Decimal("0.010000")
        assert details.result is not None
        assert details.result["messages"][0]["content"] == "done"

    asyncio.run(run_test())


def test_list_usage_parses_billing() -> None:
    usage_payload: dict[str, Any] = {
        "data": [
            {
                "usage_id": "use_1",
                "job_id": "job-1",
                "customer_id": "cust-1",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "premium": {"rate": 0.2, "value": "0.500000"},
                "total_billed": {"value": "1.000000", "currency": "USD"},
                "openrouter_cost": {"value": "0.500000", "currency": "USD"},
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300,
            }
        ],
        "has_more": True,
        "next_cursor": "use_1",
    }

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET" and request.url.path == "/v1/usage":
                assert request.headers["authorization"] == "Bearer test-key"
                return httpx.Response(status_code=200, json=usage_payload)
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)

        async with PremiumApiClient(
            base_url="https://premium.example.com",
            api_key="test-key",
            transport=transport,
        ) as client:
            page = await client.list_usage(limit=10)

        assert page.has_more is True
        assert page.next_cursor == "use_1"
        assert len(page.records) == 1
        record = page.records[0]
        assert record.charges.premium_rate == 0.2
        assert record.charges.premium_value == Decimal("0.500000")
        assert record.charges.total_billed_value == Decimal("1.000000")
        assert record.charges.openrouter_cost == Decimal("0.500000")
        assert record.charges.total_tokens == 300

    asyncio.run(run_test())


def test_upsert_webhooks_returns_sanitized_info() -> None:
    updated_at = datetime.now(timezone.utc).isoformat()

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "PUT" and request.url.path == "/v1/webhooks":
                payload = json.loads(request.content)
                assert payload["webhooks"][0]["id"] == "default"
                return httpx.Response(
                    status_code=200,
                    json={
                        "webhooks": [
                            {
                                "id": "default",
                                "url": "https://example.com/hook",
                                "events": ["job.succeeded", "job.failed"],
                                "active": True,
                                "updated_at": updated_at,
                            }
                        ]
                    },
                )
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        definition = WebhookDefinition(
            webhook_id="default",
            url="https://example.com/hook",
            events=("job.succeeded",),
            secret="shh",
            active=True,
        )

        async with PremiumApiClient(
            base_url="https://premium.example.com",
            api_key="test-key",
            transport=transport,
        ) as client:
            webhooks = await client.upsert_webhooks([definition])

        assert len(webhooks) == 1
        info = webhooks[0]
        assert info.webhook_id == "default"
        assert "job.succeeded" in info.events
        assert info.active is True
        assert isinstance(info.updated_at, datetime)

    asyncio.run(run_test())

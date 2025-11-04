"""Tests for premium API observability exporters."""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from atlas_orchestrator.premium_api import observability
from atlas_orchestrator.premium_api.config import ObservabilitySettings


def _settings(**overrides) -> ObservabilitySettings:
    defaults = {
        "prometheus_push_url": None,
        "prometheus_job": "atlas_orchestrator_premium_api",
        "prometheus_instance": None,
        "prometheus_push_interval_seconds": 0.1,
        "otel_endpoint": None,
        "otel_headers": {},
        "log_endpoint": None,
        "log_api_key_env": None,
        "latency_threshold_ms": 2000,
        "error_rate_threshold": 0.05,
        "queue_depth_threshold": 50,
    }
    defaults.update(overrides)
    return ObservabilitySettings(**defaults)


def test_configure_prometheus_push(monkeypatch: pytest.MonkeyPatch) -> None:
    observability.reset()
    calls: list[dict[str, object]] = []
    triggered = threading.Event()

    def _fake_request(method: str, url: str, **kwargs):
        content = kwargs.get("content")
        decoded = content.decode("utf-8") if isinstance(content, (bytes, bytearray)) else content
        calls.append({"method": method, "url": url, "content": decoded})
        triggered.set()
        return SimpleNamespace(status_code=202)

    monkeypatch.setattr("atlas_orchestrator.premium_api.observability.httpx.request", _fake_request)

    settings = _settings(
        prometheus_push_url="https://push.example",
        prometheus_job="premium",
        prometheus_instance="local",
        prometheus_push_interval_seconds=0.05,
    )
    observability.configure(settings)
    observability.record_request("GET", "/healthz", 200, 0.02)
    assert triggered.wait(0.5)
    observability.reset()

    assert calls, "expected metrics push to occur"
    first = calls[0]
    assert first["method"] == "PUT"
    assert first["url"] == "https://push.example/metrics/job/premium/instance/local"
    assert "atlas_orchestrator_premium_api_requests_total" in str(first["content"])


def test_ship_log_posts_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    observability.reset()
    posts: list[dict[str, object]] = []
    delivered = threading.Event()

    def _fake_post(url: str, *, json=None, headers=None, timeout=None):
        posts.append({"url": url, "json": json, "headers": headers})
        delivered.set()
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr("atlas_orchestrator.premium_api.observability.httpx.post", _fake_post)

    settings = _settings(log_endpoint="https://logs.example")
    observability.configure(settings)
    observability.ship_log({"event": "test_event", "http_status": 200})
    assert delivered.wait(0.5)
    observability.reset()

    assert posts, "expected log shipment"
    entry = posts[0]
    assert entry["url"] == "https://logs.example"
    assert entry["json"]["event"] == "test_event"


def test_alert_thresholds_reflect_configuration() -> None:
    observability.reset()
    settings = _settings(
        latency_threshold_ms=1500,
        error_rate_threshold=0.02,
        queue_depth_threshold=10,
    )
    observability.configure(settings)
    thresholds = observability.alert_thresholds()
    observability.reset()

    assert thresholds == {
        "latency_ms_p95": 1500,
        "error_rate": 0.02,
        "queue_depth": 10,
    }

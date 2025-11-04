"""Lightweight observability helpers for the premium API."""

from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, Iterator

import httpx

from fastapi import Response
from fastapi.responses import JSONResponse

from atlas_orchestrator.premium_api.config import ObservabilitySettings

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace  # type: ignore
except Exception:  # pragma: no cover - fallback path
    trace = None  # type: ignore

LOGGER = logging.getLogger("atlas_orchestrator.premium_api.observability")

_lock = threading.Lock()
_config_lock = threading.Lock()
_request_counters: dict[tuple[str, str, int], int] = {}
_request_latency_sum: dict[tuple[str, str], float] = {}
_request_latency_count: dict[tuple[str, str], int] = {}
_job_submissions: dict[str, int] = {}
_job_completions: dict[str, int] = {}
_queue_depth: float = 0.0
_start_time = time.time()
_config: ObservabilitySettings | None = None
_push_thread: threading.Thread | None = None
_push_stop = threading.Event()
_log_executor: ThreadPoolExecutor | None = None
_DEFAULT_LATENCY_THRESHOLD_MS = 2000
_DEFAULT_ERROR_RATE_THRESHOLD = 0.05
_DEFAULT_QUEUE_DEPTH_THRESHOLD = 50
_tracer_provider: Any | None = None


def record_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    key = (method, path, status_code)
    with _lock:
        _request_counters[key] = _request_counters.get(key, 0) + 1
        latency_key = (method, path)
        _request_latency_sum[latency_key] = _request_latency_sum.get(latency_key, 0.0) + duration_seconds
        _request_latency_count[latency_key] = _request_latency_count.get(latency_key, 0) + 1


def record_job_submission(plan_tier: str) -> None:
    with _lock:
        _job_submissions[plan_tier] = _job_submissions.get(plan_tier, 0) + 1


def record_job_completion(status: str) -> None:
    with _lock:
        _job_completions[status] = _job_completions.get(status, 0) + 1


def record_queue_depth(depth: int | float | None) -> None:
    if depth is None:
        return
    with _lock:
        global _queue_depth
        _queue_depth = float(depth)


def configure(settings: ObservabilitySettings) -> None:
    """Configure remote exporters and alert thresholds."""
    global _config
    _stop_push_thread()
    if not settings.log_endpoint:
        _shutdown_log_executor()
    with _config_lock:
        _config = settings
    if settings.otel_endpoint:
        _configure_tracer(settings)
    else:
        _shutdown_tracer_provider()
    if settings.prometheus_push_url:
        _start_push_thread()


def alert_thresholds() -> dict[str, Any]:
    """Return alert threshold guidance derived from configuration."""
    settings = _current_config()
    if settings is None:
        return {
            "latency_ms_p95": _DEFAULT_LATENCY_THRESHOLD_MS,
            "error_rate": _DEFAULT_ERROR_RATE_THRESHOLD,
            "queue_depth": _DEFAULT_QUEUE_DEPTH_THRESHOLD,
        }
    return {
        "latency_ms_p95": settings.latency_threshold_ms,
        "error_rate": settings.error_rate_threshold,
        "queue_depth": settings.queue_depth_threshold,
    }


def ship_log(payload: dict[str, Any]) -> None:
    """Send a structured log payload to the configured endpoint."""
    settings = _current_config()
    if settings is None or not settings.log_endpoint:
        return
    headers = {"Content-Type": "application/json"}
    if settings.log_api_key_env:
        token = os.getenv(settings.log_api_key_env)
        if token:
            headers["Authorization"] = f"Bearer {token}"
    executor = _ensure_log_executor()
    if executor is None:
        return
    executor.submit(_post_log, settings.log_endpoint, headers, dict(payload))


def _current_config() -> ObservabilitySettings | None:
    with _config_lock:
        return _config


def _start_push_thread() -> None:
    global _push_thread
    if _push_thread is not None and _push_thread.is_alive():
        return
    _push_stop.clear()
    _push_thread = threading.Thread(target=_push_loop, name="premium-api-metrics", daemon=True)
    _push_thread.start()


def _stop_push_thread() -> None:
    global _push_thread
    if _push_thread is None:
        return
    _push_stop.set()
    _push_thread.join(timeout=1.0)
    _push_thread = None
    _push_stop.clear()


def _push_loop() -> None:
    while not _push_stop.is_set():
        settings = _current_config()
        if settings is None or not settings.prometheus_push_url:
            if _push_stop.wait(1.0):
                break
            continue
        interval = max(settings.prometheus_push_interval_seconds, 0.1)
        if _push_stop.wait(interval):
            break
        try:
            _push_metrics_once(settings)
        except Exception:  # pragma: no cover - defensive guard
            LOGGER.exception("premium_api_metrics_push_failed")


def _push_metrics_once(settings: ObservabilitySettings) -> None:
    metrics = _render_metrics()
    base = settings.prometheus_push_url.rstrip("/")
    path = f"{base}/metrics/job/{settings.prometheus_job}"
    if settings.prometheus_instance:
        path = f"{path}/instance/{settings.prometheus_instance}"
    headers = {"Content-Type": "text/plain; version=0.0.4"}
    try:
        httpx.request(
            "PUT",
            path,
            content=metrics.encode("utf-8"),
            headers=headers,
            timeout=5.0,
        )
    except httpx.HTTPError as exc:  # pragma: no cover - network guard
        LOGGER.debug(
            "premium_api_prometheus_push_failed",
            extra={"event": "premium_api.prometheus.push_failed", "error": str(exc)},
        )


def _ensure_log_executor() -> ThreadPoolExecutor | None:
    global _log_executor
    if _log_executor is None:
        try:
            _log_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="premium-api-log")
        except Exception:  # pragma: no cover - resource guard
            LOGGER.debug("premium_api_log_executor_failed")
            return None
    return _log_executor


def _shutdown_log_executor() -> None:
    global _log_executor
    if _log_executor is None:
        return
    _log_executor.shutdown(wait=True, cancel_futures=True)
    _log_executor = None


def _post_log(endpoint: str, headers: dict[str, str], payload: dict[str, Any]) -> None:
    try:
        httpx.post(endpoint, json=payload, headers=headers, timeout=5.0)
    except httpx.HTTPError as exc:  # pragma: no cover - network guard
        LOGGER.debug(
            "premium_api_log_ship_failed",
            extra={"event": "premium_api.log_ship_failed", "error": str(exc)},
        )


def _configure_tracer(settings: ObservabilitySettings) -> None:
    if trace is None:  # pragma: no cover - depends on optional dependency
        LOGGER.debug("premium_api_otel_disabled_missing_runtime")
        return
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception:  # pragma: no cover - optional dependency not installed
        LOGGER.debug("premium_api_otel_components_missing")
        return

    global _tracer_provider
    _shutdown_tracer_provider()
    headers = settings.otel_headers or {}
    try:
        exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint, headers=headers or None)
    except Exception as exc:  # pragma: no cover - exporter instantiation failure
        LOGGER.debug(
            "premium_api_otel_exporter_init_failed",
            extra={"event": "premium_api.otel.exporter_failed", "error": str(exc)},
        )
        return
    resource = Resource.create({"service.name": "atlas-orchestrator-premium-api"})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def _shutdown_tracer_provider() -> None:
    global _tracer_provider
    if _tracer_provider is None:
        return
    try:
        _tracer_provider.shutdown()
    except Exception:  # pragma: no cover - defensive guard
        LOGGER.debug("premium_api_otel_shutdown_failed")
    _tracer_provider = None


def _render_metrics() -> str:
    lines: list[str] = []
    lines.append("# HELP atlas_orchestrator_premium_api_requests_total Total HTTP requests processed")
    lines.append("# TYPE atlas_orchestrator_premium_api_requests_total counter")
    with _lock:
        for (method, path, status_code), value in sorted(_request_counters.items()):
            lines.append(
                f'atlas_orchestrator_premium_api_requests_total{{method="{method}",path="{path}",status="{status_code}"}} {value}'
            )

        lines.append("# HELP atlas_orchestrator_premium_api_request_duration_seconds_sum Sum of request latencies in seconds")
        lines.append("# TYPE atlas_orchestrator_premium_api_request_duration_seconds_sum gauge")
        for (method, path), total in sorted(_request_latency_sum.items()):
            lines.append(
                f'atlas_orchestrator_premium_api_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total}'
            )

        lines.append("# HELP atlas_orchestrator_premium_api_request_duration_seconds_count Count of recorded request latencies")
        lines.append("# TYPE atlas_orchestrator_premium_api_request_duration_seconds_count gauge")
        for (method, path), count in sorted(_request_latency_count.items()):
            lines.append(
                f'atlas_orchestrator_premium_api_request_duration_seconds_count{{method="{method}",path="{path}"}} {count}'
            )

        lines.append("# HELP atlas_orchestrator_premium_api_jobs_submitted_total Jobs submitted by plan tier")
        lines.append("# TYPE atlas_orchestrator_premium_api_jobs_submitted_total counter")
        for tier, value in sorted(_job_submissions.items()):
            lines.append(f'atlas_orchestrator_premium_api_jobs_submitted_total{{plan_tier="{tier}"}} {value}')

        lines.append("# HELP atlas_orchestrator_premium_api_jobs_completed_total Jobs completed by terminal status")
        lines.append("# TYPE atlas_orchestrator_premium_api_jobs_completed_total counter")
        for status, value in sorted(_job_completions.items()):
            lines.append(f'atlas_orchestrator_premium_api_jobs_completed_total{{status="{status}"}} {value}')

        lines.append("# HELP atlas_orchestrator_premium_api_queue_depth Current queue depth observed by worker")
        lines.append("# TYPE atlas_orchestrator_premium_api_queue_depth gauge")
        lines.append(f"atlas_orchestrator_premium_api_queue_depth {_queue_depth}")

        uptime = time.time() - _start_time

    lines.append("# HELP atlas_orchestrator_premium_api_uptime_seconds Service uptime in seconds")
    lines.append("# TYPE atlas_orchestrator_premium_api_uptime_seconds gauge")
    lines.append(f"atlas_orchestrator_premium_api_uptime_seconds {uptime}")

    return "\n".join(lines) + "\n"


def metrics_response() -> Response:
    """Return a Prometheus-compatible metrics payload."""
    payload = _render_metrics()
    return Response(content=payload, media_type="text/plain; version=0.0.4")


def health_payload() -> dict[str, Any]:
    with _lock:
        uptime = time.time() - _start_time
        queue_depth = _queue_depth
    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "queue_depth": queue_depth,
    }


def health_response() -> JSONResponse:
    return JSONResponse(health_payload())


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
    if trace is None:  # pragma: no cover - span disabled
        yield
        return
    tracer = trace.get_tracer("atlas_orchestrator.premium_api")
    with tracer.start_as_current_span(name) as span:  # pragma: no cover - requires OTel runtime
        if attributes:
            for key, value in attributes.items():
                try:
                    span.set_attribute(key, value)
                except Exception:
                    continue
        yield


def reset() -> None:
    """Reset collected metrics; primarily for test isolation."""
    _stop_push_thread()
    _shutdown_log_executor()
    _shutdown_tracer_provider()
    with _config_lock:
        global _config
        _config = None
    with _lock:
        _request_counters.clear()
        _request_latency_sum.clear()
        _request_latency_count.clear()
        _job_submissions.clear()
        _job_completions.clear()
        global _queue_depth, _start_time
        _queue_depth = 0.0
        _start_time = time.time()

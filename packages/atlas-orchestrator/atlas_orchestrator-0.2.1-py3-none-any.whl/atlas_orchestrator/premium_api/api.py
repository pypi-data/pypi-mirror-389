"""FastAPI application for the premium API surface."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from . import observability
from .auth import APIKeyAuth
from .audit import AuditLogger
from .billing import BillingEngine
from .config import TLSSettings
from .models import CustomerContext, JobRequestPayload, JobStatus
from .rate_limiter import RateLimiter
from .security import DEFAULT_SECURITY, SecurityPolicy
from .services import JobService, KeyService
from .webhooks import WebhookConfig, WebhookDispatcher, WebhookRepository

LOGGER = logging.getLogger("atlas_orchestrator.premium_api.api")


def _job_response(record, result) -> dict[str, Any]:
    body: dict[str, Any] = {
        "job_id": str(record.job_id),
        "status": record.status.value,
        "submitted_at": record.created_at.isoformat(),
    }
    if record.started_at:
        body["started_at"] = record.started_at.isoformat()
    if record.completed_at:
        body["completed_at"] = record.completed_at.isoformat()
    if record.metadata:
        body["metadata"] = record.metadata
    if record.status == JobStatus.succeeded and result:
        body["result"] = result.result
        body["usage"] = result.usage
    if record.status == JobStatus.failed and result:
        body["error"] = {
            "code": result.error_code,
            "message": result.error_message,
        }
    if record.status == JobStatus.cancelled:
        body["error"] = {"code": "cancelled", "message": "Job cancelled by user"}
    return body


def create_app(
    *,
    key_service: KeyService,
    job_service: JobService,
    rate_limiter: RateLimiter,
    audit_logger: AuditLogger,
    webhook_repository: WebhookRepository,
    dispatcher: WebhookDispatcher,
    billing: BillingEngine,
    security_policy: SecurityPolicy | None = None,
    tls_settings: TLSSettings | None = None,
) -> FastAPI:
    app = FastAPI(title="Atlas Orchestrator Premium API", version="0.1.0")
    tls = tls_settings
    if tls and tls.require_https:
        @app.middleware("http")
        async def enforce_https(request: Request, call_next):
            if _is_secure_request(request, tls):
                response = await call_next(request)
                if tls.hsts_enabled:
                    response.headers.setdefault(
                        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
                    )
                return response
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, content={"detail": "https_required"}
            )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        route = request.scope.get("route")
        route_path = getattr(route, "path", None) or request.url.path
        with observability.start_span(
            "premium_api.http_request",
            {
                "http.method": request.method,
                "http.route": route_path,
            },
        ):
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                duration = time.perf_counter() - start
                observability.record_request(request.method, route_path, status_code, duration)
                log_payload = {
                    "event": "premium_api.request",
                    "http_method": request.method,
                    "http_route": route_path,
                    "http_status": status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
                LOGGER.info("premium_api_request", extra=log_payload)
                observability.ship_log(log_payload)

    policy = security_policy or DEFAULT_SECURITY
    auth = APIKeyAuth(key_service, rate_limiter, audit_logger, security=policy)

    async def resolve_context(request: Request) -> CustomerContext:
        return await auth(request)

    @app.post("/v1/jobs", status_code=status.HTTP_202_ACCEPTED)
    async def submit_job(
        payload: JobRequestPayload,
        context: CustomerContext = Depends(resolve_context),
    ) -> dict[str, Any]:
        webhook_details = None
        if payload.webhook:
            webhook_details = _resolve_webhook_details(
                payload.webhook,
                customer_id=context.customer_id,
                repository=webhook_repository,
            )
        record = await job_service.submit(
            payload=payload,
            context=context,
            webhook=webhook_details,
        )
        return {
            "job_id": str(record.job_id),
            "status": record.status.value,
            "submitted_at": record.created_at.isoformat(),
            "poll_after": (record.created_at + timedelta(seconds=2)).isoformat(),
        }

    @app.get("/v1/jobs/{job_id}")
    async def get_job(
        job_id: UUID,
        context: CustomerContext = Depends(resolve_context),
    ) -> Any:
        record = job_service.get(job_id)
        if record is None or record.customer_id != context.customer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")
        result = job_service.get_result(job_id)
        if record.status in {JobStatus.pending, JobStatus.running}:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "job_id": str(record.job_id),
                    "status": record.status.value,
                    "submitted_at": record.created_at.isoformat(),
                },
            )
        response = _job_response(record, result)
        return response

    @app.post("/v1/jobs/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
    async def cancel_job(
        job_id: UUID,
        context: CustomerContext = Depends(resolve_context),
    ) -> dict[str, Any]:
        record = job_service.get(job_id)
        if record is None or record.customer_id != context.customer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")
        updated = job_service.cancel(job_id)
        return {
            "job_id": str(updated.job_id),
            "status": updated.status.value,
        }

    @app.put("/v1/webhooks")
    async def upsert_webhooks(
        payload: dict[str, Any],
        context: CustomerContext = Depends(resolve_context),
    ) -> dict[str, Any]:
        entries = payload.get("webhooks") or []
        now = datetime.now(timezone.utc)
        configs = []
        for raw in entries:
            webhook_id = raw.get("id") or raw.get("shared_secret_id") or raw.get("webhook_id")
            if not webhook_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webhook_id_required")
            url = raw.get("url")
            if not url:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webhook_url_required")
            secret = raw.get("secret")
            events = raw.get("events") or ["job.succeeded", "job.failed"]
            configs.append(
                WebhookConfig(
                    webhook_id=webhook_id,
                    url=url,
                    secret=secret,
                    events=tuple(events),
                    active=bool(raw.get("active", True)),
                    updated_at=now,
                )
            )
        webhook_repository.upsert_many(context.customer_id, configs)
        sanitized = [
            {
                "id": config.webhook_id,
                "url": config.url,
                "events": list(config.events),
                "active": config.active,
                "updated_at": config.updated_at.isoformat(),
            }
            for config in configs
        ]
        return {"webhooks": sanitized}

    @app.get("/v1/usage")
    async def list_usage(
        context: CustomerContext = Depends(resolve_context),
        limit: int = Query(50, ge=1, le=100),
        starting_after: UUID | None = None,
        ending_before: UUID | None = None,
        from_ts: datetime | None = Query(None, alias="from"),
        to_ts: datetime | None = Query(None, alias="to"),
    ) -> dict[str, Any]:
        def _normalize(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        normalized_from = _normalize(from_ts)
        normalized_to = _normalize(to_ts)
        if normalized_from and normalized_to and normalized_from > normalized_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_range")

        raw_records = billing.list_usage(
            context.customer_id,
            limit=limit + 1,
            starting_after=starting_after,
            ending_before=ending_before,
            start=normalized_from,
            end=normalized_to,
        )
        has_more = len(raw_records) > limit
        records = raw_records[:limit]
        response: dict[str, Any] = {"data": records, "has_more": has_more}
        if has_more and records:
            response["next_cursor"] = records[-1]["usage_id"]
        return response

    @app.get("/metrics")
    async def metrics() -> Any:
        return observability.metrics_response()

    @app.get("/healthz")
    async def health() -> Any:
        return observability.health_response()

    return app


def _is_secure_request(request: Request, tls: TLSSettings) -> bool:
    if not tls.require_https or tls.mode == "off":
        return True
    scheme = request.url.scheme
    forwarded = request.headers.get("x-forwarded-proto", "")
    if forwarded:
        forwarded = forwarded.split(",")[0].strip().lower()
    if tls.mode == "terminate":
        return scheme == "https"
    if tls.mode == "forwarded":
        if forwarded:
            return forwarded == "https"
        return scheme == "https"
    return scheme == "https"


def _resolve_webhook_details(
    payload: dict[str, Any],
    *,
    customer_id: str,
    repository: WebhookRepository,
) -> dict[str, object]:
    identifier = payload.get("id") or payload.get("shared_secret_id")
    direct_url = payload.get("url")
    if identifier:
        config = repository.get(customer_id, identifier)
        if config is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webhook_not_found")
        return {
            "id": config.webhook_id,
            "url": config.url,
            "secret": config.secret,
            "events": list(config.events) or ["job.succeeded", "job.failed"],
        }
    if direct_url:
        events = payload.get("events") or ["job.succeeded", "job.failed"]
        details: dict[str, object] = {
            "url": direct_url,
            "events": events,
        }
        if payload.get("secret"):
            details["secret"] = payload["secret"]
        return details
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webhook_url_required")

"""Integration tests for premium API FastAPI surface."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from atlas_orchestrator.premium_api import observability
from atlas_orchestrator.premium_api.api import create_app
from atlas_orchestrator.premium_api.audit import AuditLogger
from atlas_orchestrator.premium_api.billing import BillingEngine, SqliteBillingRepository
from atlas_orchestrator.premium_api.config import (
    IpFilterSettings,
    RequestSigningSettings,
    SecuritySettings,
    TLSSettings,
    WAFSettings,
)
from atlas_orchestrator.premium_api.hashing import Argon2KeyHasher
from atlas_orchestrator.premium_api.jobs import SqliteJobRepository
from atlas_orchestrator.premium_api.models import CustomerContext, JobStatus, RateLimitSettings
from atlas_orchestrator.premium_api.queue import InMemoryJobQueue
from atlas_orchestrator.premium_api.rate_limiter import InMemoryRateLimiter
from atlas_orchestrator.premium_api.secrets import FileSigningSecretProvider, SigningSecretProvider
from atlas_orchestrator.premium_api.security import SecurityPolicy
from atlas_orchestrator.premium_api.services import JobService, KeyService
from atlas_orchestrator.premium_api.storage import SqliteApiKeyRepository
from atlas_orchestrator.premium_api.webhooks import WebhookRepository


class _StubDispatcher:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def enqueue(self, *, url: str, secret: str | None, payload: dict[str, object]) -> None:
        self.events.append({"url": url, "secret": secret, "payload": payload})


class _StubProvider:
    def __init__(self, *, cost: float = 0.01) -> None:
        self._cost = cost

    async def complete(self, job):
        usage: dict[str, object] = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        if self._cost is not None:
            usage["openrouter_cost"] = {"value": f"{self._cost:.6f}", "currency": "USD"}
        return (
            {
                "type": "chat.completion",
                "messages": [{"role": "assistant", "content": "stub response"}],
            },
            usage,
        )


class _DictSecretProvider(SigningSecretProvider):
    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def set_secret(self, identifier: str, secret: str) -> None:
        self._secrets[identifier] = secret

    def get_secret(self, context: CustomerContext) -> str | None:
        for candidate in (context.signing_key_id, context.key_id, context.customer_id):
            if candidate and candidate in self._secrets:
                return self._secrets[candidate]
        return None


def _compute_signature(secret: str, method: str, path: str, timestamp: str, body: bytes) -> str:
    payload = b"|".join(
        [
            timestamp.encode("utf-8"),
            method.upper().encode("utf-8"),
            path.encode("utf-8"),
            body,
        ]
    )
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _build_components(
    tmp_path,
    *,
    default_rate: RateLimitSettings,
    key_security: SecuritySettings | None = None,
    security_policy: SecurityPolicy | None = None,
    tls_settings: TLSSettings | None = None,
) -> tuple:
    observability.reset()
    db_path = tmp_path / "premium.db"
    audit = AuditLogger(tmp_path / "audit.log")
    key_repo = SqliteApiKeyRepository(db_path)
    job_repo = SqliteJobRepository(db_path)
    billing_repo = SqliteBillingRepository(db_path)
    queue = InMemoryJobQueue()
    webhooks = WebhookRepository(db_path)
    dispatcher = _StubDispatcher()
    key_service = KeyService(
        repository=key_repo,
        hasher=Argon2KeyHasher(),
        audit=audit,
        key_prefix="ao_live_",
        prefix_length=16,
        default_rate_limit=default_rate,
        security=key_security,
    )
    billing_engine = BillingEngine(repository=billing_repo, audit=audit)
    job_service = JobService(
        repository=job_repo,
        queue=queue,
        audit=audit,
        dispatcher=dispatcher,
        billing=billing_engine,
    )
    rate_limiter = InMemoryRateLimiter()
    app = create_app(
        key_service=key_service,
        job_service=job_service,
        rate_limiter=rate_limiter,
        audit_logger=audit,
        webhook_repository=webhooks,
        dispatcher=dispatcher,
        billing=billing_engine,
        security_policy=security_policy,
        tls_settings=tls_settings,
    )
    return app, key_service, job_service, queue, rate_limiter, webhooks, dispatcher, billing_repo, billing_engine


def _process_single_job(queue: InMemoryJobQueue, job_service: JobService, *, cost: float = 0.01) -> None:
    async def _process() -> None:
        job = await queue.dequeue(timeout=0.2)
        job_service.mark_running(job.job_id)
        provider = _StubProvider(cost=cost)
        result, usage = await provider.complete(job)
        job_service.complete(
            job.job_id,
            status=JobStatus.succeeded,
            result=result,
            usage=usage,
            error_code=None,
            error_message=None,
        )

    asyncio.run(_process())


def test_job_submission_and_completion(tmp_path) -> None:
    default_rate = RateLimitSettings(per_minute=60, burst=120)
    app, key_service, job_service, queue, _, webhooks, dispatcher, _, _ = _build_components(
        tmp_path, default_rate=default_rate
    )
    client = TestClient(app)

    material = key_service.issue_key(customer_id="cust-one", plan_tier="standard")
    headers = {"Authorization": f"Bearer {material.api_key}"}
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    response = client.post("/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    _process_single_job(queue, job_service)

    finished = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert finished.status_code == 200
    body = finished.json()
    assert body["status"] == "succeeded"
    assert body["result"]["messages"][0]["content"] == "stub response"
    assert body["usage"]["premium"]["rate"] == 0.10
    assert body["usage"]["premium"]["value"] == "0.001000"
    assert body["usage"]["total_billed"]["value"] == "0.011000"
    assert body["usage"]["openrouter_cost"]["value"] == "0.010000"
    assert "anomaly" not in body["usage"]

    response_cancel = client.post(f"/v1/jobs/{job_id}/cancel", headers=headers)
    assert response_cancel.status_code == 409

    second = client.post("/v1/jobs", json=payload, headers=headers)
    assert second.status_code == 202
    job_id_two = second.json()["job_id"]
    cancel_resp = client.post(f"/v1/jobs/{job_id_two}/cancel", headers=headers)
    assert cancel_resp.status_code == 202
    assert cancel_resp.json()["status"] == "cancelled"

    usage_listing = client.get("/v1/usage", headers=headers)
    assert usage_listing.status_code == 200
    usage_body = usage_listing.json()
    assert usage_body["has_more"] is False
    assert usage_body["data"], "expected usage record"
    record = usage_body["data"][0]
    assert record["job_id"] == job_id
    assert record["premium"]["rate"] == 0.10
    assert record["total_billed"]["value"] == "0.011000"
    assert "anomaly" not in record

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    metrics_text = metrics.text
    assert 'atlas_orchestrator_premium_api_jobs_completed_total{status="succeeded"} 1' in metrics_text
    assert 'atlas_orchestrator_premium_api_jobs_submitted_total{plan_tier="standard"}' in metrics_text
    assert 'atlas_orchestrator_premium_api_jobs_completed_total{status="cancelled"}' in metrics_text
    health = client.get("/healthz")
    assert health.status_code == 200
    health_body = health.json()
    assert health_body["status"] == "ok"


def test_rate_limiter_enforced(tmp_path) -> None:
    default_rate = RateLimitSettings(per_minute=1, burst=1)
    app, key_service, *_ = _build_components(tmp_path, default_rate=default_rate)
    client = TestClient(app)

    material = key_service.issue_key(
        customer_id="cust-two",
        plan_tier="standard",
        rate_limit=RateLimitSettings(per_minute=1, burst=1),
    )
    headers = {"Authorization": f"Bearer {material.api_key}"}
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    first = client.post("/v1/jobs", json=payload, headers=headers)
    assert first.status_code == 202
    second = client.post("/v1/jobs", json=payload, headers=headers)
    assert second.status_code == 429
    assert second.json()["detail"] == "rate_limited"


def test_webhook_dispatch(tmp_path) -> None:
    default_rate = RateLimitSettings(per_minute=60, burst=120)
    app, key_service, job_service, queue, _, webhooks, dispatcher, _, _ = _build_components(
        tmp_path, default_rate=default_rate
    )
    client = TestClient(app)

    material = key_service.issue_key(customer_id="cust-hooks", plan_tier="standard")
    headers = {"Authorization": f"Bearer {material.api_key}"}

    webhook_payload = {
        "webhooks": [
            {"id": "default", "url": "https://example.com/hook", "secret": "shh"}
        ]
    }
    response = client.put("/v1/webhooks", json=webhook_payload, headers=headers)
    assert response.status_code == 200
    assert webhooks.get("cust-hooks", "default") is not None

    payload = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "ping"}],
        "webhook": {"id": "default"},
    }
    job_response = client.post("/v1/jobs", json=payload, headers=headers)
    assert job_response.status_code == 202
    job_id = job_response.json()["job_id"]

    _process_single_job(queue, job_service)
    assert dispatcher.events, "expected webhook to be enqueued"
    event = dispatcher.events[-1]
    assert event["payload"]["job_id"] == job_id
    assert event["payload"]["event"] == "job.succeeded"
    assert event["secret"] == "shh"


def test_usage_anomaly_detection_and_invoice(tmp_path) -> None:
    default_rate = RateLimitSettings(per_minute=60, burst=120)
    (
        app,
        key_service,
        job_service,
        queue,
        _,
        _,
        _,
        billing_repo,
        _,
    ) = _build_components(tmp_path, default_rate=default_rate)
    client = TestClient(app)

    material = key_service.issue_key(customer_id="cust-anomaly", plan_tier="enterprise")
    headers = {"Authorization": f"Bearer {material.api_key}"}
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    response = client.post("/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    _process_single_job(queue, job_service, cost=120.0)

    job_view = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert job_view.status_code == 200
    job_usage = job_view.json()["usage"]
    assert job_usage["anomaly"]["flagged"] is True
    assert job_usage["total_billed"]["value"] == "132.000000"

    usage_listing = client.get("/v1/usage", headers=headers)
    assert usage_listing.status_code == 200
    usage_body = usage_listing.json()
    assert usage_body["has_more"] is False
    assert usage_body["data"], "expected usage data"
    record = usage_body["data"][0]
    assert record["anomaly"]["flagged"] is True
    assert record["anomaly"]["reason"] == "exceeds_threshold"
    assert record["total_billed"]["value"] == "132.000000"

    period = record["recorded_at"][:7]
    invoice = billing_repo.get_invoice(material.customer_id, period)
    assert invoice is not None
    assert invoice.total_billed_value == Decimal("132.000000")
    assert invoice.total_premium_value == Decimal("12.000000")
    assert invoice.usage_count == 1


def test_request_signature_required_for_enterprise_plan(tmp_path) -> None:
    security_settings = SecuritySettings(
        request_signing=RequestSigningSettings(
            enabled=True,
            header="X-Test-Signature",
            timestamp_header="X-Test-Timestamp",
            clock_skew_seconds=300,
            required_plan_tiers=["enterprise"],
            secret_source="env",
            secret_namespace=None,
            vault_mount="kv",
            vault_field="signing_secret",
            vault_cache_ttl_seconds=300,
        ),
        ip_filter=IpFilterSettings(allow=tuple(), deny=tuple()),
        waf=WAFSettings(mode="monitor", blocked_user_agents=tuple(), blocked_paths=tuple()),
    )
    provider = _DictSecretProvider()
    policy = SecurityPolicy(security_settings, secret_provider=provider)
    app, key_service, *_ = _build_components(
        tmp_path,
        default_rate=RateLimitSettings(per_minute=60, burst=120),
        key_security=security_settings,
        security_policy=policy,
    )
    client = TestClient(app)

    material = key_service.issue_key(customer_id="ent-cust", plan_tier="enterprise")
    provider.set_secret(material.key_id, "signing-secret")

    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = datetime.now(timezone.utc).isoformat()
    signature = _compute_signature(
        "signing-secret",
        "POST",
        "/v1/jobs",
        timestamp,
        body,
    )
    headers = {
        "Authorization": f"Bearer {material.api_key}",
        security_settings.request_signing.timestamp_header: timestamp,
        security_settings.request_signing.header: signature,
        "Content-Type": "application/json",
    }

    accepted = client.post("/v1/jobs", content=body, headers=headers)
    assert accepted.status_code == 202

    missing_signature = client.post(
        "/v1/jobs",
        content=body,
        headers={"Authorization": f"Bearer {material.api_key}", "Content-Type": "application/json"},
    )
    assert missing_signature.status_code == 401
    assert missing_signature.json()["detail"] == "signature_required"


def test_ip_allowlist_enforced(tmp_path) -> None:
    security_settings = SecuritySettings(
        request_signing=RequestSigningSettings(
            enabled=False,
            header="X-AO-Signature",
            timestamp_header="X-AO-Timestamp",
            clock_skew_seconds=300,
            required_plan_tiers=[],
            secret_source="env",
            secret_namespace=None,
            vault_mount="kv",
            vault_field="signing_secret",
            vault_cache_ttl_seconds=300,
        ),
        ip_filter=IpFilterSettings(allow=("192.0.2.0/24",), deny=tuple()),
        waf=WAFSettings(mode="monitor", blocked_user_agents=tuple(), blocked_paths=tuple()),
    )
    policy = SecurityPolicy(security_settings)
    app, key_service, *_ = _build_components(
        tmp_path,
        default_rate=RateLimitSettings(per_minute=60, burst=120),
        key_security=security_settings,
        security_policy=policy,
    )
    client = TestClient(app)
    material = key_service.issue_key(customer_id="ip-cust", plan_tier="standard")
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    allowed = client.post(
        "/v1/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {material.api_key}", "X-Forwarded-For": "192.0.2.42"},
    )
    assert allowed.status_code == 202

    blocked = client.post(
        "/v1/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {material.api_key}", "X-Forwarded-For": "198.51.100.3"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "access_restricted"


def test_waf_blocks_user_agent(tmp_path) -> None:
    security_settings = SecuritySettings(
        request_signing=RequestSigningSettings(
            enabled=False,
            header="X-AO-Signature",
            timestamp_header="X-AO-Timestamp",
            clock_skew_seconds=300,
            required_plan_tiers=[],
            secret_source="env",
            secret_namespace=None,
            vault_mount="kv",
            vault_field="signing_secret",
            vault_cache_ttl_seconds=300,
        ),
        ip_filter=IpFilterSettings(allow=tuple(), deny=tuple()),
        waf=WAFSettings(mode="block", blocked_user_agents=("badbot",), blocked_paths=tuple()),
    )
    policy = SecurityPolicy(security_settings)
    app, key_service, *_ = _build_components(
        tmp_path,
        default_rate=RateLimitSettings(per_minute=60, burst=120),
        key_security=security_settings,
        security_policy=policy,
    )
    client = TestClient(app)
    material = key_service.issue_key(customer_id="ua-cust", plan_tier="standard")
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    blocked = client.post(
        "/v1/jobs",
        json=payload,
        headers={
            "Authorization": f"Bearer {material.api_key}",
            "User-Agent": "BadBot/1.0",
        },
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "blocked"


def test_file_signing_secret_provider(tmp_path) -> None:
    secrets_file = tmp_path / "signing.json"
    secrets_file.write_text(json.dumps({"key-main": "alpha", "cust-1": "beta"}), encoding="utf-8")
    provider = FileSigningSecretProvider(secrets_file)
    context = CustomerContext(
        key_id="key-main",
        customer_id="cust-1",
        plan_tier="enterprise",
        rate_limit=RateLimitSettings(per_minute=10, burst=20),
        signing_key_id="key-main",
    )
    assert provider.get_secret(context) == "alpha"

    fallback_context = CustomerContext(
        key_id="unused",
        customer_id="cust-1",
        plan_tier="enterprise",
        rate_limit=RateLimitSettings(per_minute=10, burst=20),
        signing_key_id=None,
    )
    assert provider.get_secret(fallback_context) == "beta"


def test_tls_enforcement_requires_https(tmp_path) -> None:
    tls_settings = TLSSettings(
        mode="forwarded",
        require_https=True,
        hsts_enabled=True,
        certificate_path=None,
        private_key_path=None,
    )
    app, key_service, *_ = _build_components(
        tmp_path,
        default_rate=RateLimitSettings(per_minute=60, burst=120),
        tls_settings=tls_settings,
    )
    client = TestClient(app)
    material = key_service.issue_key(customer_id="tls-cust", plan_tier="standard")
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "ping"}]}

    blocked = client.post("/v1/jobs", json=payload, headers={"Authorization": f"Bearer {material.api_key}"})
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "https_required"

    allowed = client.post(
        "/v1/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {material.api_key}", "X-Forwarded-Proto": "https"},
    )
    assert allowed.status_code == 202
    assert allowed.headers.get("Strict-Transport-Security")


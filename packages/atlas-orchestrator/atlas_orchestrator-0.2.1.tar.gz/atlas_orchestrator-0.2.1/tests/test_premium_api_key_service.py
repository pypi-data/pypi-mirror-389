"""Tests for premium API key management service."""

from __future__ import annotations

from fastapi import HTTPException

from atlas_orchestrator.premium_api.audit import AuditLogger
from atlas_orchestrator.premium_api.hashing import Argon2KeyHasher
from atlas_orchestrator.premium_api.models import RateLimitSettings
from atlas_orchestrator.premium_api.services import KeyService
from atlas_orchestrator.premium_api.storage import SqliteApiKeyRepository


def build_service(tmp_path, *, prefix_length: int = 16) -> KeyService:
    repo = SqliteApiKeyRepository(tmp_path / "keys.db")
    audit = AuditLogger(tmp_path / "audit.log")
    return KeyService(
        repository=repo,
        hasher=Argon2KeyHasher(),
        audit=audit,
        key_prefix="ao_live_",
        prefix_length=prefix_length,
        default_rate_limit=RateLimitSettings(per_minute=60, burst=120),
    )


def test_issue_and_authenticate_key(tmp_path) -> None:
    service = build_service(tmp_path)
    material = service.issue_key(customer_id="cust_123", plan_tier="standard", metadata={"plan": "beta"})
    assert material.prefix.startswith("ao_live_")

    repo = service._repository  # type: ignore[attr-defined]
    record = repo.get_by_prefix(material.prefix)
    assert record is not None
    assert record.customer_id == "cust_123"
    assert record.hashed_key != material.api_key

    authed = service.authenticate(material.api_key)
    assert authed.key_id == record.key_id

    service.revoke(record.key_id)
    try:
        service.authenticate(material.api_key)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:  # pragma: no cover - ensure exception raised
        raise AssertionError("Authentication succeeded for revoked key")


def test_issue_with_custom_rate_limit(tmp_path) -> None:
    service = build_service(tmp_path)
    rate_limit = RateLimitSettings(per_minute=10, burst=25)
    material = service.issue_key(customer_id="cust_456", plan_tier="enterprise", rate_limit=rate_limit)

    repo = service._repository  # type: ignore[attr-defined]
    record = repo.get_by_prefix(material.prefix)
    assert record is not None
    assert record.rate_limit_per_minute == 10
    assert record.rate_limit_burst == 25

"""Tests for premium API secret providers."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from atlas_orchestrator.premium_api.models import CustomerContext, RateLimitSettings
from atlas_orchestrator.premium_api.secrets import VaultHTTPClient, VaultSigningSecretProvider


class _StubVaultClient:
    def __init__(self, mapping: dict[str, dict]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    def read(self, path: str) -> dict | None:
        self.calls.append(path)
        return self._mapping.get(path)


def _context(
    *,
    key_id: str = "key-main",
    customer_id: str = "cust-1",
    signing_key_id: str | None = "sign-123",
) -> CustomerContext:
    return CustomerContext(
        key_id=key_id,
        customer_id=customer_id,
        plan_tier="enterprise",
        rate_limit=RateLimitSettings(per_minute=60, burst=120),
        signing_key_id=signing_key_id,
    )


def test_vault_provider_returns_secret_and_caches() -> None:
    path = "kv/data/premium/signing/sign-123"
    client = _StubVaultClient({path: {"data": {"data": {"signing_secret": "alpha"}}}})
    provider = VaultSigningSecretProvider(
        client,
        mount="kv",
        base_path="premium/signing",
        field="signing_secret",
    )

    secret = provider.get_secret(_context())
    assert secret == "alpha"
    # second lookup should reuse cache and avoid extra reads
    assert provider.get_secret(_context()) == "alpha"
    assert client.calls == [path]


def test_vault_provider_falls_back_to_customer_identifier() -> None:
    path = "kv/data/premium/signing/cust-1"
    client = _StubVaultClient({path: {"data": {"data": {"signing_secret": "beta"}}}})
    provider = VaultSigningSecretProvider(
        client,
        mount="kv",
        base_path="premium/signing",
        field="signing_secret",
    )
    context = _context(signing_key_id=None)

    assert provider.get_secret(context) == "beta"
    assert client.calls[-1] == path


def test_vault_provider_handles_missing_secrets() -> None:
    client = _StubVaultClient({})
    provider = VaultSigningSecretProvider(client, mount="kv")

    assert provider.get_secret(_context()) is None


def test_vault_provider_refreshes_after_ttl_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    path = "kv/data/premium/signing/sign-123"
    mapping = {"data": {"data": {"signing_secret": "alpha"}}}
    client = _StubVaultClient({path: mapping})
    clock = {"value": 0.0}
    monkeypatch.setattr("atlas_orchestrator.premium_api.secrets.time.monotonic", lambda: clock["value"])

    provider = VaultSigningSecretProvider(
        client,
        mount="kv",
        base_path="premium/signing",
        field="signing_secret",
        cache_ttl_seconds=1,
    )

    assert provider.get_secret(_context()) == "alpha"
    assert client.calls == [path]

    mapping["data"]["data"]["signing_secret"] = "beta"
    clock["value"] = 0.5
    assert provider.get_secret(_context()) == "alpha"
    assert client.calls == [path]

    clock["value"] = 2.0
    assert provider.get_secret(_context()) == "beta"
    assert client.calls == [path, path]


def test_vault_provider_invalidate_triggers_refresh() -> None:
    path = "kv/data/premium/signing/sign-123"
    mapping = {"data": {"data": {"signing_secret": "alpha"}}}
    client = _StubVaultClient({path: mapping})
    provider = VaultSigningSecretProvider(
        client,
        mount="kv",
        base_path="premium/signing",
        field="signing_secret",
    )

    assert provider.get_secret(_context()) == "alpha"
    mapping["data"]["data"]["signing_secret"] = "beta"
    provider.invalidate("sign-123")
    assert provider.get_secret(_context()) == "beta"
    assert client.calls == [path, path]


def test_vault_provider_retries_missing_after_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    path = "kv/data/premium/signing/sign-123"
    mapping: dict[str, dict] = {}
    client = _StubVaultClient(mapping)
    clock = {"value": 0.0}
    monkeypatch.setattr("atlas_orchestrator.premium_api.secrets.time.monotonic", lambda: clock["value"])

    provider = VaultSigningSecretProvider(
        client,
        mount="kv",
        base_path="premium/signing",
        field="signing_secret",
        cache_ttl_seconds=1,
    )

    assert provider.get_secret(_context()) is None
    mapping[path] = {"data": {"data": {"signing_secret": "gamma"}}}
    clock["value"] = 2.0
    assert provider.get_secret(_context()) == "gamma"


def test_vault_http_client_reads_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": {"data": {"signing_secret": "gamma"}}}

    class _DummyResponse:
        def __init__(self, body: bytes) -> None:
            self.status = 200
            self._body = body

        def read(self) -> bytes:
            return self._body

        def __enter__(self) -> "_DummyResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    recorded = {"request": None}

    def _fake_urlopen(request, timeout: float):
        headers = {key.lower(): value for key, value in dict(request.header_items()).items()}
        recorded["request"] = SimpleNamespace(
            url=request.full_url,
            headers=headers,
        )
        return _DummyResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("atlas_orchestrator.premium_api.secrets.urllib_request.urlopen", _fake_urlopen)

    client = VaultHTTPClient(address="https://vault.example", token="tok", namespace="team")
    result = client.read("kv/data/premium/signing/sign-123")
    assert result == payload

    sent = recorded["request"]
    assert sent is not None
    assert sent.url == "https://vault.example/v1/kv/data/premium/signing/sign-123"
    assert sent.headers["x-vault-token"] == "tok"
    assert sent.headers["x-vault-namespace"] == "team"
    assert sent.headers["x-vault-request"] == "true"


def test_vault_http_client_handles_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raising_urlopen(*args, **kwargs):
        raise OSError("network failure")

    monkeypatch.setattr("atlas_orchestrator.premium_api.secrets.urllib_request.urlopen", _raising_urlopen)

    client = VaultHTTPClient(address="https://vault.example", token="tok")
    assert client.read("kv/data/foo") is None

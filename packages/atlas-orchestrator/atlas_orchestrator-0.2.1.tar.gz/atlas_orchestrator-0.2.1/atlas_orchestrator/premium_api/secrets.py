"""Secret provider abstractions for premium API signing keys."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

from .models import CustomerContext


class SigningSecretProvider(Protocol):
    """Resolve signing secrets for request validation."""

    def get_secret(self, context: CustomerContext) -> str | None:  # pragma: no cover - interface
        raise NotImplementedError


class EnvSigningSecretProvider(SigningSecretProvider):
    """Resolve signing secrets from environment variables."""

    def __init__(
        self, *, prefix: str = "ATLAS_ORCHESTRATOR_SIGNING_SECRET__"
    ) -> None:
        self._prefix = prefix

    def get_secret(self, context: CustomerContext) -> str | None:
        for identifier in self._candidate_identifiers(context):
            if not identifier:
                continue
            env_key = f"{self._prefix}{identifier.upper().replace('-', '_')}"
            value = os.getenv(env_key)
            if value:
                return value
        return None

    def _candidate_identifiers(self, context: CustomerContext) -> tuple[str | None, ...]:
        return (
            context.signing_key_id,
            context.key_id,
            context.customer_id,
        )


class FileSigningSecretProvider(SigningSecretProvider):
    """Resolve signing secrets from a JSON file mapping ids to secrets."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get_secret(self, context: CustomerContext) -> str | None:
        data = self._load()
        for identifier in (
            context.signing_key_id,
            context.key_id,
            context.customer_id,
        ):
            if identifier and identifier in data:
                return data[identifier]
        return None

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            content = self._path.read_text(encoding="utf-8")
        except OSError:
            return {}
        try:
            loaded = json.loads(content) or {}
        except json.JSONDecodeError:
            return {}
        if not isinstance(loaded, dict):
            return {}
        result: dict[str, str] = {}
        for key, value in loaded.items():
            if isinstance(key, str) and isinstance(value, str):
                result[key] = value
        return result


class VaultClient(Protocol):
    """Minimal client interface for reading secrets from a managed Vault."""

    def read(self, path: str) -> dict[str, Any] | None:  # pragma: no cover - interface
        raise NotImplementedError


class VaultSigningSecretProvider(SigningSecretProvider):
    """Resolve signing secrets via a Vault KV (v2) backend."""

    def __init__(
        self,
        client: VaultClient,
        *,
        mount: str = "kv",
        base_path: str | None = None,
        field: str = "signing_secret",
        cache_ttl_seconds: int = 300,
    ) -> None:
        self._client = client
        self._mount = mount.strip("/") or "kv"
        self._base_path = base_path.strip("/") if base_path else None
        self._field = field
        self._cache_ttl = max(0, cache_ttl_seconds)
        self._cache: dict[str, tuple[str | None, float | None]] = {}

    def get_secret(self, context: CustomerContext) -> str | None:
        for identifier in (
            context.signing_key_id,
            context.key_id,
            context.customer_id,
        ):
            secret = self._resolve(identifier)
            if secret:
                return secret
        return None

    def invalidate(self, identifier: str | None = None) -> None:
        """Invalidate cached Vault entries."""
        if self._cache_ttl == 0:
            return
        if identifier is None:
            self._cache.clear()
            return
        path = self._path_for(identifier)
        self._cache.pop(path, None)

    def _resolve(self, identifier: str | None) -> str | None:
        if not identifier:
            return None
        path = self._path_for(identifier)
        now = time.monotonic()
        if self._cache_ttl != 0:
            cached = self._cache.get(path)
            if cached:
                value, expires_at = cached
                if expires_at is None or expires_at > now:
                    return value
        payload = self._client.read(path)
        secret = self._extract(payload)
        if self._cache_ttl != 0:
            expires_at = None if self._cache_ttl < 0 else now + self._cache_ttl
            self._cache[path] = (secret, expires_at)
        return secret

    def _path_for(self, identifier: str) -> str:
        data_prefix = self._data_prefix()
        if self._base_path:
            return "/".join(
                part.strip("/")
                for part in (data_prefix, self._base_path, identifier)
                if part is not None
            )
        return "/".join((data_prefix, identifier.strip("/")))

    def _data_prefix(self) -> str:
        cleaned = self._mount.rstrip("/")
        if cleaned.endswith("/data"):
            return cleaned
        return f"{cleaned}/data"

    def _extract(self, payload: dict[str, Any] | None) -> str | None:
        if not isinstance(payload, dict):
            return None
        data = payload.get("data")
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            data = data["data"]
        if isinstance(data, dict):
            value = data.get(self._field)
            if isinstance(value, str):
                return value
        value = payload.get(self._field)
        if isinstance(value, str):
            return value
        return None


class VaultHTTPClient:
    """Lightweight HTTP client for Vault KV reads."""

    def __init__(
        self,
        *,
        address: str,
        token: str,
        namespace: str | None = None,
        timeout: float = 2.0,
    ) -> None:
        self._address = address.rstrip("/")
        self._token = token
        self._namespace = namespace
        self._timeout = timeout

    def read(self, path: str) -> dict[str, Any] | None:
        url = f"{self._address}/v1/{path.lstrip('/')}"
        request = urllib_request.Request(url)
        request.add_header("X-Vault-Token", self._token)
        request.add_header("X-Vault-Request", "true")
        if self._namespace:
            request.add_header("X-Vault-Namespace", self._namespace)
        try:
            with urllib_request.urlopen(request, timeout=self._timeout) as response:
                if getattr(response, "status", 200) >= 400:
                    return None
                raw = response.read()
        except (urllib_error.URLError, OSError):
            return None
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None
        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

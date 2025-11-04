"""Security enforcement utilities for the premium API."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import ip_address, ip_network
from typing import Sequence

from fastapi import HTTPException, Request, status

from .audit import AuditLogger
from .config import IpFilterSettings, RequestSigningSettings, SecuritySettings, WAFSettings
from .models import CustomerContext
from .secrets import EnvSigningSecretProvider, SigningSecretProvider


@dataclass
class _IPAddressFilter:
    settings: IpFilterSettings
    audit: AuditLogger | None = None

    def enforce(self, request: Request, context: CustomerContext) -> None:
        remote_ip = self._extract_client_ip(request)
        if not remote_ip:
            return

        deny_networks = list(self._networks(self.settings.deny))
        if context.ip_denylist:
            deny_networks.extend(self._networks(context.ip_denylist))
        if any(remote_ip in network for network in deny_networks):
            self._record("security.ip.deny", remote_ip, context)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="access_denied")

        allow_networks = list(self._networks(self.settings.allow))
        if context.ip_allowlist:
            allow_networks.extend(self._networks(context.ip_allowlist))
        if allow_networks and not any(remote_ip in network for network in allow_networks):
            self._record("security.ip.restricted", remote_ip, context)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="access_restricted")

    def _extract_client_ip(self, request: Request):
        header = request.headers.get("x-forwarded-for")
        if header:
            candidate = header.split(",")[0].strip()
        elif request.client is not None:
            candidate = request.client.host
        else:
            candidate = ""
        if not candidate:
            return None
        try:
            return ip_address(candidate)
        except ValueError:
            return None

    def _networks(self, values: Sequence[str]):
        for value in values:
            try:
                yield ip_network(value, strict=False)
            except ValueError:
                self._record("security.ip.invalid", value, None)

    def _record(self, event: str, subject: str, context: CustomerContext | None) -> None:
        if not self.audit:
            return
        payload = {"subject": subject}
        if context:
            payload.update({"customer_id": context.customer_id, "key_id": context.key_id})
        self.audit.record(event, payload)


@dataclass
class _WAFGuard:
    settings: WAFSettings
    audit: AuditLogger | None = None

    def enforce(self, request: Request, context: CustomerContext) -> None:
        user_agent = request.headers.get("user-agent", "")
        path = request.url.path
        if self._is_blocked_user_agent(user_agent) or self._is_blocked_path(path):
            self._record("security.waf.match", user_agent, path, context)
            if self.settings.mode == "block":
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="blocked")

    def _is_blocked_user_agent(self, user_agent: str) -> bool:
        lowered = user_agent.lower()
        return any(token.lower() in lowered for token in self.settings.blocked_user_agents)

    def _is_blocked_path(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.settings.blocked_paths)

    def _record(self, event: str, user_agent: str, path: str, context: CustomerContext) -> None:
        if not self.audit:
            return
        self.audit.record(
            event,
            {
                "customer_id": context.customer_id,
                "key_id": context.key_id,
                "user_agent": user_agent,
                "path": path,
                "mode": self.settings.mode,
            },
        )


@dataclass
class _RequestSigningEnforcer:
    settings: RequestSigningSettings
    secret_provider: SigningSecretProvider | None
    audit: AuditLogger | None

    async def enforce(self, request: Request, context: CustomerContext) -> None:
        if not self._should_enforce(context):
            return
        secret = context.signing_secret
        if not secret and self.secret_provider:
            secret = self.secret_provider.get_secret(context)
        if not secret:
            self._log_failure("missing_secret", context)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="signature_required")
        signature = request.headers.get(self.settings.header)
        timestamp = request.headers.get(self.settings.timestamp_header)
        if not signature or not timestamp:
            self._log_failure("missing_headers", context)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="signature_required")
        try:
            timestamp_seconds = self._parse_timestamp(timestamp)
        except ValueError:
            self._log_failure("invalid_timestamp", context)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="signature_invalid")
        if abs(time.time() - timestamp_seconds) > self.settings.clock_skew_seconds:
            self._log_failure("expired_timestamp", context)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="signature_expired")

        body = await request.body()
        payload = b"|".join(
            [
                timestamp.encode("utf-8"),
                request.method.upper().encode("utf-8"),
                request.url.path.encode("utf-8"),
                body,
            ]
        )
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            self._log_failure("mismatch", context)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="signature_invalid")

    def _should_enforce(self, context: CustomerContext) -> bool:
        if context.requires_signature:
            return True
        if not self.settings.enabled:
            return False
        tiers = self.settings.required_plan_tiers
        if not tiers:
            return True
        return context.plan_tier in tiers

    def _parse_timestamp(self, value: str) -> float:
        try:
            return float(value)
        except ValueError:
            cleaned = value.strip()
            if cleaned.endswith("Z"):
                cleaned = f"{cleaned[:-1]}+00:00"
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.timestamp()

    def _log_failure(self, reason: str, context: CustomerContext) -> None:
        if not self.audit:
            return
        self.audit.record(
            "security.signature.failed",
            {
                "reason": reason,
                "customer_id": context.customer_id,
                "key_id": context.key_id,
            },
        )


class SecurityPolicy:
    """Aggregate security enforcement applied to each premium API request."""

    def __init__(
        self,
        settings: SecuritySettings,
        *,
        audit: AuditLogger | None = None,
        secret_provider: SigningSecretProvider | None = None,
    ) -> None:
        self._audit = audit
        self._signing = _RequestSigningEnforcer(settings.request_signing, secret_provider, audit)
        self._ip_filter = _IPAddressFilter(settings.ip_filter, audit)
        self._waf = _WAFGuard(settings.waf, audit)

    async def enforce(self, request: Request, context: CustomerContext) -> None:
        self._ip_filter.enforce(request, context)
        self._waf.enforce(request, context)
        await self._signing.enforce(request, context)


DEFAULT_SECURITY = SecurityPolicy(
    SecuritySettings(
        request_signing=RequestSigningSettings(
            enabled=False,
            header="X-AO-Signature",
            timestamp_header="X-AO-Timestamp",
            clock_skew_seconds=300,
            required_plan_tiers=tuple(),
            secret_source="env",
            secret_namespace=None,
            vault_mount="kv",
            vault_field="signing_secret",
            vault_cache_ttl_seconds=300,
        ),
        ip_filter=IpFilterSettings(allow=tuple(), deny=tuple()),
        waf=WAFSettings(mode="monitor", blocked_user_agents=tuple(), blocked_paths=tuple()),
    ),
    secret_provider=EnvSigningSecretProvider(),
)

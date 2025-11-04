"""Authentication dependencies for FastAPI."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from .audit import AuditLogger
from .models import CustomerContext
from .rate_limiter import RateLimiter
from .security import DEFAULT_SECURITY, SecurityPolicy
from .services import KeyService


class APIKeyAuth:
    """FastAPI dependency enforcing bearer authentication and rate limits."""

    def __init__(
        self,
        key_service: KeyService,
        rate_limiter: RateLimiter,
        audit: AuditLogger,
        *,
        security: SecurityPolicy | None = None,
    ) -> None:
        self._key_service = key_service
        self._rate_limiter = rate_limiter
        self._audit = audit
        self._security = security or DEFAULT_SECURITY

    async def __call__(self, request: Request) -> CustomerContext:
        token = self._extract_bearer_token(request)
        record = self._key_service.authenticate(token)
        context = self._key_service.customer_context(record)
        allowed = await self._rate_limiter.allow(
            context.customer_id,
            per_minute=context.rate_limit.per_minute,
            burst=context.rate_limit.burst,
        )
        if not allowed:
            self._audit.record(
                "api_key.rate_limited",
                {
                    "customer_id": context.customer_id,
                    "key_id": context.key_id,
                    "source_ip": request.client.host if request.client else None,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limited",
                headers={"Retry-After": "60"},
            )
        self._audit.record(
            "api_key.authenticated",
            {
                "customer_id": context.customer_id,
                "key_id": context.key_id,
                "source_ip": request.client.host if request.client else None,
            },
        )
        await self._security.enforce(request, context)
        return context

    def _extract_bearer_token(self, request: Request) -> str:
        header = request.headers.get("authorization")
        if not header:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
        return token.strip()

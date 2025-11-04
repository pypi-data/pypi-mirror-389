"""Bootstrap utilities for wiring premium API services."""

from __future__ import annotations

import os
from pathlib import Path

from redis.asyncio import Redis

from atlas_orchestrator.config import AppConfig
from atlas_orchestrator.container import DependencyContainer
from atlas_orchestrator.premium_api import observability
from atlas_orchestrator.premium_api.audit import AuditLogger
from atlas_orchestrator.premium_api.billing import BillingEngine, SqliteBillingRepository
from atlas_orchestrator.premium_api.config import PremiumAPISettings
from atlas_orchestrator.premium_api.hashing import Argon2KeyHasher
from atlas_orchestrator.premium_api.jobs import SqliteJobRepository
from atlas_orchestrator.premium_api.providers import OpenRouterCompletionProvider
from atlas_orchestrator.premium_api.queue import InMemoryJobQueue
from atlas_orchestrator.premium_api.rate_limiter import InMemoryRateLimiter, RedisRateLimiter
from atlas_orchestrator.premium_api.security import SecurityPolicy
from atlas_orchestrator.premium_api.services import JobService, KeyService
from atlas_orchestrator.premium_api.secrets import (
    EnvSigningSecretProvider,
    FileSigningSecretProvider,
    VaultHTTPClient,
    VaultSigningSecretProvider,
)
from atlas_orchestrator.premium_api.storage import SqliteApiKeyRepository
from atlas_orchestrator.premium_api.webhooks import WebhookDispatcher, WebhookRepository
from atlas_orchestrator.premium_api.worker import JobWorker


def register_premium_api_services(
    container: DependencyContainer,
    config: AppConfig,
    workspace_root: Path,
) -> None:
    settings = PremiumAPISettings.from_config(config.premium_api, workspace_root)
    settings.ensure_directories()
    container.register_instance("premium_api.settings", settings)
    observability.configure(settings.observability)
    container.register_instance("premium_api.observability", settings.observability)

    audit_logger = AuditLogger(settings.audit_log_path)
    key_repository = SqliteApiKeyRepository(settings.database_path)
    job_repository = SqliteJobRepository(settings.database_path)
    billing_repository = SqliteBillingRepository(settings.database_path)
    job_queue = InMemoryJobQueue()
    webhook_repository = WebhookRepository(settings.database_path)
    dispatcher = WebhookDispatcher(audit=audit_logger)

    billing_engine = BillingEngine(repository=billing_repository, audit=audit_logger)

    default_rate_limit = _build_rate_limit(settings.rate_limit_per_minute, settings.rate_limit_burst)
    signing_secret_provider = None
    signing_config = settings.security.request_signing
    if signing_config.secret_source == "env":
        prefix = signing_config.secret_namespace or "ATLAS_ORCHESTRATOR_SIGNING_SECRET__"
        signing_secret_provider = EnvSigningSecretProvider(prefix=prefix)
    elif signing_config.secret_source == "file":
        namespace = signing_config.secret_namespace
        if namespace:
            path = Path(namespace)
            if not path.is_absolute():
                path = settings.base_dir / path
        else:
            path = settings.base_dir / "signing_secrets.json"
        signing_secret_provider = FileSigningSecretProvider(path)
    elif signing_config.secret_source == "vault":
        vault_client = None
        if "premium_api.vault_client" in container:
            try:
                vault_client = container.resolve("premium_api.vault_client")
            except KeyError:
                vault_client = None
        if vault_client is None:
            vault_addr = os.getenv("ATLAS_ORCHESTRATOR_VAULT_ADDR")
            vault_token = os.getenv("ATLAS_ORCHESTRATOR_VAULT_TOKEN")
            if vault_addr and vault_token:
                namespace = os.getenv("ATLAS_ORCHESTRATOR_VAULT_NAMESPACE")
                timeout_value = os.getenv("ATLAS_ORCHESTRATOR_VAULT_TIMEOUT")
                timeout = None
                if timeout_value:
                    try:
                        timeout = float(timeout_value)
                    except ValueError:
                        timeout = None
                vault_client = VaultHTTPClient(
                    address=vault_addr,
                    token=vault_token,
                    namespace=namespace,
                    timeout=timeout or 2.0,
                )
                container.register_instance("premium_api.vault_client", vault_client)
        if vault_client is not None:
            signing_secret_provider = VaultSigningSecretProvider(
                vault_client,
                mount=signing_config.vault_mount,
                base_path=signing_config.secret_namespace,
                field=signing_config.vault_field,
                cache_ttl_seconds=signing_config.vault_cache_ttl_seconds,
            )
    security_policy = SecurityPolicy(
        settings.security,
        audit=audit_logger,
        secret_provider=signing_secret_provider,
    )
    key_service = KeyService(
        repository=key_repository,
        hasher=Argon2KeyHasher(),
        audit=audit_logger,
        key_prefix=settings.key_prefix,
        prefix_length=settings.prefix_length,
        default_rate_limit=default_rate_limit,
        default_premium_rate=config.premium_api.premium_rate_default,
        security=settings.security,
    )
    job_service = JobService(
        repository=job_repository,
        queue=job_queue,
        audit=audit_logger,
        dispatcher=dispatcher,
        billing=billing_engine,
    )

    container.register_instance("premium_api.audit", audit_logger)
    container.register_instance("premium_api.key_service", key_service)
    container.register_instance("premium_api.job_service", job_service)
    container.register_instance("premium_api.queue", job_queue)
    container.register_instance("premium_api.webhooks", webhook_repository)
    container.register_instance("premium_api.dispatcher", dispatcher)
    container.register_instance("premium_api.billing_repository", billing_repository)
    container.register_instance("premium_api.billing", billing_engine)
    container.register_instance("premium_api.security_policy", security_policy)
    container.register_instance("premium_api.tls_settings", settings.tls)
    if signing_secret_provider is not None:
        container.register_instance("premium_api.signing_secret_provider", signing_secret_provider)

    rate_limiter = _build_rate_limiter(settings)
    container.register_instance("premium_api.rate_limiter", rate_limiter)

    openrouter_key = os.getenv("PREMIUM_API_OPENROUTER_KEY") or os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        provider = OpenRouterCompletionProvider(api_key=openrouter_key)
    else:
        provider = _NullProvider()
    worker = JobWorker(queue=job_queue, job_service=job_service, provider=provider)
    container.register_instance("premium_api.provider", provider)
    container.register_instance("premium_api.worker", worker)


def _build_rate_limit(per_minute: int, burst: int):
    from atlas_orchestrator.premium_api.models import RateLimitSettings

    return RateLimitSettings(per_minute=per_minute, burst=burst)


def _build_rate_limiter(settings: PremiumAPISettings):
    redis_url = os.getenv("PREMIUM_API_REDIS_URL")
    if redis_url:
        client = Redis.from_url(redis_url)
        return RedisRateLimiter(client)
    return InMemoryRateLimiter()


class _NullProvider:
    async def complete(self, job):  # pragma: no cover - placeholder
        raise RuntimeError("No completion provider configured")


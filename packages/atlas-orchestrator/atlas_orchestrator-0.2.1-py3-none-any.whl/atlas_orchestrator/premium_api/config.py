"""Runtime configuration helpers for premium API services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from atlas_orchestrator.config import PremiumAPIConfig


@dataclass(frozen=True)
class RequestSigningSettings:
    enabled: bool
    header: str
    timestamp_header: str
    clock_skew_seconds: int
    required_plan_tiers: tuple[str, ...]
    secret_source: str
    secret_namespace: str | None
    vault_mount: str
    vault_field: str
    vault_cache_ttl_seconds: int


@dataclass(frozen=True)
class IpFilterSettings:
    allow: tuple[str, ...]
    deny: tuple[str, ...]


@dataclass(frozen=True)
class WAFSettings:
    mode: str
    blocked_user_agents: tuple[str, ...]
    blocked_paths: tuple[str, ...]


@dataclass(frozen=True)
class SecuritySettings:
    request_signing: RequestSigningSettings
    ip_filter: IpFilterSettings
    waf: WAFSettings


@dataclass(frozen=True)
class TLSSettings:
    mode: str
    require_https: bool
    hsts_enabled: bool
    certificate_path: Path | None
    private_key_path: Path | None


@dataclass(frozen=True)
class ObservabilitySettings:
    prometheus_push_url: str | None
    prometheus_job: str
    prometheus_instance: str | None
    prometheus_push_interval_seconds: float
    otel_endpoint: str | None
    otel_headers: dict[str, str]
    log_endpoint: str | None
    log_api_key_env: str | None
    latency_threshold_ms: int
    error_rate_threshold: float
    queue_depth_threshold: int


@dataclass(frozen=True)
class PremiumAPISettings:
    """Resolved settings used by premium API components."""

    enabled: bool
    key_prefix: str
    prefix_length: int
    base_dir: Path
    database_path: Path
    audit_log_path: Path
    rate_limit_per_minute: int
    rate_limit_burst: int
    security: SecuritySettings
    tls: TLSSettings
    observability: ObservabilitySettings

    @classmethod
    def from_config(cls, config: PremiumAPIConfig, workspace_root: Path) -> "PremiumAPISettings":
        base_dir = workspace_root / "premium_api"
        db_path = base_dir / config.storage.path
        audit_path = base_dir / config.audit.destination
        security = config.security
        tls = config.tls
        return cls(
            enabled=config.enabled,
            key_prefix=config.key_prefix,
            prefix_length=config.prefix_length,
            base_dir=base_dir,
            database_path=db_path,
            audit_log_path=audit_path,
            rate_limit_per_minute=config.rate_limit.per_minute,
            rate_limit_burst=config.rate_limit.burst,
            security=SecuritySettings(
                request_signing=RequestSigningSettings(
                    enabled=security.request_signing.enabled,
                    header=security.request_signing.header,
                    timestamp_header=security.request_signing.timestamp_header,
                    clock_skew_seconds=security.request_signing.clock_skew_seconds,
                    required_plan_tiers=tuple(security.request_signing.required_plan_tiers),
                    secret_source=security.request_signing.secret_source,
                    secret_namespace=security.request_signing.secret_namespace,
                    vault_mount=security.request_signing.vault_mount,
                    vault_field=security.request_signing.vault_field,
                    vault_cache_ttl_seconds=security.request_signing.vault_cache_ttl_seconds,
                ),
                ip_filter=IpFilterSettings(
                    allow=tuple(security.ip_filter.allow),
                    deny=tuple(security.ip_filter.deny),
                ),
                waf=WAFSettings(
                    mode=security.waf.mode,
                    blocked_user_agents=tuple(security.waf.blocked_user_agents),
                    blocked_paths=tuple(security.waf.blocked_paths),
                ),
            ),
            tls=TLSSettings(
                mode=tls.mode,
                require_https=tls.require_https,
                hsts_enabled=tls.hsts_enabled,
                certificate_path=base_dir / tls.certificate_path if tls.certificate_path else None,
                private_key_path=base_dir / tls.private_key_path if tls.private_key_path else None,
            ),
            observability=ObservabilitySettings(
                prometheus_push_url=config.observability.prometheus_push_url,
                prometheus_job=config.observability.prometheus_job,
                prometheus_instance=config.observability.prometheus_instance,
                prometheus_push_interval_seconds=config.observability.prometheus_push_interval_seconds,
                otel_endpoint=config.observability.otel_endpoint,
                otel_headers=dict(config.observability.otel_headers),
                log_endpoint=config.observability.log_endpoint,
                log_api_key_env=config.observability.log_api_key_env,
                latency_threshold_ms=config.observability.latency_threshold_ms,
                error_rate_threshold=config.observability.error_rate_threshold,
                queue_depth_threshold=config.observability.queue_depth_threshold,
            ),
        )

    def ensure_directories(self) -> None:
        """Create parent directories where necessary."""

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.tls.certificate_path:
            self.tls.certificate_path.parent.mkdir(parents=True, exist_ok=True)
        if self.tls.private_key_path:
            self.tls.private_key_path.parent.mkdir(parents=True, exist_ok=True)

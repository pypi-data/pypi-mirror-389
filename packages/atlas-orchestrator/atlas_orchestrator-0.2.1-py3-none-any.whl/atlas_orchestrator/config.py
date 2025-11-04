"""Configuration loading and validation for the Atlas Orchestrator application."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, Literal, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigError(RuntimeError):
    """Raised when configuration files cannot be parsed or validated."""


class ProjectConfig(BaseModel):
    """Project-level metadata and workspace settings."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        default="atlas-orchestrator-project", description="Human readable project name"
    )
    workspace: str = Field(
        default=".atlas_orchestrator", description="Relative path to workspace artifacts"
    )
    environment: str = Field(
        default="development",
        description="Named environment for feature flags",
    )


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    model_config = ConfigDict(extra="forbid")

    level: str = Field(default="INFO", description="Python logging level")
    format: str = Field(default="structured", description="Logging formatter identifier")
    destination: str = Field(
        default="stderr",
        description="Where logs are emitted (stdout/stderr/file path)",
    )


class ProviderSettings(BaseModel):
    """Configuration for an individual AI provider."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(description="Adapter identifier used to instantiate the provider")
    model: str = Field(description="Default model to use for requests")
    api_key: str | None = Field(
        default=None,
        description="Direct API key value supplied programmatically",
    )
    api_key_env: str | None = Field(
        default=None,
        description="Environment variable containing credentials",
    )
    endpoint: str | None = Field(default=None, description="Explicit base URL when required")
    pricing: dict[str, float] | None = Field(
        default=None,
        description='Per-1K token pricing with optional "prompt" and "completion" keys',
    )


class AIConfig(BaseModel):
    """AI provider registry with default selection."""

    model_config = ConfigDict(extra="forbid")

    default_provider: str = Field(description="Name of the provider used unless overridden")
    fallback_providers: list[str] = Field(
        default_factory=list,
        description="Provider names attempted if the default fails",
    )
    providers: dict[str, ProviderSettings] = Field(default_factory=dict)

    def default(self) -> ProviderSettings:
        return self.get(self.default_provider)

    def get(self, name: str) -> ProviderSettings:
        try:
            return self.providers[name]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ConfigError(f"Unknown AI provider '{name}'") from exc

    def provider_chain(self) -> list[ProviderSettings]:
        names = [self.default_provider, *self.fallback_providers]
        chain: list[ProviderSettings] = []
        seen: set[str] = set()
        for name in names:
            if name in seen:
                continue
            chain.append(self.get(name))
            seen.add(name)
        return chain


class FeatureFlags(BaseModel):
    """Feature toggle configuration."""

    model_config = ConfigDict(extra="allow")

    experimental: bool = Field(default=False)
    telemetry: bool = Field(default=True)


class PremiumAPIRateLimitConfig(BaseModel):
    """Rate limiting defaults for premium API keys."""

    model_config = ConfigDict(extra="forbid")

    per_minute: int = Field(default=60, ge=1, description="Sustained requests allowed per minute")
    burst: int = Field(default=120, ge=1, description="Maximum burst capacity")


class PremiumAPIStorageConfig(BaseModel):
    """Storage options for premium API metadata."""

    model_config = ConfigDict(extra="forbid")

    backend: Literal["sqlite"] = Field(default="sqlite", description="Storage backend identifier")
    path: str = Field(default="premium_api.db", description="Relative path to database file")


class PremiumAPIAuditConfig(BaseModel):
    """Audit logging options for premium API operations."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True, description="Whether audit logging is enabled")
    destination: str = Field(
        default="premium_api_audit.log",
        description="Relative path for JSONL audit log output",
    )


class PremiumAPIObservabilityConfig(BaseModel):
    """Observability exporters and alert thresholds for the premium API."""

    model_config = ConfigDict(extra="forbid")

    prometheus_push_url: str | None = Field(
        default=None,
        description="Optional Prometheus Pushgateway base URL (e.g. https://push.example.com).",
    )
    prometheus_job: str = Field(
        default="atlas_orchestrator_premium_api",
        description="Job label used when pushing metrics to the gateway.",
    )
    prometheus_instance: str | None = Field(
        default=None,
        description="Optional instance label appended to pushgateway requests.",
    )
    prometheus_push_interval_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Interval between Prometheus Pushgateway uploads.",
    )
    otel_endpoint: str | None = Field(
        default=None,
        description="OTLP HTTP endpoint for exporting traces (if opentelemetry runtime is present).",
    )
    otel_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers (key/value) supplied to the OTLP exporter.",
    )
    log_endpoint: str | None = Field(
        default=None,
        description="HTTP endpoint for shipping structured request logs.",
    )
    log_api_key_env: str | None = Field(
        default=None,
        description="Environment variable containing the bearer token for log shipping.",
    )
    latency_threshold_ms: int = Field(
        default=2000,
        ge=0,
        description="Alert threshold for p95 latency, expressed in milliseconds.",
    )
    error_rate_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Alert threshold for error rate (fraction between 0 and 1).",
    )
    queue_depth_threshold: int = Field(
        default=50,
        ge=0,
        description="Alert threshold for worker queue depth before paging.",
    )


class PremiumAPIRequestSigningConfig(BaseModel):
    """Request signing enforcement for premium API clients."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=False,
        description="Enable HMAC request signing validation for incoming requests",
    )
    header: str = Field(
        default="X-AO-Signature",
        description="Header containing the request signature digest",
    )
    timestamp_header: str = Field(
        default="X-AO-Timestamp",
        description="Header providing an ISO8601 timestamp for freshness validation",
    )
    clock_skew_seconds: int = Field(
        default=300,
        ge=0,
        description="Allowed timestamp drift in seconds when validating signatures",
    )
    required_plan_tiers: list[str] = Field(
        default_factory=list,
        description="Plan tiers that must present a valid signature on every request",
    )
    secret_source: Literal["env", "file", "vault"] = Field(
        default="env",
        description="Secret backend identifier used to resolve signing secrets",
    )
    secret_namespace: str | None = Field(
        default=None,
        description=(
            "Namespace identifier used by the configured secret backend "
            "(e.g. environment variable prefix or path to secrets file)."
        ),
    )
    vault_mount: str = Field(
        default="kv",
        description="Name of the Vault mount handling secrets (KV v2 expected).",
    )
    vault_field: str = Field(
        default="signing_secret",
        description="Field in the Vault secret payload that stores the signing key material.",
    )
    vault_cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        description="Seconds to cache Vault signing secrets before re-fetching (0 disables caching).",
    )


class PremiumAPIIpFilterConfig(BaseModel):
    """IP allow/deny configuration for premium API enforcement."""

    model_config = ConfigDict(extra="forbid")

    allow: list[str] = Field(
        default_factory=list,
        description="CIDR blocks or IP addresses explicitly allowed",
    )
    deny: list[str] = Field(
        default_factory=list,
        description="CIDR blocks or IP addresses explicitly denied",
    )


class PremiumAPIWAFConfig(BaseModel):
    """Lightweight request inspection and blocking rules."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["monitor", "block"] = Field(
        default="monitor",
        description="When set to 'block', requests matching WAF rules are rejected",
    )
    blocked_user_agents: list[str] = Field(
        default_factory=list,
        description="Case-insensitive substrings of User-Agent headers to reject",
    )
    blocked_paths: list[str] = Field(
        default_factory=list,
        description="Path prefixes that should be rejected early",
    )


class PremiumAPISecurityConfig(BaseModel):
    """Aggregate security controls for the premium API."""

    model_config = ConfigDict(extra="forbid")

    request_signing: PremiumAPIRequestSigningConfig = Field(
        default_factory=PremiumAPIRequestSigningConfig
    )
    ip_filter: PremiumAPIIpFilterConfig = Field(default_factory=PremiumAPIIpFilterConfig)
    waf: PremiumAPIWAFConfig = Field(default_factory=PremiumAPIWAFConfig)


class PremiumAPITLSConfig(BaseModel):
    """TLS termination preferences for the premium API."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["off", "terminate", "forwarded"] = Field(
        default="forwarded",
        description=(
            "TLS handling strategy: 'off' disables enforcement, 'terminate' expects direct TLS "
            "termination within the service, 'forwarded' trusts X-Forwarded-Proto headers."
        ),
    )
    require_https: bool = Field(
        default=True,
        description="When true, reject non-HTTPS requests (or non-forwarded HTTPS headers).",
    )
    hsts_enabled: bool = Field(
        default=True,
        description="Emit HSTS headers on responses when TLS enforcement is enabled.",
    )
    certificate_path: str | None = Field(
        default=None,
        description="Path to TLS certificate (PEM) when running in terminate mode.",
    )
    private_key_path: str | None = Field(
        default=None,
        description="Path to private key (PEM) when running in terminate mode.",
    )


class PremiumAPIConfig(BaseModel):
    """Top-level configuration for the premium API service."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=False, description="Enable premium API services")
    key_prefix: str = Field(default="ao_live_", description="API key prefix presented to customers")
    prefix_length: int = Field(default=16, ge=8, description="Number of characters used for lookup prefix")
    storage: PremiumAPIStorageConfig = Field(default_factory=PremiumAPIStorageConfig)
    rate_limit: PremiumAPIRateLimitConfig = Field(default_factory=PremiumAPIRateLimitConfig)
    audit: PremiumAPIAuditConfig = Field(default_factory=PremiumAPIAuditConfig)
    premium_rate_default: float = Field(
        default=0.10,
        ge=0.0,
        description="Default premium markup rate applied to usage totals",
    )
    security: PremiumAPISecurityConfig = Field(default_factory=PremiumAPISecurityConfig)
    tls: PremiumAPITLSConfig = Field(default_factory=PremiumAPITLSConfig)
    observability: PremiumAPIObservabilityConfig = Field(
        default_factory=PremiumAPIObservabilityConfig
    )


class AppConfig(BaseModel):
    """Top-level application configuration model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ai: AIConfig
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    premium_api: PremiumAPIConfig = Field(default_factory=PremiumAPIConfig)


class ConfigLoader:
    """Loads and validates configuration data from multiple sources."""

    ENV_PREFIX = "ATLAS_ORCHESTRATOR__"

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd())
        self._default_path = Path(__file__).with_name("data").joinpath("default_config.yaml")

    def load(
        self,
        config_file: Path | None = None,
        *,
        env: Mapping[str, str] | None = None,
        overrides: Mapping[str, Any] | None = None,
    ) -> AppConfig:
        """Load configuration by merging defaults, files, env vars, and overrides."""

        raw_config: MutableMapping[str, Any] = self._load_defaults()

        file_path = config_file or self._discover_config_path(env)
        if file_path is not None:
            file_data = self._load_file(file_path)
            _deep_merge(raw_config, file_data)

        env_overrides = self._extract_env_overrides(env)
        if env_overrides:
            _deep_merge(raw_config, env_overrides)

        if overrides:
            _deep_merge(raw_config, dict(overrides))

        try:
            return AppConfig.model_validate(raw_config)
        except ValidationError as exc:
            raise ConfigError("Configuration failed validation") from exc

    def _load_defaults(self) -> MutableMapping[str, Any]:
        if not self._default_path.exists():  # pragma: no cover - defensive check
            raise ConfigError(f"Default configuration not found at {self._default_path}")
        return self._load_file(self._default_path)

    def _discover_config_path(self, env: Mapping[str, str] | None) -> Path | None:
        env = env or os.environ
        env_path = env.get("ATLAS_ORCHESTRATOR_CONFIG_FILE")
        if env_path:
            return Path(env_path).expanduser()

        candidates = [
            self.project_root / "atlas_orchestrator.yaml",
            self.project_root / "atlas_orchestrator.yml",
            self.project_root / ".atlas_orchestrator" / "config.yaml",
            self.project_root / "a4.yaml",  # legacy fallback
            self.project_root / ".a4" / "config.yaml",  # legacy fallback
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _load_file(self, path: Path) -> MutableMapping[str, Any]:
        resolved = path.expanduser()
        if not resolved.exists():
            raise ConfigError(f"Configuration file not found: {resolved}")
        try:
            with resolved.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:  # pragma: no cover - forwarded error path
            raise ConfigError(f"Failed to parse YAML configuration: {resolved}") from exc
        if not isinstance(data, MutableMapping):
            raise ConfigError(f"Configuration file must contain a mapping: {resolved}")
        return dict(data)

    def _extract_env_overrides(self, env: Mapping[str, str] | None) -> MutableMapping[str, Any]:
        env = env or os.environ
        overrides: MutableMapping[str, Any] = {}
        for key, value in env.items():
            if not key.startswith(self.ENV_PREFIX):
                continue
            path_parts = key[len(self.ENV_PREFIX) :].lower().split("__")
            if not all(part for part in path_parts):
                continue
            coerced = _coerce_value(value)
            _assign_nested(overrides, path_parts, coerced)
        return overrides


def _deep_merge(base: MutableMapping[str, Any], other: Mapping[str, Any]) -> None:
    for key, value in other.items():
        existing = base.get(key)
        if isinstance(existing, MutableMapping) and isinstance(value, Mapping):
            _deep_merge(existing, value)
        elif isinstance(value, Mapping):
            base[key] = dict(value)
        else:
            base[key] = value


def _assign_nested(target: MutableMapping[str, Any], path: list[str], value: Any) -> None:
    cursor = target
    for part in path[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, MutableMapping):
            next_value = {}
            cursor[part] = next_value
        cursor = next_value
    cursor[path[-1]] = value


def _coerce_value(raw: str) -> Any:
    trimmed = raw.strip()
    lowered = trimmed.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        return int(trimmed)
    except ValueError:
        pass
    try:
        return float(trimmed)
    except ValueError:
        pass
    try:
        return json.loads(trimmed)
    except (json.JSONDecodeError, TypeError, ValueError):
        return trimmed


__all__ = [
    "AIConfig",
    "AppConfig",
    "ConfigError",
    "ConfigLoader",
    "FeatureFlags",
    "LoggingConfig",
    "PremiumAPIIpFilterConfig",
    "PremiumAPIAuditConfig",
    "PremiumAPIObservabilityConfig",
    "PremiumAPIConfig",
    "PremiumAPIRateLimitConfig",
    "PremiumAPIRequestSigningConfig",
    "PremiumAPISecurityConfig",
    "PremiumAPITLSConfig",
    "PremiumAPIWAFConfig",
    "PremiumAPIStorageConfig",
    "ProjectConfig",
    "ProviderSettings",
]


"""Runtime entrypoint for the premium API service.

This module wires configuration, dependency container, and FastAPI application objects so
the premium API can be hosted via Uvicorn (or any ASGI-compliant server). It is intended
to be used both by the container image and local operators who need a simple CLI entry
point (`python -m atlas_orchestrator.premium_api.server`).
"""

from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI

from atlas_orchestrator.config import AppConfig, ConfigLoader
from atlas_orchestrator.container import DependencyContainer
from atlas_orchestrator.logging import configure_logging

from .api import create_app
from .bootstrap import register_premium_api_services


def _resolve_project_root(project_root: Path | None) -> Path:
    """Resolve the project root used for configuration discovery."""
    env_root = os.getenv("ATLAS_ORCHESTRATOR_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    if project_root is not None:
        return Path(project_root).expanduser().resolve()
    return Path.cwd().resolve()


def _resolve_workspace_root(config: AppConfig, project_root: Path) -> Path:
    """Compute the workspace root for premium API artifacts."""
    override = os.getenv("ATLAS_ORCHESTRATOR_PREMIUM_API_WORKSPACE")
    if override:
        workspace = Path(override).expanduser()
    else:
        workspace = project_root / config.project.workspace
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def build_application(
    *,
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> FastAPI:
    """Construct the FastAPI application with wired dependencies."""

    resolved_root = _resolve_project_root(project_root)
    loader = ConfigLoader(project_root=resolved_root)
    config = loader.load(config_file=config_path)
    configure_logging(config.logging)

    if not config.premium_api.enabled:
        raise RuntimeError(
            "Premium API is disabled in configuration. Enable `premium_api.enabled` to start the service."
        )

    workspace_root = _resolve_workspace_root(config, resolved_root)

    container = DependencyContainer()
    container.register_instance("config", config)

    register_premium_api_services(container, config, workspace_root)

    key_service = container.resolve("premium_api.key_service")
    job_service = container.resolve("premium_api.job_service")
    rate_limiter = container.resolve("premium_api.rate_limiter")
    audit_logger = container.resolve("premium_api.audit")
    webhook_repository = container.resolve("premium_api.webhooks")
    dispatcher = container.resolve("premium_api.dispatcher")
    billing = container.resolve("premium_api.billing")
    security_policy = container.resolve("premium_api.security_policy")
    tls_settings = container.resolve("premium_api.tls_settings")
    worker = container.resolve("premium_api.worker")

    app = create_app(
        key_service=key_service,
        job_service=job_service,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        webhook_repository=webhook_repository,
        dispatcher=dispatcher,
        billing=billing,
        security_policy=security_policy,
        tls_settings=tls_settings,
    )

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()

    app.router.lifespan_context = _lifespan  # type: ignore[assignment]

    app.state.container = container  # stash container for debugging/inspection
    app.state.config = config
    return app


def main(argv: Optional[list[str]] = None) -> None:
    """CLI entrypoint that builds and runs the premium API application."""

    parser = argparse.ArgumentParser(description="Run the Atlas Orchestrator premium API service.")
    parser.add_argument("--config", type=Path, default=None, help="Optional configuration file path.")
    parser.add_argument("--project-root", type=Path, default=None, help="Override project root directory.")
    parser.add_argument("--host", default=os.getenv("ATLAS_ORCHESTRATOR_PREMIUM_API_HOST", "0.0.0.0"), help="Host interface to bind.")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("ATLAS_ORCHESTRATOR_PREMIUM_API_PORT", "8080")),
        help="TCP port to bind.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("ATLAS_ORCHESTRATOR_PREMIUM_API_LOG_LEVEL", "info"),
        help="Uvicorn log level.",
    )

    args = parser.parse_args(argv)

    app = build_application(config_path=args.config, project_root=args.project_root)

    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


__all__ = ["build_application", "main"]

if __name__ == "__main__":  # pragma: no cover - manual execution path
    main()

# Atlas Orchestrator

Foundational scaffolding for the Atlas Orchestrator workflow platform. This repository hosts the CLI and SDK skeleton along with shared infrastructure (configuration, dependency injection, logging) that other phases will extend.

## Getting Started

1. Create a virtual environment with Python 3.10+.
2. Install the package in editable mode:
   ```bash
   pip install -e .[dev]
   ```
3. Run diagnostics:
   ```bash
   atlas-orchestrator --health
   atlas-orchestrator --version
   ```

## Highlights

- **Provider Fallbacks**: Configure multiple AI providers with automatic failover in `atlas_orchestrator.yaml` (`ai.fallback_providers`).
- **Resumable Drafting**: Retry interrupted drafting runs with `atlas-orchestrator draft generate --resume`; progress is checkpointed under `.atlas_orchestrator/state/`.
- **Usage Analytics**: Telemetry-aware logging writes to `.atlas_orchestrator/metrics/`. Inspect summaries with `atlas-orchestrator observe usage` or disable tracking via `features.telemetry=false`.

## Project Structure

- `atlas_orchestrator/` - Python package with CLI, configuration loader, and core utilities.
- `.atlas_orchestrator/` - Workspace artifacts generated at runtime (plans, specs, drafts, validation).
- `docs/` - Architectural, product, and delivery documentation.
- `tests/` - Automated tests covering core scaffolding.

See `docs/` for detailed design and roadmap information.

## Documentation

- docs/CLI_HANDBOOK.md - CLI usage guide with full command reference.
- docs/SDK_QUICKSTART.md - Programmatic examples for integrating the SDK.
- docs/ACCEPTANCE_REPORT.md - Pilot testing summary and sign-off details.
- docs/POST_LAUNCH_SUPPORT.md - Support rotation and telemetry hand-off plan.
- docs/SYSTEM_ARCHITECTURE.md - Architecture blueprint with release and operations view.


"""Command line interface entry point for Atlas Orchestrator."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Annotated, Iterable, Mapping, Sequence

import typer

from . import __version__
from .config import ConfigLoader
from .container import DependencyContainer
from .logging import configure_logging
from .sdk import AtlasOrchestratorClient
from .specs import SpecificationCoverageError
from .validation import ValidationGateError
from .workflows import WorkflowExecutionError

app = typer.Typer(add_completion=False, help="Atlas Orchestrator workflow CLI")
plan_app = typer.Typer(help="Planning workflow operations")
spec_app = typer.Typer(help="Specification workflow operations")
draft_app = typer.Typer(help="Implementation drafting operations")
validate_app = typer.Typer(help="Validation workflow operations")
observe_app = typer.Typer(help="Observability insights")
admin_app = typer.Typer(help="Administrative operations")
app.add_typer(plan_app, name="plan")
app.add_typer(spec_app, name="spec")
app.add_typer(draft_app, name="draft")
app.add_typer(validate_app, name="validate")
app.add_typer(observe_app, name="observe")
app.add_typer(admin_app, name="admin")
_container = DependencyContainer()
_bootstrapped_client: AtlasOrchestratorClient | None = None

VersionFlag = Annotated[bool, typer.Option("--version", help="Show version information and exit")]
HealthFlag = Annotated[bool, typer.Option("--health", help="Run health diagnostics and exit")]
ConfigOption = Annotated[
    Path | None,
    typer.Option(
        "--config",
        help="Path to configuration file",
        exists=False,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
]
SpecModuleOption = Annotated[
    str | None,
    typer.Option("--module", help="Target a specific module identifier"),
]
DraftModuleOption = Annotated[
    str | None,
    typer.Option(
        "--module",
        "-m",
        help="Regenerate specific module identifiers (comma separated)",
    ),
]
SpecSectionOption = Annotated[
    list[str] | None,
    typer.Option(
        "--section",
        "-s",
        help="Filter output to the provided PRD requirement sections",
    ),
]
RefreshFlag = Annotated[
    bool,
    typer.Option("--refresh", help="Force context refresh before generation"),
]

ResumeFlag = Annotated[
    bool,
    typer.Option("--resume", help="Resume from previous progress if available"),
]
ValidateOverrideFlag = Annotated[
    bool,
    typer.Option("--override", help="Record an override when validations fail"),
]
ValidateReasonOption = Annotated[
    str | None,
    typer.Option("--reason", help="Reason provided when overriding validation failures"),
]

class OutputFormat(str, Enum):
    table = "table"
    json = "json"


OutputFormatOption = Annotated[
    OutputFormat,
    typer.Option(
        "--output",
        "-o",
        help="Choose result output format",
        case_sensitive=False,
        show_choices=True,
    ),
]




def _bootstrap(config_path: Path | None) -> AtlasOrchestratorClient:
    global _bootstrapped_client

    cwd = Path.cwd().resolve()
    if _bootstrapped_client is not None and config_path is None:
        if _bootstrapped_client.project_root == cwd:
            return _bootstrapped_client

    loader = ConfigLoader(project_root=cwd)
    config = loader.load(config_file=config_path)
    configure_logging(config.logging)

    _container.register_instance("config", config)
    client = AtlasOrchestratorClient(config=config, project_root=cwd, container=_container)
    if config_path is None and client.project_root == cwd:
        _bootstrapped_client = client
    return client



def _record_cli_usage(event: str, metadata: Mapping[str, object] | None = None) -> None:
    try:
        analytics = _container.resolve("analytics.usage")
    except KeyError:
        return
    analytics.record(event, metadata or {})

def _get_client(ctx: typer.Context) -> AtlasOrchestratorClient:
    obj = ctx.ensure_object(dict)
    existing = obj.get("client")
    if isinstance(existing, AtlasOrchestratorClient):
        return existing
    config_path = obj.get("config_path")
    client = _bootstrap(config_path)
    obj["client"] = client
    return client


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: VersionFlag = False,
    health: HealthFlag = False,
    config: ConfigOption = None,
) -> None:
    obj = ctx.ensure_object(dict)
    obj["config_path"] = config

    if version:
        typer.echo(__version__)
        raise typer.Exit()

    if health:
        client = _bootstrap(config)
        report = client.health()
        typer.echo(f"status={report['status']} version={report['version']}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo("Atlas Orchestrator CLI (try `atlas-orchestrator --health` or `atlas-orchestrator --help`)")
        raise typer.Exit()

    client = _bootstrap(config)
    obj["client"] = client
    obj["config"] = client.config


@app.command(help="Run health diagnostics")
def health(ctx: typer.Context) -> None:
    client = _get_client(ctx)
    report = client.health()
    typer.echo(f"status={report['status']} version={report['version']}")


@app.command(help="Show CLI version")
def version() -> None:
    typer.echo(__version__)


@plan_app.command("create", help="Generate a new plan artifact")
def plan_create(
    ctx: typer.Context,
    objective: Annotated[str, typer.Argument(help="Objective to plan against")],
    context: Annotated[str | None, typer.Option(help="Optional background context")] = None,
    output: OutputFormatOption = OutputFormat.table,
) -> None:
    client = _get_client(ctx)

    streamed = False

    if output is OutputFormat.table:
        def emitter(chunk: str) -> None:
            nonlocal streamed
            streamed = True
            typer.echo(chunk)
    else:
        emitter = None

    try:
        artifact = client.create_plan(objective, context=context, stream=emitter)
    except Exception as exc:
        _record_cli_usage(
            "cli.plan.create",
            {"status": "failure", "error": exc.__class__.__name__, "output": output.value},
        )
        raise
    _record_cli_usage(
        "cli.plan.create",
        {
            "status": "success",
            "provider": artifact.metadata.provider,
            "output": output.value,
        },
    )
    _emit_plan_result(artifact, output, streamed=streamed)


@plan_app.command("refine", help="Refine an existing plan with feedback")
def plan_refine(
    ctx: typer.Context,
    plan_id: Annotated[str, typer.Argument(help="Existing plan identifier")],
    feedback: Annotated[str, typer.Option("--feedback", prompt=True, help="Feedback to apply")],
) -> None:
    client = _get_client(ctx)

    def emitter(chunk: str) -> None:
        typer.echo(chunk)

    try:
        artifact = client.refine_plan(plan_id, feedback, stream=emitter)
    except Exception as exc:
        _record_cli_usage("cli.plan.refine", {"status": "failure", "error": exc.__class__.__name__, "plan_id": plan_id})
        raise
    _record_cli_usage("cli.plan.refine", {"status": "success", "plan_id": artifact.metadata.plan_id, "parent": plan_id})
    typer.echo(
        f"plan_id={artifact.metadata.plan_id} version={artifact.metadata.version} "
        f"parent={artifact.metadata.parent_plan_id}"
    )


@spec_app.command("generate", help="Generate specification for a plan")
def spec_generate(
    ctx: typer.Context,
    plan_id: Annotated[str, typer.Argument(help="Plan identifier to base the spec on")],
    module: SpecModuleOption = None,
    refresh: RefreshFlag = False,
    output: OutputFormatOption = OutputFormat.table,
) -> None:
    client = _get_client(ctx)

    streamed = False

    if output is OutputFormat.table:
        def emitter(chunk: str) -> None:
            nonlocal streamed
            streamed = True
            typer.echo(chunk)
    else:
        emitter = None

    try:
        artifact = client.generate_spec(
            plan_id,
            module_id=module,
            stream=emitter,
            force_refresh=refresh,
        )
    except SpecificationCoverageError as exc:
        _record_cli_usage(
            "cli.spec.generate",
            {
                "status": "failure",
                "error": "coverage",
                "plan_id": plan_id,
                "output": output.value,
            },
        )
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        _record_cli_usage(
            "cli.spec.generate",
            {
                "status": "failure",
                "error": exc.__class__.__name__,
                "plan_id": plan_id,
                "output": output.value,
            },
        )
        raise
    _record_cli_usage(
        "cli.spec.generate",
        {
            "status": "success",
            "plan_id": plan_id,
            "spec_id": artifact.metadata.spec_id,
            "modules": len(artifact.metadata.modules),
            "output": output.value,
        },
    )
    _emit_spec_result(artifact, output, streamed=streamed)


@spec_app.command("show", help="Show a specification artifact")
def spec_show(
    ctx: typer.Context,
    spec_id: Annotated[str, typer.Argument(help="Specification identifier")],
    section: SpecSectionOption = None,
) -> None:
    client = _get_client(ctx)
    sections = section or []
    artifact = client.get_spec(spec_id, sections=sections or None)
    _echo_coverage(artifact.document.coverage)
    typer.echo(json.dumps(artifact.document.model_dump(), indent=2))


@spec_app.command("diff", help="Show differences between two specs")
def spec_diff(
    ctx: typer.Context,
    first: Annotated[str, typer.Argument(help="Base specification identifier")],
    second: Annotated[str, typer.Argument(help="Specification identifier to compare")],
    section: SpecSectionOption = None,
) -> None:
    client = _get_client(ctx)
    sections = section or []
    diff = client.diff_specs(first, second, sections=sections or None)
    if not diff:
        typer.echo("Specifications are identical")
        return
    for line in diff:
        typer.echo(line)


@draft_app.command("generate", help="Generate implementation draft from a specification")
def draft_generate(
    ctx: typer.Context,
    spec_id: Annotated[str, typer.Argument(help="Specification identifier")],
    module: DraftModuleOption = None,
    resume: ResumeFlag = False,
    output: OutputFormatOption = OutputFormat.table,
) -> None:
    client = _get_client(ctx)
    modules = [item.strip() for item in module.split(",") if item.strip()] if module else []

    streamed = False

    if output is OutputFormat.table:
        def emitter(chunk: str) -> None:
            nonlocal streamed
            streamed = True
            typer.echo(chunk)
    else:
        emitter = None

    try:
        artifact = client.generate_draft(
            spec_id,
            module_ids=modules or None,
            resume=resume,
            stream=emitter,
        )
    except WorkflowExecutionError as exc:
        _record_cli_usage(
            "cli.draft.generate",
            {
                "status": "failure",
                "error": "workflow",
                "spec_id": spec_id,
                "resume_available": exc.resume_available,
                "output": output.value,
            },
        )
        typer.echo(str(exc), err=True)
        if exc.resume_available:
            typer.echo("Run again with --resume to continue from saved progress.", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        _record_cli_usage(
            "cli.draft.generate",
            {
                "status": "failure",
                "error": exc.__class__.__name__,
                "spec_id": spec_id,
                "output": output.value,
            },
        )
        raise
    _record_cli_usage(
        "cli.draft.generate",
        {
            "status": "success",
            "spec_id": spec_id,
            "draft_id": artifact.metadata.draft_id,
            "modules": len(artifact.metadata.modules),
            "resume": resume,
            "output": output.value,
        },
    )
    _emit_draft_result(artifact, output, streamed=streamed)


@draft_app.command("list", help="List available draft identifiers")
def draft_list(ctx: typer.Context) -> None:
    client = _get_client(ctx)
    drafts = client.list_drafts()
    if not drafts:
        typer.echo("No drafts found")
        return
    for draft_id in drafts:
        typer.echo(draft_id)


@admin_app.command("key-issue", help="Issue a premium API key for a customer")
def admin_key_issue(
    ctx: typer.Context,
    customer_id: Annotated[str, typer.Argument(help="Customer identifier")],
    plan_tier: Annotated[
        str,
        typer.Option(
            "--plan-tier",
            "-t",
            help="Label describing the customer plan tier",
            show_default=True,
        ),
    ] = "standard",
    rate_per_minute: Annotated[
        int | None,
        typer.Option(
            "--rate-per-minute",
            help="Override sustained requests allowed per minute",
            min=1,
        ),
    ] = None,
    burst: Annotated[
        int | None,
        typer.Option(
            "--burst",
            help="Override maximum burst capacity",
            min=1,
        ),
    ] = None,
    metadata: Annotated[
        list[str] | None,
        typer.Option(
            "--metadata",
            "-m",
            help="Additional metadata entries in key=value form",
        ),
    ] = None,
) -> None:
    _get_client(ctx)
    try:
        key_service = _container.resolve("premium_api.key_service")
        settings = _container.resolve("premium_api.settings")
    except KeyError as exc:
        typer.echo("Premium API services are not configured.", err=True)
        raise typer.Exit(code=1) from exc

    rate_limit = None
    if rate_per_minute is not None or burst is not None:
        per_minute = rate_per_minute or settings.rate_limit_per_minute
        burst_value = burst or settings.rate_limit_burst
        from atlas_orchestrator.premium_api.models import RateLimitSettings

        rate_limit = RateLimitSettings(per_minute=per_minute, burst=burst_value)

    metadata_dict: dict[str, str] = {}
    if metadata:
        for entry in metadata:
            if "=" not in entry:
                raise typer.BadParameter(f"Invalid metadata entry '{entry}'. Use key=value format.")
            key, value = entry.split("=", 1)
            metadata_dict[key.strip()] = value.strip()

    material = key_service.issue_key(
        customer_id=customer_id,
        plan_tier=plan_tier,
        rate_limit=rate_limit,
        metadata=metadata_dict or None,
    )
    payload = material.model_dump()
    payload["created_at"] = material.created_at.isoformat()
    typer.echo(json.dumps(payload, indent=2))


@observe_app.command("usage", help="Show usage analytics summary")
def observe_usage(ctx: typer.Context) -> None:
    _get_client(ctx)
    try:
        analytics = _container.resolve("analytics.usage")
    except KeyError:
        typer.echo("Analytics disabled; set features.telemetry=true to enable tracking.")
        return
    _record_cli_usage("cli.observe.usage", {"status": "success"})
    summary = analytics.snapshot()
    typer.echo(json.dumps(summary, indent=2))


@validate_app.command("run", help="Run validation checks for a draft")
def validate_run(
    ctx: typer.Context,
    draft_id: Annotated[str, typer.Argument(help="Draft identifier")],
    override: ValidateOverrideFlag = False,
    reason: ValidateReasonOption = None,
) -> None:
    client = _get_client(ctx)

    def emitter(chunk: str) -> None:
        typer.echo(chunk)

    try:
        artifact = client.run_validation(draft_id, override=override, reason=reason, stream=emitter)
    except Exception as exc:
        _record_cli_usage(
            "cli.validate.run",
            {"status": "failure", "error": exc.__class__.__name__, "draft_id": draft_id},
        )
        raise

    _record_cli_usage(
        "cli.validate.run",
        {
            "status": artifact.metadata.status,
            "draft_id": draft_id,
            "validation_id": artifact.metadata.validation_id,
        },
    )
    typer.echo(
        f"validation_id={artifact.metadata.validation_id} status={artifact.metadata.status} "
        f"checks={len(artifact.document.checks)}"
    )
    if artifact.document.remediation:
        typer.echo("remediation:")
        for item in artifact.document.remediation:
            typer.echo(f"  - {item}")


@validate_app.command("publish", help="Ensure a draft is publishable based on validation status")
def validate_publish(
    ctx: typer.Context,
    draft_id: Annotated[str, typer.Argument(help="Draft identifier")],
    override: ValidateOverrideFlag = False,
    reason: ValidateReasonOption = None,
) -> None:
    client = _get_client(ctx)
    override_reason = reason if override else None
    if override and not override_reason:
        override_reason = "Override recorded via CLI"
    try:
        client.ensure_draft_publishable(draft_id, override_reason=override_reason)
    except ValidationGateError as exc:
        _record_cli_usage(
            "cli.validate.publish",
            {"status": "blocked", "draft_id": draft_id, "error": exc.__class__.__name__},
        )
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    _record_cli_usage(
        "cli.validate.publish",
        {
            "status": "allowed" if not override_reason else "override",
            "draft_id": draft_id,
        },
    )
    typer.echo("publishable=true")


@draft_app.command("show", help="Show a draft artifact and tooling results")
def draft_show(
    ctx: typer.Context,
    draft_id: Annotated[str, typer.Argument(help="Draft identifier")],
) -> None:
    client = _get_client(ctx)
    artifact = client.get_draft(draft_id)
    _echo_tool_results(artifact.metadata.tool_results)
    typer.echo(json.dumps(artifact.document.model_dump(), indent=2))


def _emit_plan_result(artifact, output: OutputFormat, *, streamed: bool) -> None:
    if output is OutputFormat.json:
        typer.echo(json.dumps(artifact.model_dump_with_metadata(), indent=2))
        return
    if streamed:
        typer.echo()
    typer.echo(_format_summary_table("Plan Summary", _plan_summary_rows(artifact)))


def _emit_spec_result(artifact, output: OutputFormat, *, streamed: bool) -> None:
    if output is OutputFormat.json:
        typer.echo(json.dumps(artifact.model_dump_with_metadata(), indent=2))
        return
    if streamed:
        typer.echo()
    typer.echo(_format_summary_table("Spec Summary", _spec_summary_rows(artifact)))


def _emit_draft_result(artifact, output: OutputFormat, *, streamed: bool) -> None:
    if output is OutputFormat.json:
        typer.echo(json.dumps(artifact.model_dump_with_metadata(), indent=2))
        return
    if streamed:
        typer.echo()
    typer.echo(_format_summary_table("Draft Summary", _draft_summary_rows(artifact)))


def _plan_summary_rows(artifact) -> list[tuple[str, str]]:
    rows = [
        ("Plan ID", artifact.metadata.plan_id),
        ("Version", artifact.metadata.version),
        ("Provider", artifact.metadata.provider),
        ("Created", artifact.metadata.created_at.isoformat()),
        ("Source", artifact.metadata.source),
        ("Parent Plan", artifact.metadata.parent_plan_id or "-"),
        ("Milestones", f"{len(getattr(artifact.plan, 'milestones', []))} total"),
        ("Usage", _format_usage(getattr(artifact.metadata, "usage", None))),
    ]
    return _prepare_rows(rows)


def _spec_summary_rows(artifact) -> list[tuple[str, str]]:
    coverage = getattr(artifact.document, "coverage", [])
    rows = [
        ("Spec ID", artifact.metadata.spec_id),
        ("Plan ID", artifact.metadata.plan_id),
        ("Version", artifact.metadata.version),
        ("Provider", artifact.metadata.provider),
        ("Created", artifact.metadata.created_at.isoformat()),
        ("Modules", _format_modules_list(artifact.metadata.modules)),
        ("Coverage", _format_coverage_summary(coverage)),
        ("Usage", _format_usage(getattr(artifact.metadata, "usage", None))),
    ]
    return _prepare_rows(rows)


def _draft_summary_rows(artifact) -> list[tuple[str, str]]:
    metadata = artifact.metadata
    rows = [
        ("Draft ID", metadata.draft_id),
        ("Spec ID", metadata.spec_id),
        ("Version", metadata.version),
        ("Provider", metadata.provider),
        ("Created", metadata.created_at.isoformat()),
        ("Modules", _format_modules_list(metadata.modules)),
        ("Targets", _format_modules_list(metadata.target_modules)),
        ("Validation", metadata.validation_status),
        ("Tool Results", _format_tool_results(metadata.tool_results)),
        ("Usage", _format_usage(getattr(metadata, "usage", None))),
    ]
    return _prepare_rows(rows)


def _prepare_rows(rows: Iterable[tuple[str, object]]) -> list[tuple[str, str]]:
    prepared: list[tuple[str, str]] = []
    for label, value in rows:
        prepared.append((label, _stringify_value(value)))
    return prepared


def _format_summary_table(title: str, rows: Sequence[tuple[str, str]]) -> str:
    if not rows:
        return title
    max_label = max(len(label) for label, _ in rows)
    max_label = max(max_label, len("Field"))
    lines = [
        title,
        "=" * len(title),
        "",
        f"{'Field':<{max_label}}  Value",
        f"{'-' * max_label}  -----",
    ]
    lines.extend(f"{label:<{max_label}}  {value}" for label, value in rows)
    return "\n".join(lines)


def _format_usage(usage) -> str:
    if usage is None:
        return "-"
    total_cost = getattr(usage, "total_cost", None)
    cost = f"${total_cost:.6f}" if isinstance(total_cost, (float, int)) else "-"
    return (
        f"model={getattr(usage, 'model', '-')}, "
        f"input={getattr(usage, 'input_tokens', '-')}, "
        f"output={getattr(usage, 'output_tokens', '-')}, "
        f"cost={cost}"
    )


def _format_modules_list(modules: Sequence[str]) -> str:
    if not modules:
        return "-"
    if len(modules) <= 3:
        return ", ".join(modules)
    preview = ", ".join(modules[:3])
    remaining = len(modules) - 3
    return f"{len(modules)} total ({preview}, +{remaining} more)"


def _format_coverage_summary(coverage: Sequence) -> str:
    if not coverage:
        return "n/a"
    total = len(coverage)
    gaps = sum(1 for entry in coverage if getattr(entry, "status", "") == "gap")
    if gaps:
        return f"{total} entries (gaps={gaps})"
    return f"{total} entries"


def _format_tool_results(results: Sequence) -> str:
    if not results:
        return "none"
    statuses = {getattr(r, "status", "-") for r in results}
    return f"{len(results)} recorded ({', '.join(sorted(statuses))})"


def _stringify_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, set)):
        if not value:
            return "-"
        return ", ".join(str(item) for item in value)
    return str(value)


def _echo_coverage(coverage: Sequence) -> None:
    if not coverage:
        return
    typer.echo("coverage:")
    for entry in coverage:
        sections = ",".join(entry.sections) if entry.sections else "n/a"
        typer.echo(
            f"  module={entry.module_id} requirements={entry.total_requirements} sections={sections}"
        )


def _echo_tool_results(results: Sequence) -> None:
    if not results:
        return
    typer.echo("tooling:")
    for result in results:
        typer.echo(
            f"  tool={result.tool} module={result.module_id} status={result.status} output={result.output}"
        )


def main() -> None:  # pragma: no cover - console entry point
    app()


__all__ = ["app", "main"]






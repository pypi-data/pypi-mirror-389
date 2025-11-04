"""Validation service orchestrating automated checks and gating."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Iterable, Sequence
from uuid import uuid4

from atlas_orchestrator.analytics import UsageAnalytics
from atlas_orchestrator.drafting import DraftArtifact, DraftRepository
from atlas_orchestrator.drafting.models import DraftMetadata, DraftModule
from atlas_orchestrator.specs import SpecificationArtifact, SpecificationRepository

from .models import ValidationArtifact, ValidationCheck, ValidationDocument, ValidationMetadata
from .repository import ValidationRepository
from .runner import PytestReport, PytestRunner

StreamCallback = Callable[[str], None]


class ValidationGateError(RuntimeError):
    """Raised when publication gating blocks draft release."""

    def __init__(self, draft_id: str, status: str) -> None:
        super().__init__(f"Draft '{draft_id}' cannot be published; validation status is '{status}'.")
        self.draft_id = draft_id
        self.status = status


class ValidationService:
    """Runs validation workflows and maintains gating state."""

    def __init__(
        self,
        *,
        draft_repository: DraftRepository,
        specification_repository: SpecificationRepository,
        validation_repository: ValidationRepository,
        pytest_runner: PytestRunner,
        analytics: UsageAnalytics | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._draft_repository = draft_repository
        self._spec_repository = specification_repository
        self._validation_repository = validation_repository
        self._pytest_runner = pytest_runner
        self._analytics = analytics
        self._clock = clock or datetime.utcnow

    def run(
        self,
        draft_id: str,
        *,
        override: bool = False,
        reason: str | None = None,
        stream: StreamCallback | None = None,
        pytest_args: Sequence[str] | None = None,
    ) -> ValidationArtifact:
        draft = self._draft_repository.load(draft_id)
        spec = self._spec_repository.load(draft.metadata.spec_id)

        self._emit(stream, f"validating draft={draft_id} spec={spec.metadata.spec_id}")

        pytest_report = self._pytest_runner.run(pytest_args)
        checks = [self._build_pytest_check(pytest_report)]
        remediation: list[str] = []
        if pytest_report.status != "passed":
            remediation.append("Investigate failing pytest suite; see captured output for details.")

        semantic_checks, semantic_remediation = self._semantic_checks(draft, spec)
        checks.extend(semantic_checks)
        remediation.extend(semantic_remediation)

        status = "passed" if all(check.status == "passed" for check in checks) else "failed"
        override_reason = None
        if status == "failed" and override:
            status = "overridden"
            override_reason = reason or "Override accepted without reason provided."
            remediation.append("Validation failures overridden; address outstanding issues before release.")

        metadata = ValidationMetadata(
            validation_id=uuid4().hex,
            status=status,
            draft_id=draft.metadata.draft_id,
            spec_id=spec.metadata.spec_id,
            created_at=self._clock(),
            override_reason=override_reason,
        )
        document = ValidationDocument(
            draft_id=draft.metadata.draft_id,
            spec_id=spec.metadata.spec_id,
            checks=checks,
            remediation=remediation,
        )
        artifact = ValidationArtifact(document=document, metadata=metadata)

        self._validation_repository.save(artifact)
        self._update_draft_metadata(draft, metadata)

        self._emit(stream, f"validation status={metadata.status} record={metadata.validation_id}")
        self._record_usage(
            "validation.run",
            {
                "draft_id": draft.metadata.draft_id,
                "status": metadata.status,
                "override": bool(override_reason),
                "checks": len(checks),
            },
        )
        return artifact

    def ensure_publishable(
        self,
        draft_id: str,
        *,
        override_reason: str | None = None,
    ) -> None:
        draft = self._draft_repository.load(draft_id)
        status = draft.metadata.validation_status
        if status in {"passed", "overridden"}:
            self._record_usage(
                "validation.publish",
                {"draft_id": draft_id, "status": status, "override": False},
            )
            return

        if override_reason:
            updated = draft.metadata.model_copy(
                update={
                    "validation_status": "overridden",
                    "validation_override_reason": override_reason,
                }
            )
            self._draft_repository.update_metadata(draft_id, updated)
            self._record_usage(
                "validation.publish",
                {"draft_id": draft_id, "status": "overridden", "override": True},
            )
            return

        self._record_usage(
            "validation.publish",
            {"draft_id": draft_id, "status": status, "override": False},
        )
        raise ValidationGateError(draft_id, status)

    def latest(self, draft_id: str) -> ValidationArtifact | None:
        return self._validation_repository.latest_for_draft(draft_id)

    def _build_pytest_check(self, report: PytestReport) -> ValidationCheck:
        summary = (
            f"pytest status={report.status} passed={report.passed} "
            f"failed={report.failed} errors={report.errors}"
        )
        details = report.output[-2000:] if report.output else None
        return ValidationCheck(
            id="checks::pytest",
            name="pytest suite",
            kind="tests",
            status="passed" if report.status == "passed" else "failed",
            summary=summary,
            details=details,
            metadata={
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "errors": report.errors,
                "duration": report.duration,
            },
        )

    def _semantic_checks(
        self,
        draft: DraftArtifact,
        spec: SpecificationArtifact,
    ) -> tuple[list[ValidationCheck], list[str]]:
        checks: list[ValidationCheck] = []
        remediation: list[str] = []
        draft_modules = {module.id: module for module in draft.document.modules}
        spec_modules = {module.id: module for module in spec.document.modules}

        for module_id, spec_module in spec_modules.items():
            draft_module = draft_modules.get(module_id)
            requirement_ids = [trace.requirement_id for trace in spec_module.traces]
            if draft_module is None:
                checks.append(
                    ValidationCheck(
                        id=f"semantic::{module_id}::missing",
                        name=f"module {module_id}",
                        kind="semantic",
                        status="failed",
                        summary="Draft module missing for specification module.",
                        requirement_ids=requirement_ids,
                    )
                )
                remediation.append(
                    f"Regenerate draft module '{module_id}' to cover spec acceptance criteria."
                )
                continue

            failures = list(self._module_gaps(draft_module, spec_module))
            if failures:
                status = "failed"
                summary = "; ".join(failures)
                remediation.append(
                    f"Address semantic gaps for module '{module_id}': {summary}."
                )
            else:
                status = "passed"
                summary = "Draft module covers acceptance criteria and requirements traces."

            checks.append(
                ValidationCheck(
                    id=f"semantic::{module_id}",
                    name=f"module {module_id}",
                    kind="semantic",
                    status=status,
                    summary=summary,
                    requirement_ids=requirement_ids,
                )
            )

        extra_modules = set(draft_modules) - set(spec_modules)
        if extra_modules:
            remediation.append(
                "Prune draft modules without matching specification entries: "
                + ", ".join(sorted(extra_modules))
            )
            checks.append(
                ValidationCheck(
                    id="semantic::extraneous",
                    name="extraneous modules",
                    kind="semantic",
                    status="failed",
                    summary="Draft contains modules not present in specification.",
                    requirement_ids=[],
                    metadata={"modules": sorted(extra_modules)},
                )
            )

        return checks, remediation

    def _module_gaps(self, draft_module: DraftModule, spec_module) -> Iterable[str]:
        missing_acceptance = [
            criterion
            for criterion in spec_module.acceptance_criteria
            if criterion not in draft_module.content
        ]
        if missing_acceptance:
            yield "missing acceptance criteria: " + ", ".join(missing_acceptance)

        missing_traces = [
            trace.requirement_id
            for trace in spec_module.traces
            if trace.requirement_id not in draft_module.content
        ]
        if missing_traces:
            yield "missing requirement trace IDs: " + ", ".join(missing_traces)

    def _update_draft_metadata(self, draft: DraftArtifact, metadata: ValidationMetadata) -> None:
        status_map = {
            "passed": "passed",
            "failed": "failed",
            "overridden": "overridden",
        }
        updated = draft.metadata.model_copy(
            update={
                "validation_status": status_map[metadata.status],
                "validation_record_id": metadata.validation_id,
                "validation_override_reason": metadata.override_reason,
            }
        )
        self._draft_repository.update_metadata(draft.metadata.draft_id, updated)

    def _emit(self, stream: StreamCallback | None, message: str) -> None:
        if stream is not None:
            stream(message)

    def _record_usage(self, event: str, metadata: dict[str, object]) -> None:
        if self._analytics is None:
            return
        self._analytics.record(event, metadata)


__all__ = ["ValidationGateError", "ValidationService", "StreamCallback"]

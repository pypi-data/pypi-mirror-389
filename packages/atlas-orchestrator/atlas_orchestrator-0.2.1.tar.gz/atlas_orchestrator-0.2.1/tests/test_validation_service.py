from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from atlas_orchestrator.analytics import UsageAnalytics
from atlas_orchestrator.drafting import DraftRepository
from atlas_orchestrator.validation import PytestReport, ValidationGateError, ValidationRepository, ValidationService

from tests.test_drafting_service import WORKSPACE, _build_drafting_service, _build_spec_infrastructure


class StubPytestRunner:
    def __init__(self, report: PytestReport) -> None:
        self.report = report
        self.calls: list[tuple[str, ...] | None] = []

    def run(self, args=None) -> PytestReport:
        self.calls.append(tuple(args) if args else None)
        return self.report


def _make_validation_service(tmp_path: Path, report: PytestReport) -> tuple[ValidationService, str]:
    spec_repo, _, spec_id = _build_spec_infrastructure(tmp_path)
    drafting_service = _build_drafting_service(tmp_path, spec_repo)
    draft_artifact = drafting_service.generate(spec_id)
    draft_repo = DraftRepository(project_root=tmp_path, workspace=WORKSPACE)
    validation_repo = ValidationRepository(project_root=tmp_path, workspace=WORKSPACE)
    analytics = UsageAnalytics(tmp_path / WORKSPACE / "metrics")
    runner = StubPytestRunner(report)
    service = ValidationService(
        draft_repository=draft_repo,
        specification_repository=spec_repo,
        validation_repository=validation_repo,
        pytest_runner=runner,
        analytics=analytics,
        clock=lambda: datetime(2025, 1, 3),
    )
    return service, draft_artifact.metadata.draft_id


def _mutate_draft(tmp_path: Path, draft_id: str, module_id: str) -> None:
    module_path = tmp_path / "generated" / draft_id / f"{module_id}.py"
    module_path.write_text("# overridden module\n", encoding="utf-8")


def test_validation_service_pass(tmp_path: Path) -> None:
    service, draft_id = _make_validation_service(
        tmp_path,
        PytestReport(exit_code=0, total=3, passed=3, failed=0, errors=0, duration=0.1, output="3 passed in 0.10s"),
    )

    artifact = service.run(draft_id)

    assert artifact.metadata.status == "passed"
    draft = service._draft_repository.load(draft_id)
    assert draft.metadata.validation_status == "passed"
    assert draft.metadata.validation_record_id == artifact.metadata.validation_id


def test_validation_service_failure_without_override(tmp_path: Path) -> None:
    service, draft_id = _make_validation_service(
        tmp_path,
        PytestReport(exit_code=0, total=1, passed=1, failed=0, errors=0, duration=0.1, output="1 passed"),
    )

    draft = service._draft_repository.load(draft_id)
    _mutate_draft(tmp_path, draft_id, draft.document.modules[0].id)

    artifact = service.run(draft_id)

    assert artifact.metadata.status == "failed"
    draft = service._draft_repository.load(draft_id)
    assert draft.metadata.validation_status == "failed"


def test_validation_service_override(tmp_path: Path) -> None:
    service, draft_id = _make_validation_service(
        tmp_path,
        PytestReport(exit_code=1, total=1, passed=0, failed=1, errors=0, duration=0.1, output="1 failed"),
    )

    draft = service._draft_repository.load(draft_id)
    _mutate_draft(tmp_path, draft_id, draft.document.modules[0].id)

    artifact = service.run(draft_id, override=True, reason="Risk accepted")

    assert artifact.metadata.status == "overridden"
    draft = service._draft_repository.load(draft_id)
    assert draft.metadata.validation_status == "overridden"
    assert draft.metadata.validation_override_reason == "Risk accepted"


def test_validation_publication_gate(tmp_path: Path) -> None:
    service, draft_id = _make_validation_service(
        tmp_path,
        PytestReport(exit_code=0, total=1, passed=1, failed=0, errors=0, duration=0.1, output="1 passed"),
    )

    service.run(draft_id)
    service.ensure_publishable(draft_id)

    draft = service._draft_repository.load(draft_id)
    draft_path = tmp_path / "generated" / draft_id / f"{draft.document.modules[0].id}.py"
    draft_path.write_text("# broken", encoding="utf-8")
    service.run(draft_id)

    with pytest.raises(ValidationGateError):
        service.ensure_publishable(draft_id)

    service.ensure_publishable(draft_id, override_reason="Emergency release")
    updated = service._draft_repository.load(draft_id)
    assert updated.metadata.validation_status == "overridden"
    assert updated.metadata.validation_override_reason == "Emergency release"

"""Tests covering the validation repository persistence helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pytest

from atlas_orchestrator.validation.models import (
    ValidationArtifact,
    ValidationCheck,
    ValidationDocument,
    ValidationMetadata,
)
from atlas_orchestrator.validation.repository import ValidationRepository, ValidationRepositoryError


def _artifact(validation_id: str, *, created_at: datetime) -> ValidationArtifact:
    document = ValidationDocument(
        draft_id="draft-1",
        spec_id="spec-1",
        checks=[
            ValidationCheck(
                id="tests",
                name="unit-tests",
                kind="tests",
                status="passed",
                summary="all tests passed",
            )
        ],
    )
    metadata = ValidationMetadata(
        validation_id=validation_id,
        status="passed",
        draft_id="draft-1",
        spec_id="spec-1",
        created_at=created_at,
    )
    return ValidationArtifact(document=document, metadata=metadata)


def _collect(iterable: Iterable) -> list:
    return list(iterable)


def test_validation_repository_roundtrip(tmp_path: Path) -> None:
    repo = ValidationRepository(project_root=tmp_path, workspace=".workspace")
    first = _artifact("VAL-001", created_at=datetime.now(timezone.utc) - timedelta(minutes=5))
    second = _artifact("VAL-002", created_at=datetime.now(timezone.utc))

    repo.save(first)
    repo.save(second)

    assert repo.load("VAL-001").metadata.validation_id == "VAL-001"
    assert sorted(_collect(repo.list_ids())) == ["VAL-001", "VAL-002"]

    artifacts = _collect(repo.list_by_draft("draft-1"))
    assert {a.metadata.validation_id for a in artifacts} == {"VAL-001", "VAL-002"}

    latest = repo.latest_for_draft("draft-1")
    assert latest is not None and latest.metadata.validation_id == "VAL-002"


def test_validation_repository_errors_when_missing(tmp_path: Path) -> None:
    repo = ValidationRepository(project_root=tmp_path, workspace=".workspace")
    with pytest.raises(ValidationRepositoryError):
        repo.load("missing")

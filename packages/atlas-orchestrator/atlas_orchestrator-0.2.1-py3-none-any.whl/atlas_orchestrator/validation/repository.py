"""Validation artifact persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import ValidationArtifact, ValidationMetadata


class ValidationRepositoryError(RuntimeError):
    """Raised when validation artifacts cannot be stored or retrieved."""


@dataclass
class ValidationRepository:
    """Persist validation artifacts and expose lookup helpers."""

    project_root: Path
    workspace: str

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()
        self._validation_dir = self.project_root / self.workspace / "validation"
        self._validation_dir.mkdir(parents=True, exist_ok=True)

    @property
    def validation_dir(self) -> Path:
        return self._validation_dir

    def save(self, artifact: ValidationArtifact) -> Path:
        path = self._validation_dir / f"{artifact.metadata.validation_id}.json"
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(artifact.model_dump_with_metadata(), handle, indent=2)
        except OSError as exc:
            raise ValidationRepositoryError(f"Failed to persist validation artifact: {path}") from exc
        return path

    def load(self, validation_id: str) -> ValidationArtifact:
        path = self._validation_dir / f"{validation_id}.json"
        if not path.exists():
            raise ValidationRepositoryError(f"Validation '{validation_id}' not found")
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationRepositoryError(f"Failed to load validation artifact: {path}") from exc
        return ValidationArtifact.model_validate_with_metadata(data)

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self._validation_dir.glob("*.json")):
            yield file.stem

    def list_by_draft(self, draft_id: str) -> Iterable[ValidationArtifact]:
        for validation_id in self.list_ids():
            artifact = self.load(validation_id)
            if artifact.metadata.draft_id == draft_id:
                yield artifact

    def latest_for_draft(self, draft_id: str) -> ValidationArtifact | None:
        latest: tuple[ValidationMetadata, ValidationArtifact] | None = None
        for artifact in self.list_by_draft(draft_id):
            metadata = artifact.metadata
            if latest is None or metadata.created_at > latest[0].created_at:
                latest = (metadata, artifact)
        return latest[1] if latest else None


__all__ = ["ValidationRepository", "ValidationRepositoryError"]

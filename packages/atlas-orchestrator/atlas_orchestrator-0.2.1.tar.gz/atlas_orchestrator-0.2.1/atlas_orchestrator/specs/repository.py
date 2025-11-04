"""Specification repository."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import SpecificationArtifact


class SpecificationRepositoryError(RuntimeError):
    """Raised when specification artifacts cannot be handled."""


@dataclass
class SpecificationRepository:
    project_root: Path
    workspace: str

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()
        self._specs_dir = self.project_root / self.workspace / "specs"
        self._specs_dir.mkdir(parents=True, exist_ok=True)

    @property
    def specs_dir(self) -> Path:
        return self._specs_dir

    def save(self, artifact: SpecificationArtifact) -> Path:
        path = self._specs_dir / f"{artifact.metadata.spec_id}.json"
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(artifact.model_dump_with_metadata(), handle, indent=2)
        except OSError as exc:
            raise SpecificationRepositoryError(f"Failed to persist specification: {path}") from exc
        return path

    def load(self, spec_id: str) -> SpecificationArtifact:
        path = self._specs_dir / f"{spec_id}.json"
        if not path.exists():
            raise SpecificationRepositoryError(f"Specification '{spec_id}' not found")
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise SpecificationRepositoryError(f"Failed to load specification: {path}") from exc
        return SpecificationArtifact.model_validate_with_metadata(data)

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self._specs_dir.glob("*.json")):
            yield file.stem

    def list_by_plan(self, plan_id: str) -> Iterable[SpecificationArtifact]:
        for spec_id in self.list_ids():
            artifact = self.load(spec_id)
            if artifact.metadata.plan_id == plan_id:
                yield artifact


__all__ = ["SpecificationRepository", "SpecificationRepositoryError"]


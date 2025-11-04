"""Plan artifact persistence layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import PlanArtifact


class PlanRepositoryError(RuntimeError):
    """Raised when plan artifacts cannot be persisted or retrieved."""


@dataclass
class PlanRepository:
    """File-system backed repository for plan artifacts."""

    project_root: Path
    workspace: str

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()
        self._plans_dir = self.project_root / self.workspace / "plans"
        self._plans_dir.mkdir(parents=True, exist_ok=True)

    @property
    def plans_dir(self) -> Path:
        return self._plans_dir

    def path_for(self, plan_id: str) -> Path:
        return self._plans_dir / f"{plan_id}.json"

    def save(self, artifact: PlanArtifact) -> Path:
        path = self.path_for(artifact.metadata.plan_id)
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(artifact.model_dump_with_metadata(), handle, indent=2)
        except OSError as exc:
            raise PlanRepositoryError(f"Failed to persist plan artifact: {path}") from exc
        return path

    def load(self, plan_id: str) -> PlanArtifact:
        path = self.path_for(plan_id)
        if not path.exists():
            raise PlanRepositoryError(f"Plan '{plan_id}' not found at {path}")
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise PlanRepositoryError(f"Failed to load plan artifact: {path}") from exc
        return PlanArtifact.model_validate_with_metadata(data)

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self._plans_dir.glob("*.json")):
            yield file.stem


__all__ = ["PlanRepository", "PlanRepositoryError"]

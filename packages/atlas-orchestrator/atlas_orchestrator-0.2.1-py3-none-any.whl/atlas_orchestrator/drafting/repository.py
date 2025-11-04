"""Draft artifact persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import DraftArtifact, DraftMetadata


class DraftRepositoryError(RuntimeError):
    """Raised when draft artifacts cannot be stored or retrieved."""


@dataclass
class DraftRepository:
    """Persist draft artifacts and generated code bundles."""

    project_root: Path
    workspace: str

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()
        self._drafts_dir = self.project_root / self.workspace / "drafts"
        self._generated_dir = self.project_root / "generated"
        self._drafts_dir.mkdir(parents=True, exist_ok=True)
        self._generated_dir.mkdir(parents=True, exist_ok=True)

    @property
    def drafts_dir(self) -> Path:
        return self._drafts_dir

    @property
    def generated_dir(self) -> Path:
        return self._generated_dir

    def save(self, artifact: DraftArtifact) -> Path:
        draft_path = self._drafts_dir / f"{artifact.metadata.draft_id}.json"
        bundle_dir = self._generated_dir / artifact.metadata.draft_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        try:
            for module in artifact.document.modules:
                module_path = bundle_dir / module.path
                module_path.parent.mkdir(parents=True, exist_ok=True)
                payload = self._with_header(module, artifact)
                module_path.write_text(payload, encoding="utf-8")
            with draft_path.open("w", encoding="utf-8") as handle:
                json.dump(artifact.model_dump_with_metadata(), handle, indent=2)
        except OSError as exc:
            raise DraftRepositoryError(f"Failed to persist draft artifact: {draft_path}") from exc
        return draft_path

    def load(self, draft_id: str) -> DraftArtifact:
        draft_path = self._drafts_dir / f"{draft_id}.json"
        if not draft_path.exists():
            raise DraftRepositoryError(f"Draft '{draft_id}' not found")
        try:
            with draft_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DraftRepositoryError(f"Failed to load draft artifact: {draft_path}") from exc
        artifact = DraftArtifact.model_validate_with_metadata(data)
        bundle_dir = self._generated_dir / draft_id
        modules: list = []
        for module in artifact.document.modules:
            module_path = bundle_dir / module.path
            if module_path.exists():
                module_content = module_path.read_text(encoding="utf-8")
                modules.append(module.model_copy(update={"content": module_content}))
            else:
                modules.append(module)
        updated_document = artifact.document.model_copy(update={"modules": modules})
        return artifact.model_copy(update={"document": updated_document})

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self._drafts_dir.glob("*.json")):
            yield file.stem

    def list_by_spec(self, spec_id: str) -> Iterable[DraftArtifact]:
        for draft_id in self.list_ids():
            artifact = self.load(draft_id)
            if artifact.metadata.spec_id == spec_id:
                yield artifact

    def update_metadata(self, draft_id: str, metadata: DraftMetadata) -> None:
        draft_path = self._drafts_dir / f"{draft_id}.json"
        if not draft_path.exists():
            raise DraftRepositoryError(f"Draft '{draft_id}' not found")
        try:
            with draft_path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DraftRepositoryError(f"Failed to update draft metadata: {draft_path}") from exc
        data['metadata'] = metadata.model_dump()
        data['metadata']['created_at'] = metadata.created_at.isoformat()
        try:
            with draft_path.open('w', encoding='utf-8') as handle:
                json.dump(data, handle, indent=2)
        except OSError as exc:
            raise DraftRepositoryError(f"Failed to write draft metadata: {draft_path}") from exc

    def _with_header(self, module, artifact: DraftArtifact) -> str:
        header = [
            "# === Atlas Orchestrator GENERATED CODE ===",
            f"# Draft: {artifact.metadata.draft_id} (version {artifact.metadata.version})",
            f"# Spec: {artifact.metadata.spec_id}",
            f"# Module: {module.id} - {module.title}",
        ]
        body = module.content
        if not body.endswith("\n"):
            body += "\n"
        return "\n".join(header) + "\n\n" + body


__all__ = ["DraftRepository", "DraftRepositoryError"]

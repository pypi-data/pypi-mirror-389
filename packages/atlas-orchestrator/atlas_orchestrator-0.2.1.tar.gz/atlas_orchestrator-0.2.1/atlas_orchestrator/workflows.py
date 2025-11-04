"""Workflow state tracking and resumable execution utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, MutableMapping


class WorkflowExecutionError(RuntimeError):
    """Raised when a workflow fails but can be resumed."""

    def __init__(
        self,
        workflow: str,
        key: str,
        message: str,
        *,
        resume_available: bool = False,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.workflow = workflow
        self.key = key
        self.resume_available = resume_available
        self.__cause__ = cause


@dataclass
class WorkflowStateStore:
    """Persist workflow progress for resumable operations."""

    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def load(self, workflow: str, key: str) -> MutableMapping[str, Any]:
        path = self._path(workflow, key)
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):  # pragma: no cover - corrupted state fallback
            return {}

    def update(self, workflow: str, key: str, data: Mapping[str, Any]) -> None:
        with self._lock:
            state = self.load(workflow, key)
            state.update(data)
            state["updated_at"] = datetime.utcnow().isoformat()
            self._write_state(workflow, key, state)

    def clear(self, workflow: str, key: str) -> None:
        path = self._path(workflow, key)
        if path.exists():
            try:
                path.unlink()
            except OSError:  # pragma: no cover - ignore cleanup failures
                path.write_text("{}", encoding="utf-8")

    def _write_state(self, workflow: str, key: str, state: Mapping[str, Any]) -> None:
        path = self._path(workflow, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)

    def _path(self, workflow: str, key: str) -> Path:
        safe_workflow = workflow.replace("/", "-")
        safe_key = key.replace("/", "-")
        return self.root / safe_workflow / f"{safe_key}.json"


__all__ = ["WorkflowExecutionError", "WorkflowStateStore"]

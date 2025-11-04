"""File-based cache for context bundles."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ContextBundle


class ContextCache:
    """Persists context bundles under the project workspace."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def path_for(self, plan_id: str) -> Path:
        return self._root / f"{plan_id}.json"

    def get(self, plan_id: str) -> ContextBundle | None:
        path = self.path_for(plan_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return ContextBundle.model_validate(data)

    def set(self, bundle: ContextBundle) -> Path:
        path = self.path_for(bundle.plan_id)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(bundle.model_dump(mode="json"), handle, indent=2)
        return path

    def invalidate(self, plan_id: str) -> None:
        path = self.path_for(plan_id)
        if path.exists():
            path.unlink()


__all__ = ["ContextCache"]

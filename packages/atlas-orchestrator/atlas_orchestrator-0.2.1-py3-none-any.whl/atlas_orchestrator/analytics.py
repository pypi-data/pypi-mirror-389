"""Usage analytics collector for CLI and SDK instrumentation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, MutableMapping


class UsageAnalytics:
    """Append-only usage tracker with aggregated summaries."""

    def __init__(self, root: Path, enabled: bool = True) -> None:
        self._root = root.resolve()
        self._enabled = enabled
        self._root.mkdir(parents=True, exist_ok=True)
        self._log_path = self._root / "usage.jsonl"
        self._summary_path = self._root / "usage_summary.json"
        self._lock = RLock()

    def record(self, event: str, metadata: Mapping[str, Any] | None = None) -> None:
        if not self._enabled:
            return
        record = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": dict(metadata or {}),
        }
        line = json.dumps(record)
        with self._lock:
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            self._update_summary(record)

    def snapshot(self) -> MutableMapping[str, Any]:
        return self._read_summary()

    def _read_summary(self) -> MutableMapping[str, Any]:
        if not self._summary_path.exists():
            return {"events": {}}
        try:
            with self._summary_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):  # pragma: no cover - corrupted summary fallback
            return {"events": {}}
        return data

    def _update_summary(self, record: Mapping[str, Any]) -> None:
        summary = self._read_summary()
        events = summary.setdefault("events", {})
        event = record.get("event", "unknown")
        entry = events.setdefault(event, {"count": 0, "last_seen": None})
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last_seen"] = record.get("timestamp")
        summary["updated_at"] = record.get("timestamp")
        with self._summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)


__all__ = ["UsageAnalytics"]

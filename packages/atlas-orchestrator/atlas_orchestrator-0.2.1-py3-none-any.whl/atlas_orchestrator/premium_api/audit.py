"""Audit logging helpers for premium API operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    """Structured event recorded for compliance and investigations."""

    type: str
    payload: dict[str, Any]
    timestamp: datetime = datetime.now(timezone.utc)

    def to_json(self) -> str:
        record = {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            **self.payload,
        }
        return json.dumps(record, separators=(",", ":"))


class AuditLogger:
    """Append-only JSONL audit writer."""

    def __init__(self, destination: Path) -> None:
        self._destination = destination
        destination.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        event = AuditEvent(type=event_type, payload=payload)
        with self._destination.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json())
            handle.write("\n")

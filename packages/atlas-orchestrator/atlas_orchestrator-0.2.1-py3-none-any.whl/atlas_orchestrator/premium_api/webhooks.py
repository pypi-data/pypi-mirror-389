"""Webhook repository and dispatcher for the premium API."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable

import httpx

from .audit import AuditLogger

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookConfig:
    """Stored webhook configuration for a customer."""

    webhook_id: str
    url: str
    secret: str | None
    events: tuple[str, ...]
    active: bool
    updated_at: datetime


class WebhookRepository:
    """SQLite-backed repository for webhook configurations."""

    def __init__(self, path: Path) -> None:
        import sqlite3

        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS webhooks (
                    customer_id TEXT NOT NULL,
                    webhook_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    secret TEXT,
                    events TEXT,
                    active INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (customer_id, webhook_id)
                )
                """
            )
            conn.commit()

    def upsert_many(self, customer_id: str, configs: Iterable[WebhookConfig]) -> None:
        import sqlite3

        with sqlite3.connect(self._path) as conn:
            conn.execute("DELETE FROM webhooks WHERE customer_id = ?", (customer_id,))
            for config in configs:
                conn.execute(
                    """
                    INSERT INTO webhooks (
                        customer_id, webhook_id, url, secret, events, active, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        customer_id,
                        config.webhook_id,
                        config.url,
                        config.secret,
                        json.dumps(list(config.events), separators=(",", ":")),
                        1 if config.active else 0,
                        config.updated_at.isoformat(),
                    ),
                )
            conn.commit()

    def get(self, customer_id: str, webhook_id: str) -> WebhookConfig | None:
        import sqlite3

        with sqlite3.connect(self._path) as conn:
            cursor = conn.execute(
                "SELECT url, secret, events, active, updated_at FROM webhooks WHERE customer_id = ? AND webhook_id = ?",
                (customer_id, webhook_id),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        events = tuple(json.loads(row[2]) if row[2] else [])
        return WebhookConfig(
            webhook_id=webhook_id,
            url=row[0],
            secret=row[1],
            events=events,
            active=bool(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
        )


class WebhookDispatcher:
    """Asynchronously deliver webhook notifications when jobs complete."""

    def __init__(self, *, audit: AuditLogger) -> None:
        self._audit = audit
        self._client = httpx.AsyncClient(timeout=10)
        self._queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
        self._worker: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._worker is None:
                self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        async with self._lock:
            if self._worker is not None:
                await self._queue.put({"type": "shutdown"})
                await self._worker
                self._worker = None
        await self._client.aclose()

    def enqueue(
        self,
        *,
        url: str,
        secret: str | None,
        payload: dict[str, object],
    ) -> None:
        if self._worker is None:
            raise RuntimeError(
                "WebhookDispatcher has not been started; call 'await dispatcher.start()' before enqueueing payloads."
            )
        entry = {
            "type": "delivery",
            "url": url,
            "secret": secret,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._queue.put_nowait(entry)

    async def _run(self) -> None:
        while True:
            message = await self._queue.get()
            if message.get("type") == "shutdown":
                break
            await self._deliver(message)

    async def _deliver(self, message: dict[str, object]) -> None:
        url = message["url"]  # type: ignore[index]
        secret = message.get("secret")
        payload = message["payload"]  # type: ignore[index]
        timestamp = datetime.now(timezone.utc).isoformat()
        body = json.dumps(payload, separators=(",", ":"))
        headers = {"Content-Type": "application/json", "X-AO-Timestamp": timestamp}
        if secret:
            signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), sha256).hexdigest()
            headers["X-AO-Signature"] = signature
        try:
            response = await self._client.post(url, content=body, headers=headers)
            response.raise_for_status()
            self._audit.record("webhook.delivered", {"url": url, "status": response.status_code})
        except Exception as exc:  # pragma: no cover - network failure path
            LOGGER.warning("Webhook delivery failed", exc_info=exc)
            self._audit.record(
                "webhook.failed",
                {"url": url, "error": exc.__class__.__name__, "message": str(exc)},
            )

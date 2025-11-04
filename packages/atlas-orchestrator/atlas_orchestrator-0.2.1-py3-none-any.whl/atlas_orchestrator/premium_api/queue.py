"""Async job queue abstractions."""

from __future__ import annotations

import asyncio
from typing import Protocol

from .models import QueueJob


class JobQueue(Protocol):
    """Protocol for enqueuing and consuming jobs."""

    async def enqueue(self, job: QueueJob) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def dequeue(self, *, timeout: float | None = None) -> QueueJob:  # pragma: no cover
        raise NotImplementedError


class InMemoryJobQueue(JobQueue):
    """Lightweight asyncio.Queue-backed implementation for development and tests."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[QueueJob] = asyncio.Queue()

    async def enqueue(self, job: QueueJob) -> None:
        await self._queue.put(job)

    async def dequeue(self, *, timeout: float | None = None) -> QueueJob:
        if timeout is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=timeout)

    def qsize(self) -> int:
        return self._queue.qsize()

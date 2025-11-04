"""Tests for the premium API job worker orchestration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from atlas_orchestrator.premium_api.models import (
    CustomerContext,
    JobRequestPayload,
    JobStatus,
    QueueJob,
    RateLimitSettings,
)
from atlas_orchestrator.premium_api.queue import InMemoryJobQueue
from atlas_orchestrator.premium_api.worker import JobWorker


def _queue_job(job_id: UUID | None = None) -> QueueJob:
    payload = JobRequestPayload(
        model="openrouter/gpt-5",
        messages=[{"role": "user", "content": "hello"}],
    )
    return QueueJob(
        job_id=job_id or uuid4(),
        customer_id="customer-1",
        payload=payload,
        submitted_at=datetime.now(timezone.utc),
        customer_context=CustomerContext(
            key_id="key-1",
            customer_id="customer-1",
            plan_tier="pro",
            rate_limit=RateLimitSettings(per_minute=10, burst=20),
        ),
    )


class StubJobService:
    def __init__(self) -> None:
        self.marked: list[UUID] = []
        self.completed: list[dict[str, Any]] = []

    def mark_running(self, job_id: UUID) -> None:
        self.marked.append(job_id)

    def complete(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        result: dict | None,
        usage: dict | None,
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        self.completed.append(
            {
                "job_id": job_id,
                "status": status,
                "result": result,
                "usage": usage,
                "error_code": error_code,
                "error_message": error_message,
            }
        )


class StubProvider:
    def __init__(self) -> None:
        self.called_with: list[QueueJob] = []
        self.completed = asyncio.Event()

    async def complete(self, job: QueueJob) -> tuple[dict, dict]:
        self.called_with.append(job)
        self.completed.set()
        return {"ok": True}, {"tokens": 42}


def test_job_worker_processes_job_queue() -> None:
    async def run() -> None:
        queue = InMemoryJobQueue()
        job_service = StubJobService()
        provider = StubProvider()
        worker = JobWorker(
            queue=queue,
            job_service=job_service,
            provider=provider,
            poll_timeout=0.01,
        )

        job = _queue_job()
        await queue.enqueue(job)

        await worker.start()
        await asyncio.wait_for(provider.completed.wait(), timeout=1)
        await worker.stop()

        assert job_service.marked == [job.job_id]
        assert provider.called_with[0].job_id == job.job_id
        assert job_service.completed[0]["status"] is JobStatus.succeeded
        assert job_service.completed[0]["result"] == {"ok": True}
        assert job_service.completed[0]["usage"] == {"tokens": 42}

    asyncio.run(run())


def test_job_worker_stop_without_start() -> None:
    async def run() -> None:
        queue = InMemoryJobQueue()
        worker = JobWorker(
            queue=queue,
            job_service=StubJobService(),
            provider=StubProvider(),
        )

        # Should no-op when the worker was never started.
        await worker.stop()

    asyncio.run(run())

"""Asynchronous worker for premium API jobs."""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from . import observability
from .models import JobStatus, QueueJob
from .queue import JobQueue
from .services import JobService


class CompletionProvider(Protocol):
    """Provider responsible for executing queued jobs."""

    async def complete(self, job: QueueJob) -> tuple[dict, dict]:  # pragma: no cover - interface
        raise NotImplementedError


class JobWorker:
    """Background consumer that pulls jobs from the queue and executes them."""

    def __init__(
        self,
        *,
        queue: JobQueue,
        job_service: JobService,
        provider: CompletionProvider,
        poll_timeout: float = 0.5,
    ) -> None:
        self._queue = queue
        self._job_service = job_service
        self._provider = provider
        self._poll_timeout = poll_timeout
        self._task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()
        self._logger = logging.getLogger("atlas_orchestrator.premium_api.worker")

    async def start(self) -> None:
        if self._task is not None:
            return
        self._shutdown.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._shutdown.set()
        await self._task
        self._task = None

    async def _run(self) -> None:
        try:
            while not self._shutdown.is_set():
                try:
                    job = await self._queue.dequeue(timeout=self._poll_timeout)
                except asyncio.TimeoutError:
                    observability.record_queue_depth(self._queue_size())
                    continue
                observability.record_queue_depth(self._queue_size())
                self._job_service.mark_running(job.job_id)
                with observability.start_span(
                    "premium_api.worker.process_job", {"job_id": str(job.job_id), "customer": job.customer_id}
                ):
                    try:
                        result, usage = await self._provider.complete(job)
                    except Exception as exc:  # pragma: no cover - worker failure path
                        self._job_service.complete(
                            job.job_id,
                            status=JobStatus.failed,
                            result=None,
                            usage=None,
                            error_code="worker_error",
                            error_message=str(exc),
                        )
                        self._logger.error(
                            "premium_api_worker_failure",
                            extra={
                                "event": "premium_api.worker.failure",
                                "job_id": str(job.job_id),
                                "customer_id": job.customer_id,
                                "error": str(exc),
                            },
                        )
                        observability.record_queue_depth(self._queue_size())
                        continue
                    self._job_service.complete(
                        job.job_id,
                        status=JobStatus.succeeded,
                        result=result,
                        usage=usage,
                        error_code=None,
                        error_message=None,
                    )
                    self._logger.info(
                        "premium_api_worker_job_succeeded",
                        extra={
                            "event": "premium_api.worker.succeeded",
                            "job_id": str(job.job_id),
                            "customer_id": job.customer_id,
                        },
                    )
                observability.record_queue_depth(self._queue_size())
        except asyncio.CancelledError:  # pragma: no cover - cancellation path
            pass
        finally:
            self._shutdown.clear()

    def _queue_size(self) -> int | None:
        size_getter = getattr(self._queue, "qsize", None)
        if callable(size_getter):
            try:
                return int(size_getter())
            except Exception:  # pragma: no cover - defensive path
                return None
        return None

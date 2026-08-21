"""Background worker: polls the persistent SQLite job queue.

Run standalone:  python -m app.workers.worker
Or embedded in the API process (RUN_WORKER_IN_APP=true).
"""
from __future__ import annotations

import asyncio
import contextlib

import structlog

from app.core.config import settings
from app.core.logging import configure_logging, job_id_var
from app.db.database import SessionLocal
from app.db.repositories.job_repository import JobRepository
from app.workers.job_runner import JobRunner

logger = structlog.get_logger(__name__)

_claim_lock = asyncio.Lock()


async def poll_and_execute_once() -> bool:
    """Claim and run at most one job. Returns True if a job was executed."""
    if _claim_lock.locked():
        return False
    async with _claim_lock:
        db = SessionLocal()
        try:
            job = JobRepository(db).claim_next_pending()
            if job is None:
                return False
            job_id_var.set(job.id)
            logger.info("worker.claimed_job", job_id=job.id, attempt=job.attempt)
            db.commit()
            runner = JobRunner(db)
            status = await runner.execute(job)
            logger.info("worker.job_finished", job_id=job.id, status=status)
            return True
        finally:
            job_id_var.set("-")
            db.close()


async def worker_loop(shutdown: asyncio.Event | None = None) -> None:
    configure_logging()
    logger.info("worker.started", poll_interval=settings.worker_poll_interval_seconds)
    while not (shutdown and shutdown.is_set()):
        executed = await poll_and_execute_once()
        if not executed:
            with contextlib.suppress(asyncio.TimeoutError):
                if shutdown is not None:
                    await asyncio.wait_for(shutdown.wait(), timeout=settings.worker_poll_interval_seconds)
                else:
                    await asyncio.sleep(settings.worker_poll_interval_seconds)


def main() -> None:
    """Standalone worker entrypoint."""
    configure_logging()

    async def _run() -> None:
        await worker_loop()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

"""Job runner: executes a claimed job with error handling."""
from __future__ import annotations

import traceback

import structlog
from datetime import datetime

from app.core.constants import JobStatus
from app.db.models import ResearchJob
from app.db.repositories.job_repository import JobRepository
from app.workers.tasks.discovery_pipeline import DiscoveryPipeline

logger = structlog.get_logger(__name__)


class JobRunner:
    def __init__(self, db) -> None:  # type: ignore[no-untyped-def]
        self.db = db
        self.job_repo = JobRepository(db)

    async def execute(self, job: ResearchJob) -> str:
        """Run one job to a terminal or paused state. Returns final status."""
        self.job_repo.add_event(job.id, "job_started", f"Attempt {job.attempt}")
        try:
            if job.job_type == "discovery":
                pipeline = DiscoveryPipeline(self.db, job)
                status = await pipeline.run()
                return status
            raise ValueError(f"Unknown job type: {job.job_type}")
        except Exception as exc:
            logger.error(
                "job.failed",
                job_id=job.id,
                error=str(exc)[:300],
                trace=traceback.format_exc()[-800:],
            )
            job.status = JobStatus.FAILED.value
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.utcnow()
            self.job_repo.add_event(job.id, "job_failed", str(exc)[:500])
            self.db.commit()
            return JobStatus.FAILED.value

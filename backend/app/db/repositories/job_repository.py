"""Job repository — persistent queue operations."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.core.constants import JobStatus
from app.db.models import JobEvent, ResearchJob
from app.db.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository[ResearchJob]):
    model = ResearchJob

    def create_job(
        self,
        *,
        workspace_id: str,
        user_id: str,
        job_type: str,
        config: dict,
        total_steps: int,
    ) -> ResearchJob:
        return self.add(
            ResearchJob(
                workspace_id=workspace_id,
                user_id=user_id,
                job_type=job_type,
                config=config,
                total_steps=total_steps,
                status=JobStatus.PENDING.value,
            )
        )

    def claim_next_pending(self) -> ResearchJob | None:
        """Atomically claim the oldest pending job (single-worker MVP)."""
        job = self.db.scalar(
            select(ResearchJob)
            .where(ResearchJob.status == JobStatus.PENDING.value)
            .order_by(ResearchJob.created_at)
            .limit(1)
        )
        if job is None:
            return None
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        job.attempt += 1
        self.db.flush()
        return job

    def add_event(self, job_id: str, event_type: str, message: str | None = None, data: dict | None = None) -> None:
        self.db.add(JobEvent(job_id=job_id, event_type=event_type, message=message, data=data))
        self.db.flush()

    def events_for(self, job_id: str) -> list[JobEvent]:
        return list(
            self.db.scalars(select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at))
        )

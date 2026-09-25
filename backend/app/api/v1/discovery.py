"""Discovery job endpoints: create, monitor, pause/resume/cancel/retry."""
from __future__ import annotations

import asyncio
import re

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.constants import DISCOVERY_STEPS, JobStatus
from app.core.exceptions import JobControlError, NotFoundError
from app.db.database import SessionLocal, get_db
from app.db.models import ResearchJob, User, Workspace
from app.db.repositories.job_repository import JobRepository
from app.schemas.discovery import DiscoveryJobCreate, JobEventOut, JobOut
from app.schemas.paper_draft import PaperDraftOut

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/jobs", response_model=JobOut, status_code=201)
def create_job(
    payload: DiscoveryJobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchJob:
    ws = db.get(Workspace, payload.workspace_id)
    if ws is None or ws.user_id != user.id:
        from app.core.exceptions import AuthorizationError, NotFoundError

        if ws is None:
            raise NotFoundError("Workspace not found")
        raise AuthorizationError("No access to this workspace")
    repo = JobRepository(db)
    job = repo.create_job(
        workspace_id=ws.id,
        user_id=user.id,
        job_type="discovery",
        config=payload.model_dump(mode="json"),
        total_steps=len(DISCOVERY_STEPS),
    )
    db.commit()
    return job


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchJob:
    job = _owned_job(db, job_id, user)
    return job


@router.get("/jobs/{job_id}/events", response_model=list[JobEventOut])
def get_job_events(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobEventOut]:
    job = _owned_job(db, job_id, user)
    return [JobEventOut.model_validate(e) for e in JobRepository(db).events_for(job.id)]


@router.get("/workspaces/{workspace_id}/jobs", response_model=list[JobOut])
def list_jobs(
    workspace_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[ResearchJob]:
    from sqlalchemy import select

    return list(
        db.scalars(
            select(ResearchJob)
            .where(ResearchJob.workspace_id == ws.id)
            .order_by(ResearchJob.created_at.desc())
            .limit(50)
        )
    )


def _owned_job(db: Session, job_id: str, user: User) -> ResearchJob:
    job = db.get(ResearchJob, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    ws = db.get(Workspace, job.workspace_id)
    if ws is None or ws.user_id != user.id:
        raise NotFoundError("Job not found")  # do not leak existence
    return job


def _control(db: Session, job_id: str, user: User, action: str) -> ResearchJob:
    job = _owned_job(db, job_id, user)
    if action == "pause":
        if job.status != JobStatus.RUNNING.value:
            raise JobControlError("Only running jobs can be paused")
        job.pause_requested = True
    elif action == "resume":
        if job.status != JobStatus.PAUSED.value:
            raise JobControlError("Only paused jobs can be resumed")
        job.status = JobStatus.PENDING.value
    elif action == "cancel":
        if job.status in (JobStatus.COMPLETED.value, JobStatus.CANCELLED.value):
            raise JobControlError("Job already finished")
        job.cancel_requested = True
        if job.status == JobStatus.PAUSED.value:
            job.status = JobStatus.CANCELLED.value
    elif action == "retry":
        if job.status not in (JobStatus.FAILED.value, JobStatus.CANCELLED.value):
            raise JobControlError("Only failed or cancelled jobs can be retried")
        job.status = JobStatus.PENDING.value
        job.error_message = None
        job.progress = 0.0
        job.pause_requested = False
        job.cancel_requested = False
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/pause", response_model=JobOut)
def pause_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResearchJob:
    return _control(db, job_id, user, "pause")


@router.post("/jobs/{job_id}/resume", response_model=JobOut)
def resume_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResearchJob:
    return _control(db, job_id, user, "resume")


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResearchJob:
    return _control(db, job_id, user, "cancel")


@router.post("/jobs/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResearchJob:
    return _control(db, job_id, user, "retry")


@router.get("/jobs/{job_id}/paper-draft", response_model=PaperDraftOut)
def get_paper_draft(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDraftOut:
    """Retrieve the stored paper draft for a discovery job (404 if none)."""
    from app.services.paper_draft_service import PaperDraftService

    job = _owned_job(db, job_id, user)
    return PaperDraftService(db).get_draft(job)


@router.post("/jobs/{job_id}/paper-draft", response_model=PaperDraftOut, status_code=201)
async def generate_paper_draft(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperDraftOut:
    """Generate (or regenerate) the paper draft for a completed discovery job."""
    from app.services.paper_draft_service import PaperDraftService

    job = _owned_job(db, job_id, user)
    out = await PaperDraftService(db).generate_for_job(job)
    db.commit()
    return out


@router.get("/jobs/{job_id}/paper-draft/export")
def export_paper_draft(
    job_id: str,
    format: str = "markdown",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export a stored paper draft as Markdown or PDF (defensive; no fabrication)."""
    from app.services.paper_draft_service import PaperDraftService

    job = _owned_job(db, job_id, user)
    svc = PaperDraftService(db)
    out = svc.get_draft(job)

    if format not in ("markdown", "pdf"):
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("format must be one of: markdown, pdf")

    slug = re.sub(r"[^\w\- ]", "", out.title).strip().replace(" ", "_")[:60] or "paper_draft"
    workspace_name = db.get(Workspace, job.workspace_id).name if job.workspace_id else "workspace"
    md = svc.render_markdown(out, workspace_name or "workspace")

    if format == "pdf":
        from app.core.exceptions import NotImplementedAppError

        try:
            pdf = svc.render_pdf(md)
        except Exception as exc:  # pragma: no cover - backend import/layout issues
            raise NotImplementedAppError(f"PDF rendering is unavailable: {str(exc)[:120]}") from exc
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{slug}.pdf"'},
        )
    return Response(
        content=md + "\n",
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{slug}.md"'},
    )

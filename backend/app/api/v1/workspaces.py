"""Workspace endpoints + dashboard stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.constants import JobStatus
from app.db.database import get_db
from app.db.models import (
    CollaborationCandidate,
    Evidence,
    Hypothesis,
    Paper,
    PaperAuthor,
    ResearchGap,
    ResearchIntersection,
    ResearchJob,
    User,
    Workspace,
)
from app.schemas.misc import WorkspaceStats
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    ws = Workspace(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        discovery_mode=payload.discovery_mode,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Workspace]:
    return list(
        db.scalars(select(Workspace).where(Workspace.user_id == user.id).order_by(Workspace.created_at))
    )


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(
    ws: Workspace = Depends(get_owned_workspace),
) -> Workspace:
    return ws


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def update_workspace(
    payload: WorkspaceUpdate,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Workspace:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ws, field, value)
    db.commit()
    db.refresh(ws)
    return ws


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> None:
    db.delete(ws)
    db.commit()


@router.get("/{workspace_id}/export", status_code=200)
def export_workspace_data(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    """Privacy: full workspace data export as JSON."""
    from app.services.report_service import ReportService

    data = ReportService(db)._collect(ws.id)  # noqa: SLF001 - intentional reuse

    def ser(obj):  # type: ignore[no-untyped-def]
        if hasattr(obj, "__dict__"):
            return {
                k: v.isoformat() if isinstance(v, type(__import__("datetime").datetime.now())) else v
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        return str(obj)

    return {
        "workspace": {"id": ws.id, "name": ws.name, "description": ws.description},
        "intersections": [ser(i) for i in data["intersections"]],
        "gaps": [ser(g) for g in data["gaps"]],
        "hypotheses": [ser(h) for h in data["hypotheses"]],
        "collaborations": [ser(c) for c in data["collaborations"]],
        "evidence": [ser(e) for e in data["evidence"]],
        "trajectories": [ser(t) for t in data["trajectories"]],
    }


@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
def workspace_stats(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> WorkspaceStats:
    wid = ws.id
    papers_analyzed = (
        db.scalar(
            select(func.count(func.distinct(PaperAuthor.paper_id))).where(
                PaperAuthor.researcher_id.isnot(None)
            )
        )
        or 0
    )
    researchers_analyzed = (
        db.scalar(
            select(func.count(func.distinct(ResearchIntersection.researcher_a_id))).where(
                ResearchIntersection.workspace_id == wid
            )
        )
        or 0
    ) + (
        db.scalar(
            select(func.count(func.distinct(ResearchIntersection.researcher_b_id))).where(
                ResearchIntersection.workspace_id == wid
            )
        )
        or 0
    )
    gaps = db.scalar(select(func.count()).select_from(ResearchGap).where(ResearchGap.workspace_id == wid)) or 0
    intersections = (
        db.scalar(
            select(func.count()).select_from(ResearchIntersection).where(ResearchIntersection.workspace_id == wid)
        )
        or 0
    )
    hypotheses = (
        db.scalar(select(func.count()).select_from(Hypothesis).where(Hypothesis.workspace_id == wid)) or 0
    )
    collabs = (
        db.scalar(
            select(func.count())
            .select_from(CollaborationCandidate)
            .where(CollaborationCandidate.workspace_id == wid)
        )
        or 0
    )
    avg_conf = (
        db.scalar(
            select(func.avg(Evidence.confidence)).where(Evidence.workspace_id == wid)
        )
    )
    active_jobs = (
        db.scalar(
            select(func.count())
            .select_from(ResearchJob)
            .where(
                ResearchJob.workspace_id == wid,
                ResearchJob.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.PAUSED.value]),
            )
        )
        or 0
    )

    # topic distribution (top topics across linked papers)
    from app.db.models import PaperTopic, Topic

    topic_rows = (
        db.execute(
            select(Topic.name, func.count(PaperTopic.paper_id))
            .join(PaperTopic, PaperTopic.topic_id == Topic.id)
            .group_by(Topic.name)
            .order_by(func.count(PaperTopic.paper_id).desc())
            .limit(8)
        )
        .all()
    )
    from app.db.models import Method, PaperMethod

    method_rows = (
        db.execute(
            select(Method.name, func.count(PaperMethod.paper_id))
            .join(PaperMethod, PaperMethod.method_id == Method.id)
            .group_by(Method.name)
            .order_by(func.count(PaperMethod.paper_id).desc())
            .limit(8)
        )
        .all()
    )
    timeline_rows = (
        db.execute(
            select(Paper.publication_year, func.count(Paper.id))
            .group_by(Paper.publication_year)
            .order_by(Paper.publication_year)
        )
        .all()
    )
    ix_rows = (
        db.execute(
            select(ResearchIntersection.title, ResearchIntersection.novelty_confidence * 100)
            .where(ResearchIntersection.workspace_id == wid)
            .limit(10)
        )
        .all()
    )

    return WorkspaceStats(
        papers_analyzed=int(papers_analyzed),
        researchers_analyzed=int(researchers_analyzed),
        gaps=int(gaps),
        intersections=int(intersections),
        hypotheses=int(hypotheses),
        collaboration_opportunities=int(collabs),
        avg_confidence=round(float(avg_conf or 0), 3),
        active_jobs=int(active_jobs),
        topics=[{"name": n, "count": c} for n, c in topic_rows],
        methods=[{"name": n, "count": c} for n, c in method_rows],
        timeline=[{"year": int(y) if y else None, "count": c} for y, c in timeline_rows if y],
        domains=[{"name": n, "count": c} for n, c in topic_rows[:5]],
        opportunity_scores=[{"name": t[:40], "score": round(float(s), 1)} for t, s in ix_rows],
    )

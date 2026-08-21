"""Result endpoints: intersections, gaps, hypotheses, collaborations, evidence."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import (
    CollaborationCandidate,
    Evidence,
    Experiment,
    Hypothesis,
    ResearchGap,
    ResearchIntersection,
    Researcher,
    User,
    Workspace,
)
from app.schemas.domain import (
    CollaborationOut,
    EvidenceOut,
    ExperimentOut,
    GapDetailOut,
    GapOut,
    HypothesisDetailOut,
    HypothesisOut,
    IntersectionDetailOut,
    IntersectionOut,
)

router = APIRouter(tags=["results"])


# -- Intersections ---------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/intersections", response_model=list[IntersectionOut])
def list_intersections(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
    mode: str | None = Query(default=None),
) -> list[ResearchIntersection]:
    stmt = select(ResearchIntersection).where(ResearchIntersection.workspace_id == ws.id)
    if mode:
        stmt = stmt.where(ResearchIntersection.discovery_mode == mode)
    return list(db.scalars(stmt.order_by(ResearchIntersection.created_at.desc())))


def _load_intersection(db: Session, ws: Workspace, intersection_id: str) -> ResearchIntersection:
    ix = db.get(ResearchIntersection, intersection_id)
    if ix is None or ix.workspace_id != ws.id:
        raise NotFoundError("Intersection not found")
    return ix


@router.get("/workspaces/{workspace_id}/intersections/{intersection_id}", response_model=IntersectionDetailOut)
def get_intersection(
    intersection_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    ix = _load_intersection(db, ws, intersection_id)
    evidence_ids = select_evidence_ids(db, "intersection", ix.id)
    evidence = list(db.scalars(select(Evidence).where(Evidence.id.in_(evidence_ids or [""]))))
    ra = db.get(Researcher, ix.researcher_a_id)
    rb = db.get(Researcher, ix.researcher_b_id)
    hyps = list(
        db.scalars(select(Hypothesis).where(Hypothesis.intersection_id == ix.id))
    )
    detail = IntersectionDetailOut(
        **IntersectionOut.model_validate(ix).model_dump(),
        researcher_a={"id": ra.id, "name": ra.name, "affiliation": ra.affiliation} if ra else None,
        researcher_b={"id": rb.id, "name": rb.name, "affiliation": rb.affiliation} if rb else None,
        evidence=[EvidenceOut.model_validate(e) for e in evidence],
        hypotheses=[HypothesisOut.model_validate(h) for h in hyps],
    )
    return detail.model_dump()


# -- Gaps --------------------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/gaps", response_model=list[GapOut])
def list_gaps(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[ResearchGap]:
    return list(
        db.scalars(
            select(ResearchGap)
            .where(ResearchGap.workspace_id == ws.id)
            .order_by(ResearchGap.confidence.desc())
        )
    )


@router.get("/workspaces/{workspace_id}/gaps/{gap_id}", response_model=GapDetailOut)
def get_gap(
    gap_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    gap = db.get(ResearchGap, gap_id)
    if gap is None or gap.workspace_id != ws.id:
        raise NotFoundError("Gap not found")
    evidence_ids = select_evidence_ids(db, "gap", gap.id)
    evidence = list(db.scalars(select(Evidence).where(Evidence.id.in_(evidence_ids or [""]))))
    return {
        **GapOut.model_validate(gap).model_dump(),
        "evidence": [EvidenceOut.model_validate(e).model_dump() for e in evidence],
    }


# -- Hypotheses ----------------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/hypotheses", response_model=list[HypothesisOut])
def list_hypotheses(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[Hypothesis]:
    return list(
        db.scalars(select(Hypothesis).where(Hypothesis.workspace_id == ws.id))
    )


@router.get("/workspaces/{workspace_id}/hypotheses/{hypothesis_id}", response_model=HypothesisDetailOut)
def get_hypothesis(
    hypothesis_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    hyp = db.get(Hypothesis, hypothesis_id)
    if hyp is None or hyp.workspace_id != ws.id:
        raise NotFoundError("Hypothesis not found")
    exp = db.scalar(select(Experiment).where(Experiment.hypothesis_id == hyp.id))
    ix = db.get(ResearchIntersection, hyp.intersection_id)
    evidence_ids = []
    if ix is not None:
        evidence_ids = select_evidence_ids(db, "intersection", ix.id)
    evidence = list(db.scalars(select(Evidence).where(Evidence.id.in_(evidence_ids or [""]))))
    return {
        **HypothesisOut.model_validate(hyp).model_dump(),
        "experiment": ExperimentOut.model_validate(exp).model_dump() if exp else None,
        "intersection": IntersectionOut.model_validate(ix).model_dump() if ix else None,
        "evidence": [EvidenceOut.model_validate(e).model_dump() for e in evidence],
    }


# -- Collaborations ---------------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/collaborations", response_model=list[CollaborationOut])
def list_collaborations(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[CollaborationCandidate]:
    return list(
        db.scalars(
            select(CollaborationCandidate)
            .where(CollaborationCandidate.workspace_id == ws.id)
            .order_by(CollaborationCandidate.score.desc())
        )
    )


# -- Evidence ------------------------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Evidence]:
    stmt = select(Evidence).where(Evidence.workspace_id == ws.id)
    if status:
        stmt = stmt.where(Evidence.status == status)
    return list(db.scalars(stmt.order_by(Evidence.created_at.desc()).limit(limit)))


@router.get("/evidence/{evidence_id}", response_model=EvidenceOut)
def get_evidence(
    evidence_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Evidence:
    ev = db.get(Evidence, evidence_id)
    if ev is None:
        raise NotFoundError("Evidence not found")
    ws = db.get(Workspace, ev.workspace_id)
    if ws is None or ws.user_id != user.id:
        raise NotFoundError("Evidence not found")
    return ev


def select_evidence_ids(db: Session, kind: str, entity_id: str) -> list[str]:  # type: ignore[no-untyped-def]
    from app.db.models import IntersectionEvidence, ResearchGapEvidence

    if kind == "intersection":
        rows = db.scalars(
            select(IntersectionEvidence.evidence_id).where(
                IntersectionEvidence.intersection_id == entity_id
            )
        )
    else:
        rows = db.scalars(
            select(ResearchGapEvidence.evidence_id).where(ResearchGapEvidence.gap_id == entity_id)
        )
    return list(rows)

"""Intersection endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_owned_workspace
from app.api.v1.result_helpers import load_evidence, load_intersection, select_evidence_ids
from app.db.database import get_db
from app.db.models import Hypothesis, ResearchIntersection, Researcher, Workspace
from app.schemas.domain import (
    EvidenceOut,
    HypothesisOut,
    IntersectionDetailOut,
    IntersectionOut,
)

router = APIRouter(tags=["intersections"])


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


@router.get(
    "/workspaces/{workspace_id}/intersections/{intersection_id}",
    response_model=IntersectionDetailOut,
)
def get_intersection(
    intersection_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    ix = load_intersection(db, ws, intersection_id)
    evidence = load_evidence(db, select_evidence_ids(db, "intersection", ix.id))
    ra = db.get(Researcher, ix.researcher_a_id)
    rb = db.get(Researcher, ix.researcher_b_id)
    hyps = list(db.scalars(select(Hypothesis).where(Hypothesis.intersection_id == ix.id)))
    detail = IntersectionDetailOut(
        **IntersectionOut.model_validate(ix).model_dump(),
        researcher_a={"id": ra.id, "name": ra.name, "affiliation": ra.affiliation} if ra else None,
        researcher_b={"id": rb.id, "name": rb.name, "affiliation": rb.affiliation} if rb else None,
        evidence=[EvidenceOut.model_validate(e) for e in evidence],
        hypotheses=[HypothesisOut.model_validate(h) for h in hyps],
    )
    return detail.model_dump()

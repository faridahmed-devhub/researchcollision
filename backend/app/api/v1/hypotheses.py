"""Hypothesis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_owned_workspace
from app.api.v1.result_helpers import load_evidence, select_evidence_ids
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import Experiment, Hypothesis, ResearchIntersection, Workspace
from app.schemas.domain import (
    EvidenceOut,
    ExperimentOut,
    HypothesisDetailOut,
    HypothesisOut,
    IntersectionOut,
)

router = APIRouter(tags=["hypotheses"])


@router.get("/workspaces/{workspace_id}/hypotheses", response_model=list[HypothesisOut])
def list_hypotheses(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[Hypothesis]:
    return list(db.scalars(select(Hypothesis).where(Hypothesis.workspace_id == ws.id)))


@router.get(
    "/workspaces/{workspace_id}/hypotheses/{hypothesis_id}",
    response_model=HypothesisDetailOut,
)
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
    evidence_ids = (
        select_evidence_ids(db, "intersection", ix.id) if ix is not None else []
    )
    evidence = load_evidence(db, evidence_ids)
    return {
        **HypothesisOut.model_validate(hyp).model_dump(),
        "experiment": ExperimentOut.model_validate(exp).model_dump() if exp else None,
        "intersection": IntersectionOut.model_validate(ix).model_dump() if ix else None,
        "evidence": [EvidenceOut.model_validate(e).model_dump() for e in evidence],
    }

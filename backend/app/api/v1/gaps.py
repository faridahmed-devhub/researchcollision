"""Gap endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_owned_workspace
from app.api.v1.result_helpers import load_evidence, select_evidence_ids
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import ResearchGap, Workspace
from app.schemas.domain import EvidenceOut, GapDetailOut, GapOut

router = APIRouter(tags=["gaps"])


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
    evidence = load_evidence(db, select_evidence_ids(db, "gap", gap.id))
    detail = GapDetailOut(
        **GapOut.model_validate(gap).model_dump(),
        evidence=[EvidenceOut.model_validate(e) for e in evidence],
    )
    return detail.model_dump()

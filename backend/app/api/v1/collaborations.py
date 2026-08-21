"""Collaboration candidate endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_owned_workspace
from app.db.database import get_db
from app.db.models import CollaborationCandidate, Workspace
from app.schemas.domain import CollaborationOut

router = APIRouter(tags=["collaborations"])


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

"""Evidence endpoints (Evidence Explorer)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import Evidence, User, Workspace
from app.schemas.domain import EvidenceOut

router = APIRouter(tags=["evidence"])


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
        raise NotFoundError("Evidence not found")  # do not leak existence
    return ev

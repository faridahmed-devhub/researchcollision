"""Paper endpoints: literature search (with fallback) + local lookup."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.db.database import get_db
from app.db.models import Paper, User, Workspace
from app.db.repositories.paper_repository import PaperRepository
from app.schemas.misc import PaperOut
from app.services.literature_service import LiteratureService
from app.services.paper_service import PaperService

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search", response_model=list[PaperOut])
async def search_papers(
    q: str = Query(min_length=1, max_length=300),
    workspace_id: str = Query(...),
    limit: int = Query(default=10, ge=1, le=50),
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Paper]:
    ws = db.get(Workspace, workspace_id)
    if ws is None or ws.user_id != user.id:
        from app.core.exceptions import AuthorizationError, NotFoundError

        if ws is None:
            raise NotFoundError("Workspace not found")
        raise AuthorizationError("No access to this workspace")
    service = LiteratureService()
    papers_meta, _provider = await service.search(q, limit=limit, refresh=refresh)
    paper_service = PaperService(db)
    out: list[Paper] = []
    for meta in papers_meta:
        paper, _created = paper_service.upsert_from_metadata(meta)
        out.append(paper)
    db.commit()
    return out


@router.get("/local", response_model=list[PaperOut])
def search_local_papers(
    q: str = Query(default="", max_length=300),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Paper]:
    repo = PaperRepository(db)
    if q.strip():
        return repo.search_local(q, limit=limit)
    return list(db.query(Paper).order_by(Paper.created_at.desc()).limit(limit))


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(
    paper_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    paper = db.get(Paper, paper_id)
    if paper is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Paper not found")
    return paper

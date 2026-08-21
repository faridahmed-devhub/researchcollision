"""Researcher endpoints: search (shared + workspace) and create."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.db.database import get_db
from app.db.models import Researcher, ResearcherAlias, User, Workspace
from app.db.repositories.researcher_repository import ResearcherRepository
from app.schemas.researcher import ResearcherCreate, ResearcherOut

router = APIRouter(prefix="/researchers", tags=["researchers"])


@router.get("/search", response_model=list[ResearcherOut])
def search_researchers(
    q: str = Query(min_length=1, max_length=200),
    workspace_id: str = Query(...),
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Researcher]:
    ws = db.get(Workspace, workspace_id)
    if ws is None or ws.user_id != user.id:
        from app.core.exceptions import AuthorizationError, NotFoundError

        if ws is None:
            raise NotFoundError("Workspace not found")
        raise AuthorizationError("No access to this workspace")
    return ResearcherRepository(db).search(q, workspace_id=ws.id, limit=limit)


@router.post("", response_model=ResearcherOut, status_code=201)
def create_researcher(
    payload: ResearcherCreate,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Researcher:
    repo = ResearcherRepository(db)
    existing = repo.find_by_name(payload.name, ws.id)
    if existing:
        return existing
    researcher = repo.add(
        Researcher(
            workspace_id=ws.id,
            name=payload.name,
            affiliation=payload.affiliation,
            homepage_url=payload.homepage_url,
            bio=payload.bio,
        )
    )
    for alias in payload.aliases[:10]:
        db.add(ResearcherAlias(researcher_id=researcher.id, alias=alias))
    db.commit()
    db.refresh(researcher)
    return researcher


@router.get("/{researcher_id}", response_model=ResearcherOut)
def get_researcher(
    researcher_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Researcher:
    r = ResearcherRepository(db).get_in_workspace(researcher_id, ws.id)
    if r is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Researcher not found")
    return r

"""Research profile endpoints: manual create, CV upload, DNA editing."""
from __future__ import annotations

import os
import uuid as uuid_mod

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.agents.profile_agent import ProfileAgent
from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.config import settings
from app.core.constants import DocumentType
from app.db.database import get_db
from app.db.models import (
    Document,
    DocumentChunk,
    ResearchProfile,
    ResearchProfileVersion,
    User,
    Workspace,
)
from app.providers.llm.factory import get_llm_provider
from app.schemas.profile import (
    ProfileCreate,
    ProfileDetailOut,
    ProfileOut,
    ProfileUpdate,
    ProfileVersionOut,
)
from app.services.cv_service import CVService
from app.services.paper_service import PaperService
from app.services.vector_service import VectorService

router = APIRouter(prefix="/research-profiles", tags=["research-profiles"])

UPLOAD_DIR = os.path.join("data", "uploads")


def _profile_detail(db: Session, profile: ResearchProfile) -> dict:
    latest = profile.versions[0] if profile.versions else None
    return ProfileDetailOut(
        id=profile.id,
        workspace_id=profile.workspace_id,
        researcher_id=profile.researcher_id,
        name=profile.name,
        source_type=profile.source_type,
        current_version=profile.current_version,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        dna=(latest.dna_json if latest else {}),
        versions=[ProfileVersionOut.model_validate(v) for v in profile.versions],
    )


@router.post("", response_model=ProfileDetailOut, status_code=201)
def create_profile(
    payload: ProfileCreate,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    profile = ResearchProfile(workspace_id=ws.id, name=payload.name, source_type="manual")
    db.add(profile)
    db.flush()
    version = ResearchProfileVersion(profile_id=profile.id, version=1, dna_json=payload.dna)
    db.add(version)
    db.commit()
    db.refresh(profile)
    return _profile_detail(db, profile)


@router.post("/upload", response_model=ProfileDetailOut, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Upload a CV (PDF/DOCX/TXT), extract Research DNA, store profile + version.

    The raw upload is stored on disk (never executed); extracted text goes to DB.
    """
    content = await file.read()
    cv_service = CVService()
    extracted = cv_service.process_upload(filename=file.filename or "cv.txt", content=content)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid_mod.uuid4().hex}_{os.path.basename(file.filename or 'cv.txt')}"[:200]
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as fh:
        fh.write(content)

    # AI extraction of Research DNA
    agent = ProfileAgent(get_llm_provider(), db=db, workspace_id=ws.id)
    dna = await agent.extract_dna(extracted.text)

    display_name = (dna.domains[0] if dna.domains else None) or (file.filename or "Researcher")
    profile = ResearchProfile(
        workspace_id=ws.id,
        name=f"{display_name} — {user.name}",
        source_type="cv",
    )
    db.add(profile)
    db.flush()

    doc = Document(
        workspace_id=ws.id,
        profile_id=profile.id,
        document_type=DocumentType.CV.value,
        filename=safe_name,
        mime_type=extracted.mime_type,
        size_bytes=extracted.size_bytes,
        content_hash=extracted.content_hash,
        extracted_text=extracted.text[:100000],
    )
    db.add(doc)
    db.flush()

    paper_service = PaperService(db)
    for i, chunk in enumerate(paper_service.make_chunks(extracted.text)):
        db.add(DocumentChunk(document_id=doc.id, chunk_index=i, text=chunk, token_count=len(chunk.split())))

    version = ResearchProfileVersion(profile_id=profile.id, version=1, dna_json=dna.model_dump())
    db.add(version)

    # Embed chunks for semantic search over the CV
    vector_service = VectorService(db)
    for i, chunk in enumerate(paper_service.make_chunks(extracted.text)):
        await vector_service.embed_and_store(
            entity_type="document_chunk",
            entity_id=f"{doc.id}:{i}",
            text=chunk,
            workspace_id=ws.id,
        )
    db.commit()
    db.refresh(profile)
    return _profile_detail(db, profile)


@router.get("/{profile_id}", response_model=ProfileDetailOut)
def get_profile(
    profile_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    profile = db.get(ResearchProfile, profile_id)
    if profile is None or profile.workspace_id != ws.id:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Profile not found")
    return _profile_detail(db, profile)


@router.patch("/{profile_id}", response_model=ProfileDetailOut)
def update_profile(
    payload: ProfileUpdate,
    profile_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    from app.core.exceptions import NotFoundError

    profile = db.get(ResearchProfile, profile_id)
    if profile is None or profile.workspace_id != ws.id:
        raise NotFoundError("Profile not found")
    if payload.name:
        profile.name = payload.name
    if payload.dna is not None:
        new_version = profile.current_version + 1
        db.add(
            ResearchProfileVersion(
                profile_id=profile.id, version=new_version, dna_json=payload.dna
            )
        )
        profile.current_version = new_version
    db.commit()
    db.refresh(profile)
    return _profile_detail(db, profile)


@router.delete("/{profile_id}/cv", status_code=204)
def delete_cv(
    profile_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> None:
    """Privacy: delete the uploaded CV document (and its chunks)."""
    from app.core.exceptions import NotFoundError

    profile = db.get(ResearchProfile, profile_id)
    if profile is None or profile.workspace_id != ws.id:
        raise NotFoundError("Profile not found")
    docs = db.query(Document).filter(Document.profile_id == profile.id).all()
    for d in docs:
        path = os.path.join(UPLOAD_DIR, d.filename)
        if os.path.exists(path):
            os.remove(path)
        db.delete(d)
    db.commit()


@router.get("", response_model=list[ProfileOut])
def list_profiles(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[ResearchProfile]:
    return list(
        db.scalars(
            select_profiles(ws.id)
        )
    )


def select_profiles(workspace_id: str):  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    return select(ResearchProfile).where(ResearchProfile.workspace_id == workspace_id)

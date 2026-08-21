"""Shared helpers for result endpoints."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import (
    Evidence,
    IntersectionEvidence,
    ResearchGapEvidence,
    ResearchIntersection,
    Workspace,
)


def select_evidence_ids(db: Session, kind: str, entity_id: str) -> list[str]:
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


def load_evidence(db: Session, ids: list[str]) -> list[Evidence]:
    if not ids:
        return []
    return list(db.scalars(select(Evidence).where(Evidence.id.in_(ids))))


def load_intersection(db: Session, ws: Workspace, intersection_id: str) -> ResearchIntersection:
    ix = db.get(ResearchIntersection, intersection_id)
    if ix is None or ix.workspace_id != ws.id:
        raise NotFoundError("Intersection not found")
    return ix

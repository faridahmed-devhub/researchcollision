"""Collaboration service: persist ranked candidates."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CollaborationCandidate


class CollaborationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        workspace_id: str,
        intersection_id: str | None,
        researcher_a_id: str,
        researcher_b_id: str,
        ranking: dict,
        rationale: str,
    ) -> CollaborationCandidate:
        cand = CollaborationCandidate(
            workspace_id=workspace_id,
            intersection_id=intersection_id,
            researcher_a_id=researcher_a_id,
            researcher_b_id=researcher_b_id,
            score=ranking["score"],
            category=ranking["category"],
            component_scores=ranking["component_scores"],
            rationale=rationale[:2000],
        )
        self.db.add(cand)
        self.db.flush()
        return cand

    def for_workspace(self, workspace_id: str, limit: int = 100) -> list[CollaborationCandidate]:
        return list(
            self.db.scalars(
                select(CollaborationCandidate)
                .where(CollaborationCandidate.workspace_id == workspace_id)
                .order_by(CollaborationCandidate.score.desc())
                .limit(limit)
            )
        )

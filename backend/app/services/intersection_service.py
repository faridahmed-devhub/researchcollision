"""Intersection service: persist intersections + evidence links."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DiscoveryMode
from app.db.models import IntersectionEvidence, ResearchIntersection


class IntersectionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        workspace_id: str,
        job_id: str | None,
        candidate: dict,
        researcher_a_id: str,
        researcher_b_id: str,
        research_gap_id: str | None,
        mode: DiscoveryMode,
    ) -> ResearchIntersection:
        ix = ResearchIntersection(
            workspace_id=workspace_id,
            job_id=job_id,
            title=candidate["title"][:390],
            description=candidate.get("description", ""),
            shared_problem=candidate.get("shared_problem"),
            complementary_expertise=candidate.get("complementary_expertise"),
            research_gap_id=research_gap_id,
            gap_description=candidate.get("research_gap"),
            researcher_a_id=researcher_a_id,
            researcher_b_id=researcher_b_id,
            why_researcher_a=candidate.get("why_researcher_a"),
            why_researcher_b=candidate.get("why_researcher_b"),
            novelty_confidence=float(candidate.get("novelty_confidence", 0.5)),
            feasibility_confidence=float(candidate.get("feasibility_confidence", 0.5)),
            discovery_mode=mode.value if isinstance(mode, DiscoveryMode) else str(mode),
        )
        self.db.add(ix)
        self.db.flush()
        for ev_id in list(dict.fromkeys(candidate.get("evidence_ids", [])))[:12]:
            self.db.add(IntersectionEvidence(intersection_id=ix.id, evidence_id=ev_id))
        self.db.flush()
        return ix

    def evidence_ids_for(self, intersection_id: str) -> list[str]:
        rows = self.db.scalars(
            select(IntersectionEvidence.evidence_id).where(
                IntersectionEvidence.intersection_id == intersection_id
            )
        )
        return list(rows)

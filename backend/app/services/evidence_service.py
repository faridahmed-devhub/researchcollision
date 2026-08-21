"""Evidence service: creation, citation validation, status control."""
from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import EvidenceStatus, SourceType
from app.db.models import Evidence, Paper
from app.agents.verification_agent import VerificationAgent

logger = structlog.get_logger(__name__)


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.verifier = VerificationAgent()

    def create(
        self,
        *,
        workspace_id: str,
        claim: str,
        paper: Paper | None = None,
        evidence_text: str | None = None,
        source_type: str = SourceType.PAPER_ABSTRACT.value,
        source_url: str | None = None,
        source_title: str | None = None,
        confidence: float = 0.5,
        status: str = EvidenceStatus.INFERRED.value,
    ) -> Evidence:
        ev = Evidence(
            workspace_id=workspace_id,
            claim=claim[:2000],
            paper_id=paper.id if paper else None,
            source_title=(source_title or (paper.title if paper else None)),
            source_url=source_url or (paper.source_url if paper else None),
            evidence_text=evidence_text[:2000] if evidence_text else None,
            source_type=source_type,
            confidence=max(0.0, min(1.0, confidence)),
            status=status,
            retrieved_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.db.add(ev)
        self.db.flush()
        return ev

    def for_paper(self, workspace_id: str, paper: Paper, claim: str) -> Evidence:
        """Create abstract-grounded evidence for a paper."""
        snippet = (paper.abstract or "")[:400]
        return self.create(
            workspace_id=workspace_id,
            claim=claim,
            paper=paper,
            evidence_text=snippet,
            confidence=0.6,
        )

    def run_verification(self, workspace_id: str) -> list[dict]:
        """Verify all workspace evidence against stored papers."""
        rows = list(
            self.db.scalars(select(Evidence).where(Evidence.workspace_id == workspace_id))
        )
        paper_ids = {r.paper_id for r in rows if r.paper_id}
        papers_by_id = {}
        if paper_ids:
            papers_by_id = {
                p.id: p
                for p in self.db.scalars(select(Paper).where(Paper.id.in_(paper_ids)))
            }
        updates = self.verifier.verify_evidence(evidence_rows=rows, papers_by_id=papers_by_id)
        by_id = {r.id: r for r in rows}
        applied = []
        for u in updates:
            row = by_id.get(u["evidence_id"])
            if row:
                row.status = u["status"]
                applied.append(u)
        self.db.flush()
        logger.info("evidence.verification_applied", count=len(applied))
        return applied

    def verified_ratio(self, workspace_id: str) -> float:
        rows = list(
            self.db.scalars(select(Evidence.status).where(Evidence.workspace_id == workspace_id))
        )
        if not rows:
            return 0.0
        good = sum(1 for s in rows if s in (EvidenceStatus.VERIFIED.value, EvidenceStatus.INFERRED.value))
        return good / len(rows)

"""Verification Agent — citation validation + evidence status control.

Algorithmic (not LLM-dependent): statuses can only be *downgraded* unless a
stored paper directly supports the claim.
"""
from __future__ import annotations

import re

import structlog

from app.core.constants import EvidenceStatus

logger = structlog.get_logger(__name__)

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


class VerificationAgent:
    name = "verification_agent"

    def validate_doi(self, doi: str | None) -> bool:
        return bool(doi) and bool(_DOI_RE.match(doi))

    def verify_evidence(
        self,
        *,
        evidence_rows: list,
        papers_by_id: dict,
    ) -> list[dict]:
        """Return updates [{evidence_id, status, reason}].

        Rules:
        - Evidence with no paper link -> UNKNOWN.
        - Evidence whose paper is missing -> UNVERIFIED (invalid citation).
        - Evidence text found in the paper abstract -> VERIFIED.
        - Otherwise -> INFERRED (reasonable interpretation of stored abstract).
        """
        updates: list[dict] = []
        for ev in evidence_rows:
            status = ev.status
            reason = ""
            if not ev.paper_id:
                if ev.status == EvidenceStatus.VERIFIED.value:
                    status = EvidenceStatus.UNKNOWN.value
                    reason = "No linked paper; cannot be verified."
            else:
                paper = papers_by_id.get(ev.paper_id)
                if paper is None:
                    status = EvidenceStatus.UNVERIFIED.value
                    reason = "Citation failed validation: paper not found in store."
                else:
                    if paper.is_synthetic:
                        # Synthetic (mock) papers cannot back a VERIFIED claim.
                        if ev.status == EvidenceStatus.VERIFIED.value:
                            status = EvidenceStatus.INFERRED.value
                            reason = "Synthetic paper; cannot be independently verified."
                    else:
                        abstract = (paper.abstract or "").lower()
                        text = (ev.evidence_text or "").lower().strip()
                        if text and len(text) > 20:
                            # fuzzy containment on first 60 chars of the quote
                            probe = " ".join(text[:60].split())
                            if probe and probe in " ".join(abstract.split()):
                                status = EvidenceStatus.VERIFIED.value
                                reason = "Quote matched stored abstract."
                            elif ev.status == EvidenceStatus.VERIFIED.value:
                                status = EvidenceStatus.INFERRED.value
                                reason = "Interpretation of stored abstract; exact quote not found."
            if status != ev.status:
                updates.append({"evidence_id": ev.id, "status": status, "reason": reason})
        logger.info("verification.complete", checked=len(evidence_rows), updated=len(updates))
        return updates

    def validate_citation(
        self, *, cited_title: str | None, cited_doi: str | None, paper
    ) -> tuple[bool, str]:
        """Validate an LLM-provided citation against the stored paper."""
        if paper is None:
            return False, "Paper not found in store."
        if cited_doi and paper.doi and cited_doi.lower() != paper.doi.lower():
            return False, "DOI mismatch."
        if cited_title:
            norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
            if norm(cited_title) != norm(paper.title):
                return False, "Title mismatch."
        return True, "Citation matches stored paper."

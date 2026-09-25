"""Paper Draft service: grounded research-paper draft generation & retrieval.

Stores drafts in the existing report system (``GeneratedReport`` rows with
format="paper_draft"), keyed by job_id so reruns replace only that job's
draft.
"""
from __future__ import annotations

import json
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.paper_writer_agent import PaperWriterAgent
from app.core.constants import PAPER_DRAFT_FORMAT
from app.core.exceptions import NotFoundError
from app.db.models import (
    Evidence,
    GeneratedReport,
    Hypothesis,
    IntersectionEvidence,
    ResearchIntersection,
    ResearchJob,
    Researcher,
)
from app.providers.llm.base import PaperDraft
from app.providers.llm.factory import get_llm_provider
from app.schemas.paper_draft import (
    PaperCitation,
    PaperDraftOut,
    PaperEvidenceRef,
)

logger = structlog.get_logger(__name__)


class PaperDraftService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- retrieval ----------------------------------------------------------

    def report_for_job(self, job_id: str) -> GeneratedReport | None:
        return self.db.scalar(
            select(GeneratedReport).where(
                GeneratedReport.job_id == job_id,
                GeneratedReport.format == PAPER_DRAFT_FORMAT,
            )
        )

    def get_draft(self, job: ResearchJob) -> PaperDraftOut:
        report = self.report_for_job(job.id)
        if report is None:
            raise NotFoundError("No paper draft has been generated for this job yet.")
        try:
            out = PaperDraftOut.model_validate(json.loads(report.content))
        except (ValueError, TypeError):  # pragma: no cover - defensive
            raise NotFoundError("Paper draft report is malformed.") from None
        return out.model_copy(update={"report_id": report.id, "created_at": report.created_at})

    # -- generation ---------------------------------------------------------

    async def generate_for_job(
        self, job: ResearchJob, intersection: ResearchIntersection | None = None
    ) -> PaperDraftOut:
        """Generate (or regenerate) a draft for a discovery job. Idempotent.

        The previous draft for this job is replaced; other jobs' reports are
        never touched.
        """
        ix = intersection or self._select_intersection(job)
        context = self._collect_context(job, ix)
        if not ix:
            raise NotFoundError("No intersections were produced by this job; cannot write a paper draft.")

        agent = PaperWriterAgent(
            get_llm_provider(), db=self.db, workspace_id=job.workspace_id, job_id=job.id
        )
        allowed_ids = [e["id"] for e in context["evidence"]]
        draft = agent.finalize(await agent.generate_draft(context), allowed_ids)
        evidence_refs, citations = self._resolve_grounding(job.workspace_id, draft, allowed_ids)

        old = self.report_for_job(job.id)
        if old is not None:
            self.db.delete(old)
            self.db.flush()

        report = GeneratedReport(
            workspace_id=job.workspace_id,
            job_id=job.id,
            title=f"Research Paper Draft — {draft.title[:180]}",
            format=PAPER_DRAFT_FORMAT,
            content=json.dumps(
                PaperDraftOut.from_draft(
                    report_id="",
                    job_id=job.id,
                    workspace_id=job.workspace_id,
                    draft=draft,
                    evidence=evidence_refs,
                    citations=citations,
                    created_at=datetime.now(),
                ).model_dump(mode="json"),
                ensure_ascii=False,
            ),
            meta={
                "kind": "paper_draft",
                "evidence_count": len(evidence_refs),
                "citation_count": len(citations),
            },
        )
        self.db.add(report)
        self.db.flush()
        self.db.refresh(report)
        logger.info(
            "paper_draft.stored",
            job_id=job.id,
            report_id=report.id,
            evidence=len(evidence_refs),
            citations=len(citations),
        )
        return self._build_out(report, draft, evidence_refs, citations)

    # -- context ------------------------------------------------------------

    def _select_intersection(self, job: ResearchJob) -> ResearchIntersection | None:
        """Pick the best intersection for a job's draft.

        Prefers: (1) this job's own intersections, (2) intersections that
        produced a hypothesis, (3) higher novelty+feasibility. Falls back to
        workspace intersections so pre-existing completed jobs can still be
        drafted on demand.
        """
        rows = list(
            self.db.scalars(
                select(ResearchIntersection).where(
                    ResearchIntersection.workspace_id == job.workspace_id
                )
            )
        )
        if not rows:
            return None
        hyp_ix_ids = set(
            self.db.scalars(
                select(Hypothesis.intersection_id).where(
                    Hypothesis.workspace_id == job.workspace_id
                )
            )
        )
        rows.sort(
            key=lambda ix: (
                ix.job_id == job.id,
                ix.id in hyp_ix_ids,
                ix.novelty_confidence + ix.feasibility_confidence,
            ),
            reverse=True,
        )
        return rows[0]

    def _collect_context(
        self, job: ResearchJob, ix: ResearchIntersection | None
    ) -> dict:
        if ix is None:
            return {
                "intersection": {}, "hypothesis": {}, "experiment": {}, "evidence": []
            }
        hypothesis = self.db.scalar(
            select(Hypothesis).where(Hypothesis.intersection_id == ix.id)
        )
        experiment = hypothesis.experiment if hypothesis is not None else None

        ev_ids = list(
            self.db.scalars(
                select(IntersectionEvidence.evidence_id).where(
                    IntersectionEvidence.intersection_id == ix.id
                )
            )
        )
        evidence: list[dict] = []
        if ev_ids:
            rows = list(
                self.db.scalars(
                    select(Evidence).where(
                        Evidence.workspace_id == job.workspace_id,
                        Evidence.id.in_(ev_ids),
                    )
                )
            )
            statuses = {r.id: r.status for r in rows}
            evidence = [
                {
                    "id": r.id,
                    "claim": r.claim,
                    "status": statuses.get(r.id, "UNKNOWN"),
                    "source_title": r.source_title,
                }
                for r in rows
            ]

        a_name = (
            self.db.get(Researcher, ix.researcher_a_id).name
            if ix.researcher_a_id
            else None
        )
        b_name = (
            self.db.get(Researcher, ix.researcher_b_id).name
            if ix.researcher_b_id
            else None
        )
        return {
            "intersection": {
                "title": ix.title,
                "description": ix.description,
                "gap_description": ix.gap_description,
                "complementary_expertise": ix.complementary_expertise,
                "researcher_a_name": a_name,
                "researcher_b_name": b_name,
            },
            "hypothesis": {
                "research_question": hypothesis.research_question if hypothesis else None,
                "hypothesis_text": hypothesis.hypothesis_text if hypothesis else None,
                "motivation": hypothesis.motivation if hypothesis else None,
                "method": hypothesis.method if hypothesis else None,
                "dataset": hypothesis.dataset if hypothesis else None,
                "baseline": hypothesis.baseline if hypothesis else None,
                "metrics": hypothesis.metrics if hypothesis else None,
            },
            "experiment": {
                "proposed_approach": experiment.proposed_approach if experiment else None,
                "dataset": experiment.dataset if experiment else None,
                "dataset_status": experiment.dataset_status if experiment else None,
                "evaluation_setup": experiment.evaluation_setup if experiment else None,
                "ablations": experiment.ablations if experiment else [],
                "failure_conditions": experiment.failure_conditions if experiment else None,
            },
            "evidence": evidence,
        }

    def _resolve_grounding(
        self,
        workspace_id: str,
        draft: PaperDraft,
        allowed_ids: list[str],
    ) -> tuple[list[PaperEvidenceRef], list[PaperCitation]]:
        """Resolve draft-referenced evidence to stored, workspace-scoped rows."""
        allowed = set(allowed_ids)
        ref_ids = [
            eid for eid in dict.fromkeys(draft.evidence_ids) if eid in allowed
        ]
        cite_ids = [
            eid
            for eid in dict.fromkeys(draft.citation_evidence_ids)
            if eid in allowed
        ]
        rows = list(
            self.db.scalars(
                select(Evidence).where(
                    Evidence.workspace_id == workspace_id,
                    Evidence.id.in_(list(set(ref_ids + cite_ids)) or ["__none__"]),
                )
            )
        )
        by_id = {r.id: r for r in rows}

        evidence_refs: list[PaperEvidenceRef] = []
        for eid in ref_ids:
            row = by_id.get(eid)
            if row is None:
                continue
            evidence_refs.append(
                PaperEvidenceRef(
                    evidence_id=eid,
                    claim=row.claim,
                    status=row.status,
                    source_title=row.source_title,
                    source_url=row.source_url,
                )
            )

        citations: list[PaperCitation] = []
        for number, eid in enumerate(cite_ids, start=1):
            row = by_id.get(eid)
            if row is None:
                continue
            citations.append(
                PaperCitation(
                    evidence_id=eid,
                    number=number,
                    status=row.status,
                    text=_citation_text(row),
                )
            )
        return evidence_refs, citations

    # -- rendering -------------------------------------------------------------

    def render_markdown(self, out: PaperDraftOut, workspace_name: str) -> str:
        lines = [
            f"# {out.title}",
            "",
            f"_Workspace: {workspace_name} · Report: {out.report_id}_",
            "",
            f"**{out.draft_status}**",
            "",
            "## Abstract",
            "",
            out.abstract,
            "",
            "## 1. Introduction",
            "",
            out.introduction,
            "",
            "## 2. Related Work",
            "",
            out.related_work,
            "",
            "## 3. Research Gap",
            "",
            out.research_gap,
            "",
            "## 4. Research Question & Hypothesis",
            "",
            f"**Research question:** {out.research_question}",
            "",
            f"**Hypothesis:** {out.hypothesis}",
            "",
            "## 5. Methodology",
            "",
            out.methodology,
            "",
            "## 6. Experiment Design",
            "",
            out.experiment_design,
            "",
            "## 7. Expected Results",
            "",
            f"_({out.expected_results_label})_",
            "",
            out.expected_results,
            "",
            "## 8. Limitations",
            "",
        ]
        lines += [f"- {lim}" for lim in out.limitations] or ["- None recorded."]
        lines += ["", "## 9. Conclusion", "", out.conclusion, ""]
        if out.citations:
            lines.append("## References (grounded in stored evidence)")
            lines.append("")
            for c in out.citations:
                lines.append(f"[{c.number}] {c.text} _([{c.status}])_")
        if out.evidence:
            lines += [
                "",
                "## Grounding Evidence",
                "",
                "Each claim in this draft traces to stored evidence:",
                "",
            ]
            for i, e in enumerate(out.evidence, start=1):
                lines.append(
                    f"- **[{e.status}]** {e.claim} — {e.source_title or 'stored evidence item'} "
                    f"(evidence ID: `{e.evidence_id}`)"
                )
        return "\n".join(lines)

    def render_pdf(self, markdown_text: str) -> bytes:
        from app.services.report_service import ReportService

        return ReportService(self.db).render_pdf(markdown_text)

    # -- helpers ---------------------------------------------------------------

    def _build_out(
        self,
        report: GeneratedReport,
        draft: PaperDraft,
        evidence: list[PaperEvidenceRef],
        citations: list[PaperCitation],
    ) -> PaperDraftOut:
        return PaperDraftOut.from_draft(
            report_id=report.id,
            job_id=report.job_id or "",
            workspace_id=report.workspace_id,
            draft=draft,
            evidence=evidence,
            citations=citations,
            created_at=report.created_at,
        )


def _citation_text(ev: Evidence) -> str:
    """Build a reference from the stored paper if available (no fabrication)."""
    if ev.paper is not None:
        paper = ev.paper
        authors = ", ".join(
            a.author_name for a in sorted(paper.authors, key=lambda x: x.position)
        )
        venue = paper.venue or ""
        year = f", {paper.publication_year}" if paper.publication_year else ""
        core = f'"{paper.title}"'
        return f"{authors or 'Unknown author'}. {core}. {venue}{year}."
    if ev.source_title:
        return f"{ev.source_title}. Stored evidence item with no linked paper."
    claim = (ev.claim or "")[:200]
    return f"Stored evidence item: {claim}…"
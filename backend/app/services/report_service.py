"""Report service: workspace research reports in markdown/json/csv/pdf."""
from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ReportFormat
from app.db.models import (
    CollaborationCandidate,
    Evidence,
    Experiment,
    GeneratedReport,
    Hypothesis,
    ResearchGap,
    ResearchIntersection,
    ResearchTrajectory,
    Researcher,
)
from app.services.settings_service import SettingsService

logger = structlog.get_logger(__name__)


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- data gathering ------------------------------------------------------

    def _collect(self, workspace_id: str) -> dict:
        intersections = list(
            self.db.scalars(
                select(ResearchIntersection)
                .where(ResearchIntersection.workspace_id == workspace_id)
                .order_by(ResearchIntersection.created_at.desc())
            )
        )
        gaps = list(
            self.db.scalars(select(ResearchGap).where(ResearchGap.workspace_id == workspace_id))
        )
        hypotheses = list(
            self.db.scalars(select(Hypothesis).where(Hypothesis.workspace_id == workspace_id))
        )
        experiments = {
            e.hypothesis_id: e
            for e in self.db.scalars(
                select(Experiment).where(
                    Experiment.hypothesis_id.in_([h.id for h in hypotheses] or [""])
                )
            )
        }
        collabs = list(
            self.db.scalars(
                select(CollaborationCandidate)
                .where(CollaborationCandidate.workspace_id == workspace_id)
                .order_by(CollaborationCandidate.score.desc())
            )
        )
        evidence = list(
            self.db.scalars(select(Evidence).where(Evidence.workspace_id == workspace_id).limit(300))
        )
        trajectories = list(
            self.db.scalars(
                select(ResearchTrajectory).where(ResearchTrajectory.workspace_id == workspace_id)
            )
        )
        researchers = {
            r.id: r
            for r in self.db.scalars(select(Researcher))
        }
        return {
            "intersections": intersections,
            "gaps": gaps,
            "hypotheses": hypotheses,
            "experiments": experiments,
            "collaborations": collabs,
            "evidence": evidence,
            "trajectories": trajectories,
            "researchers": researchers,
        }

    # -- renderers -------------------------------------------------------------

    def render_markdown(self, workspace_name: str, data: dict) -> str:
        lines: list[str] = [
            f"# ResearchCollision Report — {workspace_name}",
            "",
            f"_Generated: {datetime.now(timezone.utc).isoformat()} — AI-generated suggestions, not scientific truth._",
            "",
            "## 1. Research Profile & Trajectories",
        ]
        for t in data["trajectories"]:
            r = data["researchers"].get(t.researcher_id)
            name = r.name if r else t.researcher_id
            lines.append(f"### {name}")
            lines.append(t.summary or "_No summary available._")
            tj = t.trajectory_json or {}
            if tj.get("current_focus"):
                lines.append(f"- Current focus: {', '.join(tj['current_focus'])}")
            if tj.get("emerging_interests"):
                lines.append(f"- Emerging interests: {', '.join(tj['emerging_interests'])}")
            lines.append("")

        lines.append("## 2. Literature Overview")
        papers = {e.paper_id for e in data["evidence"] if e.paper_id}
        lines.append(f"Evidence items reference {len(papers)} distinct stored papers.")
        lines.append("")

        lines.append("## 3. Research Gaps")
        for g in data["gaps"]:
            lines.append(f"- **[{g.gap_type}]** (confidence {g.confidence:.2f}, status {g.status}) {g.description}")
        if not data["gaps"]:
            lines.append("- No gaps recorded yet.")
        lines.append("")

        lines.append("## 4. Research Intersections")
        for ix in data["intersections"]:
            a = data["researchers"].get(ix.researcher_a_id)
            b = data["researchers"].get(ix.researcher_b_id)
            lines.append(f"### {ix.title}")
            lines.append(f"- Researchers: {a.name if a else '?'} + {b.name if b else '?'} ({ix.discovery_mode} mode)")
            lines.append(f"- Shared problem: {ix.shared_problem or '—'}")
            lines.append(f"- Gap: {ix.gap_description or '—'}")
            lines.append(f"- Why A: {ix.why_researcher_a or '—'}")
            lines.append(f"- Why B: {ix.why_researcher_b or '—'}")
            lines.append(
                f"- Novelty confidence: {ix.novelty_confidence:.2f} | Feasibility: {ix.feasibility_confidence:.2f}"
            )
            lines.append("")

        lines.append("## 5. Hypotheses (AI-GENERATED)")
        for h in data["hypotheses"]:
            lines.append(f"### [{h.label}] {h.research_question}")
            lines.append(f"- Hypothesis: {h.hypothesis_text}")
            exp = data["experiments"].get(h.id)
            if exp:
                lines.append(
                    f"- Experiment: baseline={exp.baseline}; dataset={exp.dataset} "
                    f"(status: {exp.dataset_status}); metrics={exp.metrics}"
                )
                lines.append(f"- Failure conditions: {exp.failure_conditions or '—'}")
            lines.append("")

        lines.append("## 6. Collaboration Candidates")
        for c in data["collaborations"][:20]:
            a = data["researchers"].get(c.researcher_a_id)
            b = data["researchers"].get(c.researcher_b_id)
            lines.append(
                f"- **{c.score:.1f} ({c.category})** — {a.name if a else '?'} + {b.name if b else '?'}"
            )
        if not data["collaborations"]:
            lines.append("- No collaboration candidates yet.")
        lines.append("")

        lines.append("## 7. Evidence Summary")
        by_status: dict[str, int] = {}
        for e in data["evidence"]:
            by_status[e.status] = by_status.get(e.status, 0) + 1
        lines.append(", ".join(f"{k}: {v}" for k, v in sorted(by_status.items())) or "No evidence yet.")
        lines.append("")
        lines.append("## 8. Limitations")
        lines.append(
            "- All hypotheses and intersections are AI-generated suggestions based on retrieved literature.\n"
            "- Novelty statements mean only that no relevant evidence was found in the searched literature.\n"
            "- Collaboration candidates reflect publication relevance, not willingness to collaborate."
        )
        return "\n".join(lines)

    def render_csv(self, data: dict) -> str:
        import csv

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["type", "title_or_description", "score_or_confidence", "category_or_status"])
        for ix in data["intersections"]:
            writer.writerow(["intersection", ix.title, ix.novelty_confidence, ix.status])
        for g in data["gaps"]:
            writer.writerow(["gap", g.description[:200], g.confidence, g.status])
        for c in data["collaborations"]:
            writer.writerow(["collaboration", f"{c.researcher_a_id}+{c.researcher_b_id}", c.score, c.category])
        return buf.getvalue()

    def render_pdf(self, markdown_text: str) -> bytes:
        try:
            import pymupdf as fitz_mod
        except ImportError:
            import fitz as fitz_mod
        doc = fitz_mod.open()
        page = doc.new_page()
        rect = fitz_mod.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
        html = "<pre style='font-family:helvetica;font-size:9px'>" + (
            markdown_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ) + "</pre>"
        try:
            page.insert_htmlbox(rect, html)
        except Exception:
            page.insert_text((50, 72), markdown_text[:40000], fontsize=8)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    # -- public API --------------------------------------------------------------

    def generate(
        self,
        *,
        workspace_id: str,
        workspace_name: str,
        fmt: str = "markdown",
        job_id: str | None = None,
        title: str | None = None,
    ) -> GeneratedReport:
        data = self._collect(workspace_id)
        fmt_enum = ReportFormat(fmt) if fmt in [f.value for f in ReportFormat] else ReportFormat.MARKDOWN
        md = self.render_markdown(workspace_name, data)
        meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "counts": {
            "intersections": len(data["intersections"]),
            "gaps": len(data["gaps"]),
            "hypotheses": len(data["hypotheses"]),
            "collaborations": len(data["collaborations"]),
            "evidence": len(data["evidence"]),
        }}
        if fmt_enum == ReportFormat.JSON:
            content = json.dumps(
                {
                    "workspace": workspace_name,
                    "meta": meta,
                    "intersections": [
                        {
                            "id": i.id, "title": i.title, "description": i.description,
                            "novelty_confidence": i.novelty_confidence,
                            "feasibility_confidence": i.feasibility_confidence,
                        }
                        for i in data["intersections"]
                    ],
                    "gaps": [
                        {"id": g.id, "description": g.description, "gap_type": g.gap_type,
                         "confidence": g.confidence, "status": g.status}
                        for g in data["gaps"]
                    ],
                    "hypotheses": [
                        {"id": h.id, "question": h.research_question, "text": h.hypothesis_text,
                         "label": h.label}
                        for h in data["hypotheses"]
                    ],
                    "collaborations": [
                        {"score": c.score, "category": c.category,
                         "a": c.researcher_a_id, "b": c.researcher_b_id}
                        for c in data["collaborations"]
                    ],
                },
                indent=2,
            )
        elif fmt_enum == ReportFormat.CSV:
            content = self.render_csv(data)
        elif fmt_enum == ReportFormat.PDF:
            content = base64.b64encode(self.render_pdf(md)).decode("ascii")
            meta["encoding"] = "base64-pdf"
        else:
            content = md
        report = GeneratedReport(
            workspace_id=workspace_id,
            job_id=job_id,
            title=title or f"{workspace_name} — Research Report ({fmt_enum.value})",
            format=fmt_enum.value,
            content=content,
            meta=meta,
        )
        self.db.add(report)
        self.db.flush()
        logger.info("report.generated", report_id=report.id, format=fmt_enum.value)
        return report

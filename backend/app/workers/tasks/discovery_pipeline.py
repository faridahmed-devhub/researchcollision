"""Discovery pipeline — the full agentic workflow as ordered steps."""
from __future__ import annotations

import time

import structlog

from app.agents.gap_agent import GapAgent
from app.agents.hypothesis_agent import HypothesisAgent
from app.agents.intersection_agent import IntersectionAgent
from app.agents.paper_analysis_agent import PaperAnalysisAgent
from app.agents.ranking_agent import RankingAgent
from app.agents.trajectory_agent import TrajectoryAgent
from app.core.constants import (
    DISCOVERY_STEPS,
    COLLAB_LANGUAGE,
    DiscoveryMode,
    EvidenceStatus,
    JobStatus,
)
from app.db.models import (
    PaperAuthor,
    ResearchGap,
    ResearchGapEvidence,
    Researcher,
    ResearcherAlias,
)
from app.db.repositories.job_repository import JobRepository
from app.providers.llm.factory import get_llm_provider
from app.services.evidence_service import EvidenceService
from app.services.hypothesis_service import HypothesisService
from app.services.intersection_service import IntersectionService
from app.services.literature_service import LiteratureService
from app.services.paper_service import PaperService
from app.services.settings_service import SettingsService
from app.services.trajectory_service import TrajectoryService
from app.services.vector_service import VectorService

logger = structlog.get_logger(__name__)


class StepControl(Exception):
    """Raised to pause/cancel the pipeline cooperatively."""


class DiscoveryPipeline:
    def __init__(self, db, job) -> None:  # type: ignore[no-untyped-def]
        self.db = db
        self.job = job
        self.workspace_id = job.workspace_id
        self.config = job.config or {}
        self.job_repo = JobRepository(db)
        self.llm = get_llm_provider()
        self.paper_service = PaperService(db)
        self.evidence_service = EvidenceService(db)
        self.traj_service = TrajectoryService(db)
        self.ix_service = IntersectionService(db)
        self.hyp_service = HypothesisService(db)
        self.vector_service = VectorService(db)
        self.settings_service = SettingsService(db)
        self.literature = LiteratureService()
        self._paper_analyses: list[dict] = []
        self._gaps: list[dict] = []
        self._gap_rows: list[ResearchGap] = []
        self._intersections = []
        self.result_summary: dict = {}

    # -- control ---------------------------------------------------------------

    def _check_control(self) -> None:
        self.db.refresh(self.job)
        if self.job.cancel_requested:
            raise StepControl("CANCEL")
        if self.job.pause_requested:
            raise StepControl("PAUSE")

    def _step_begin(self, step: str, index: int, total: int) -> None:
        self.job.current_step = step
        self.job.progress = round(index / total * 100, 1)
        self.job_repo.add_event(self.job.id, "step_started", step, {"index": index})
        self.db.commit()

    def _step_done(self, step: str, index: int, total: int) -> None:
        self.job.progress = round((index + 1) / total * 100, 1)
        self.job_repo.add_event(self.job.id, "step_completed", step, {"index": index})
        self.db.commit()

    # -- main entry --------------------------------------------------------------

    async def run(self) -> str:
        """Returns final status string: COMPLETED | PAUSED | CANCELLED | FAILED."""
        total = len(DISCOVERY_STEPS)
        self.job.total_steps = total
        try:
            for i, step in enumerate(DISCOVERY_STEPS):
                self._check_control()
                self._step_begin(step, i, total)
                started = time.perf_counter()
                handler = getattr(self, f"step_{step}")
                await handler()
                logger.info(
                    "pipeline.step_done",
                    step=step,
                    seconds=round(time.perf_counter() - started, 2),
                    job_id=self.job.id,
                )
                self._check_control()
                self._step_done(step, i, total)
            self.job.status = JobStatus.COMPLETED.value
            self.job.progress = 100.0
            self.job.completed_at = __import__("datetime").datetime.utcnow()
            self.job.result_summary = self.result_summary
            self.job_repo.add_event(self.job.id, "job_completed", "Discovery completed", self.result_summary)
            self.db.commit()
            return JobStatus.COMPLETED.value
        except StepControl as ctrl:
            if str(ctrl) == "CANCEL":
                self.job.status = JobStatus.CANCELLED.value
                self.job_repo.add_event(self.job.id, "job_cancelled", "Cancelled by user")
            else:
                self.job.status = JobStatus.PAUSED.value
                self.job.pause_requested = False
                self.job_repo.add_event(self.job.id, "job_paused", f"Paused at {self.job.current_step}")
            self.db.commit()
            return str(ctrl)

    # -- steps ---------------------------------------------------------------------

    async def step_resolve_inputs(self) -> None:
        ra_id = self.config.get("researcher_a_id")
        rb_id = self.config.get("researcher_b_id")
        field_query = self.config.get("field_query")
        self._researcher_a = self.db.get(Researcher, ra_id)
        if self._researcher_a is None:
            raise ValueError(f"Researcher A {ra_id} not found")
        if rb_id:
            self._researcher_b = self.db.get(Researcher, rb_id)
            if self._researcher_b is None:
                raise ValueError(f"Researcher B {rb_id} not found")
        elif field_query:
            self._researcher_b = self._ensure_field_researcher(field_query)
        else:
            raise ValueError("Either researcher_b_id or field_query is required")

    def _ensure_field_researcher(self, field_query: str) -> Researcher:
        """Create/reuse a virtual researcher representing a field of interest."""
        name = f"[Field] {field_query}"
        existing = (
            self.db.query(Researcher)
            .filter(Researcher.workspace_id == self.workspace_id, Researcher.name == name)
            .first()
        )
        if existing:
            return existing
        r = Researcher(
            workspace_id=self.workspace_id,
            name=name[:290],
            affiliation=None,
            bio=f"Virtual field profile representing interest in '{field_query}'. Not a real person.",
        )
        self.db.add(r)
        self.db.flush()
        return r

    async def step_literature_search(self) -> None:
        from app.agents.literature_agent import LiteratureAgent

        agent = LiteratureAgent(self.literature.chain)
        interests_a = self._researcher_topics(self._researcher_a)
        interests_b = self._researcher_topics(self._researcher_b)
        queries = agent.build_queries(
            interests_a=interests_a,
            interests_b=interests_b,
            field_query=self.config.get("field_query"),
        )
        if not queries:
            queries = [self._researcher_a.name]
        max_papers = int(self.config.get("max_papers", 12))
        seen_ids: set[str] = set()
        self._papers = []
        provider_used = None
        for q in queries:
            try:
                papers, provider = await self.literature.search(q, limit=max_papers)
                provider_used = provider_used or provider
            except Exception as exc:
                logger.warning("pipeline.lit_query_failed", query=q, error=str(exc)[:150])
                continue
            for meta in papers:
                paper, _created = self.paper_service.upsert_from_metadata(meta)
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    self._papers.append(paper)
                self._link_author(paper, meta.authors)
        self.db.commit()
        # keep only the most relevant N papers for downstream LLM work
        self._papers.sort(key=lambda p: (p.publication_year or 0), reverse=True)
        self._papers = self._papers[: max_papers * 2]
        self._provider_used = provider_used
        self.job_repo.add_event(
            self.job.id,
            "literature_found",
            f"{len(self._papers)} papers retrieved",
            {"queries": queries, "provider": provider_used},
        )

    def _researcher_topics(self, r: Researcher) -> list[str]:
        topics: list[str] = []
        traj = self.traj_service.get(self.workspace_id, r.id)
        if traj and traj.trajectory_json:
            tj = traj.trajectory_json
            topics += tj.get("current_focus", []) + tj.get("historical_focus", [])
        if r.bio:
            import re

            topics += [w for w in re.findall(r"[a-z][a-z-]{4,}", r.bio.lower())][:6]
        return list(dict.fromkeys(topics))[:8]

    def _link_author(self, paper, author_names: list[str]) -> None:
        """Match provider author names to known researchers by name/alias."""
        targets = {}
        for r in (self._researcher_a, self._researcher_b):
            if r and r.id:
                targets[r.name.lower()] = r.id
                for alias in r.aliases:
                    targets[alias.alias.lower()] = r.id
        for name in author_names:
            rid = targets.get(name.strip().lower())
            if rid:
                exists = (
                    self.db.query(PaperAuthor)
                    .filter(PaperAuthor.paper_id == paper.id, PaperAuthor.researcher_id == rid)
                    .first()
                )
                if not exists:
                    self.db.add(PaperAuthor(paper_id=paper.id, researcher_id=rid, author_name=name))
                    self.db.flush()

    async def step_analyze_papers(self) -> None:
        agent = PaperAnalysisAgent(
            self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id
        )
        self._paper_analyses = []
        errors = 0
        for paper in self._papers:
            try:
                ev = self.evidence_service.for_paper(
                    self.workspace_id,
                    paper,
                    claim=f"Paper '{paper.title}' reports findings relevant to the searched literature.",
                )
                analysis = await agent.analyze(
                    title=paper.title,
                    abstract=paper.abstract or "",
                    year=paper.publication_year,
                    venue=paper.venue,
                    domain_hint=(paper.topics[0].name if hasattr(paper, "topics") and paper.topics else None),
                    evidence_id=ev.id,
                )
                ad = analysis.model_dump()
                ad["title"] = paper.title
                ad["evidence_id"] = ev.id
                self._paper_analyses.append(ad)
                self.paper_service.link_methods(paper.id, ad.get("methods", []))
                self.paper_service.link_datasets(paper.id, ([ad["dataset"]] if ad.get("dataset") else []))
                await self.vector_service.embed_and_store(
                    entity_type="paper",
                    entity_id=paper.id,
                    text=f"{paper.title}\n{(paper.abstract or '')[:800]}",
                    workspace_id=self.workspace_id,
                )
            except Exception as exc:
                errors += 1
                logger.warning("pipeline.paper_analysis_failed", paper=paper.title[:60], error=str(exc)[:150])
                self.job_repo.add_event(
                    self.job.id, "item_failed", f"Analysis failed for '{paper.title[:60]}'"
                )
                continue
        self.db.commit()
        self.result_summary["papers_analyzed"] = len(self._paper_analyses)
        self.result_summary["analysis_errors"] = errors

    async def step_analyze_trajectories(self) -> None:
        agent = TrajectoryAgent(
            self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id
        )
        self._trajectories: dict[str, dict] = {}
        for r in (self._researcher_a, self._researcher_b):
            papers = self.traj_service.papers_for_researcher(r)
            context = self.traj_service.paper_context(papers)
            evidence_ids = []
            for p in papers:
                pa = next((x for x in self._paper_analyses if x["title"] == p.title), None)
                if pa:
                    evidence_ids.append(pa["evidence_id"])
            try:
                analysis = await agent.analyze(
                    researcher_name=r.name, papers=context, evidence_ids=evidence_ids
                )
                ad = analysis.model_dump()
            except Exception as exc:
                logger.warning("pipeline.trajectory_failed", researcher=r.name, error=str(exc)[:150])
                ad = {
                    "historical_focus": [], "current_focus": [], "emerging_interests": [],
                    "methodology_shifts": [], "domain_shifts": [], "topic_transitions": [],
                    "phases": [], "summary": "", "evidence_ids": [],
                }
            self.traj_service.save_trajectory(
                workspace_id=self.workspace_id,
                researcher_id=r.id,
                analysis_dict=ad,
                summary=ad.get("summary", ""),
            )
            methods_pool = sorted({m for c in context for m in c["methods"]})
            domains = sorted({t for c in context for t in c["topics"]})
            self._trajectories[r.id] = {**ad, "methods_pool": methods_pool, "domains": domains}
        self.db.commit()

    async def step_detect_gaps(self) -> None:
        from sqlalchemy import select

        agent = GapAgent(self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id)
        valid_evidence_ids = set(
            self.db.scalars(select_evidence(self.workspace_id)).all()
        )
        result = await agent.detect(self._paper_analyses)
        # clear previous gaps for this workspace (regeneration replaces)
        for old in self.db.query(ResearchGap).filter(ResearchGap.workspace_id == self.workspace_id).all():
            self.db.delete(old)
        self.db.flush()
        self._gaps = []
        self._gap_rows = []
        for g in result.gaps:
            ev_ids = [e for e in g.evidence_ids if e in valid_evidence_ids]
            row = ResearchGap(
                workspace_id=self.workspace_id,
                job_id=self.job.id,
                description=g.description,
                gap_type=g.gap_type,
                confidence=g.confidence,
                status=EvidenceStatus.INFERRED.value if ev_ids else EvidenceStatus.UNKNOWN.value,
            )
            self.db.add(row)
            self.db.flush()
            for e in ev_ids[:6]:
                self.db.add(ResearchGapEvidence(gap_id=row.id, evidence_id=e))
            gd = g.model_dump()
            gd["row_id"] = row.id
            self._gaps.append(gd)
            self._gap_rows.append(row)
        self.db.commit()
        self.result_summary["gaps"] = len(self._gaps)

    async def step_discover_intersections(self) -> None:
        agent = IntersectionAgent(
            self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id
        )
        mode = DiscoveryMode(self.config.get("mode", "normal"))
        ctx_a = self._researcher_ctx(self._researcher_a)
        ctx_b = self._researcher_ctx(self._researcher_b)
        result = await agent.discover(
            researcher_a=ctx_a,
            researcher_b=ctx_b,
            gaps=self._gaps,
            mode=mode,
            max_intersections=5,
        )
        self._intersections = []
        for cand in result.intersections:
            gap_row_id = None
            gi = cand.gap_index
            if gi is not None and 0 <= gi < len(self._gaps):
                gap_row_id = self._gaps[gi].get("row_id")
            ix = self.ix_service.create(
                workspace_id=self.workspace_id,
                job_id=self.job.id,
                candidate=cand.model_dump(),
                researcher_a_id=self._researcher_a.id,
                researcher_b_id=self._researcher_b.id,
                research_gap_id=gap_row_id,
                mode=mode,
            )
            self._intersections.append(ix)
        self.db.commit()
        self.result_summary["intersections"] = len(self._intersections)

    def _researcher_ctx(self, r: Researcher) -> dict:
        traj = self._trajectories.get(r.id, {})
        all_topics = list(
            dict.fromkeys(
                self._researcher_topics(r)
                + traj.get("historical_focus", [])
                + traj.get("emerging_interests", [])
            )
        )
        return {
            "name": r.name,
            "affiliation": r.affiliation,
            "topics": all_topics,
            "methods": traj.get("methods_pool", []),
            "domains": traj.get("domains", []),
            "trajectory": traj,
            "methods_pool": traj.get("methods_pool", []),
        }

    async def step_verify_evidence(self) -> None:
        applied = self.evidence_service.run_verification(self.workspace_id)
        self.db.commit()
        verified = sum(1 for u in applied if u["status"] == EvidenceStatus.VERIFIED.value)
        self.result_summary["evidence_verified"] = verified
        self.result_summary["evidence_updated"] = len(applied)

    async def step_generate_hypotheses(self) -> None:
        if not self.config.get("generate_hypotheses", True):
            return
        agent = HypothesisAgent(
            self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id
        )
        ranked = sorted(
            self._intersections,
            key=lambda i: (i.novelty_confidence + i.feasibility_confidence),
            reverse=True,
        )[:3]
        known_datasets = self.hyp_service.known_dataset_names()
        count = 0
        for ix in ranked:
            try:
                draft = await agent.generate_hypothesis(
                    {
                        "title": ix.title,
                        "description": ix.description,
                        "shared_problem": ix.shared_problem,
                        "complementary_expertise": ix.complementary_expertise,
                        "research_gap": ix.gap_description,
                        "evidence_ids": self.ix_service.evidence_ids_for(ix.id),
                    },
                    known_datasets,
                )
                hyp = self.hyp_service.create(
                    workspace_id=self.workspace_id, intersection_id=ix.id, draft=draft.model_dump()
                )
                design = await agent.design_experiment(draft.model_dump(), known_datasets)
                self.hyp_service.attach_experiment(hyp, design.model_dump())
                count += 1
            except Exception as exc:
                logger.warning("pipeline.hypothesis_failed", intersection=ix.title[:50], error=str(exc)[:150])
                continue
        self.db.commit()
        self.result_summary["hypotheses"] = count

    async def step_rank_collaborations(self) -> None:
        from app.services.collaboration_service import CollaborationService

        ranking_agent = RankingAgent()
        collab_service = CollaborationService(self.db)
        weights = self.settings_service.collaboration_weights()
        count = 0
        for ix in self._intersections:
            ev_ids = self.ix_service.evidence_ids_for(ix.id)
            verified_ratio = 0.0
            if ev_ids:
                from app.db.models import Evidence as Ev

                statuses = self.db.scalars(select_ev_status(ev_ids)).all()
                verified_ratio = (
                    sum(1 for s in statuses if s in (EvidenceStatus.VERIFIED.value, EvidenceStatus.INFERRED.value))
                    / len(statuses)
                    if statuses
                    else 0.0
                )
            from app.utils.text import topics_shared

            shared_topics = topics_shared(
                self._researcher_topics(self._researcher_a),
                self._researcher_topics(self._researcher_b),
            )
            components = ranking_agent.score_components_from_context(
                shared_topics=shared_topics,
                a_methods=self._trajectories.get(self._researcher_a.id, {}).get("methods_pool", []),
                b_methods=self._trajectories.get(self._researcher_b.id, {}).get("methods_pool", []),
                intersection_novelty=ix.novelty_confidence,
                intersection_feasibility=ix.feasibility_confidence,
                evidence_count=len(ev_ids),
                verified_ratio=verified_ratio,
                gap_confidence=(
                    self._gaps[0]["confidence"] if self._gaps else 0.3
                ),
            )
            ranking = ranking_agent.rank_pair(weights=weights, **components)
            rationale = (
                f"{self._researcher_a.name} and {self._researcher_b.name} "
                f"{COLLAB_LANGUAGE}; combined score driven by shared topics "
                f"({', '.join(shared_topics[:3]) or 'none detected'}) and evidence strength."
            )
            collab_service.create(
                workspace_id=self.workspace_id,
                intersection_id=ix.id,
                researcher_a_id=self._researcher_a.id,
                researcher_b_id=self._researcher_b.id,
                ranking=ranking,
                rationale=rationale,
            )
            count += 1
        self.db.commit()
        self.result_summary["collaboration_candidates"] = count


# small helpers kept at module scope for testability
def select_evidence(workspace_id: str):  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from app.db.models import Evidence

    return select(Evidence.id).where(Evidence.workspace_id == workspace_id)


def select_ev_status(ids: list[str]):  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from app.db.models import Evidence

    return select(Evidence.status).where(Evidence.id.in_(ids))

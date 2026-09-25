"""Comparison baselines and the ResearchCollision agentic pipeline.

Four systems are compared by the evaluator:

* ``keyword``       — lexical keyword-overlap retrieval over the case corpus
* ``embedding``     — embedding-similarity retrieval (deterministic mock
                      embeddings, no downloads / credentials required)
* ``llm_only``      — a language model invoked WITHOUT the retrieval/evidence
                      machinery. Under offline defaults this is the
                      deterministic MockLLMProvider, which returns zero
                      citations (a retrieval-free baseline cannot ground its
                      claims). With real credentials a real model runs instead.
* ``pipeline``      — the actual ResearchCollision ``DiscoveryPipeline`` end
                      to end (search -> analysis -> trajectories -> gaps ->
                      intersections -> hypotheses + experiment design), run in
                      an isolated temp database with mock providers.

Every system returns a normalized :class:`SystemOutput`. Failures inside a
system run are surfaced as exceptions and captured by the runner.
"""
from __future__ import annotations

import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.environment import configure_offline_defaults
from evaluation.schemas import (
    EvaluationCase,
    ResearcherInput,
    SourcePaper,
    SystemGap,
    SystemHypothesis,
    SystemIntersection,
    SystemOutput,
    SystemRef,
)

configure_offline_defaults()

from sqlalchemy import select

from app.core.constants import JobStatus
from app.db.base import Base
from app.db.models import (
    Evidence,
    Experiment,
    Hypothesis,
    IntersectionEvidence,
    Paper,
    Researcher,
    ResearchGap,
    ResearchGapEvidence,
    ResearchIntersection,
    ResearchJob,
    User,
    Workspace,
)

LLM_ONLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"description": {"type": "string"}},
                "required": ["description"],
            },
        },
        "intersections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "description"],
            },
        },
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
        "evidence_titles": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["gaps", "intersections", "hypotheses", "evidence_titles"],
}


def _topic_tokens(case: EvaluationCase) -> set[str]:
    from evaluation.metrics import tokenize

    parts: list[str] = []
    for r in (case.researcher_a, case.researcher_b):
        if r:
            parts += r.topics + r.methods
        if r and r.bio:
            parts.append(r.bio)
    if case.field_query:
        parts.append(case.field_query)
    return tokenize(" ".join(parts))


def _paper_window(p: SourcePaper, topics_set: set[str]) -> set[str]:
    from evaluation.metrics import tokenize

    out = set()
    for t in p.topics:
        out.update(tokenize(t))
    return out


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

@dataclass
class SystemScore:
    # kept as a tiny placeholder for future per-case scoring knobs
    pass


class BaseSystem:
    name: str = ""
    kind: str = "baseline"

    def __init__(self, seed: int | None = None) -> None:
        # Seed is forwarded to LLM providers for reproducible sampling where
        # the endpoint supports it. Deterministic components (retrieval,
        # mock providers) ignore it. Systems are constructed fresh per run via
        # ``get_system(name, seed=...)`` so instances never share mutable state.
        self.seed = seed

    async def run(self, case: EvaluationCase) -> SystemOutput:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Keyword-overlap baseline
# ---------------------------------------------------------------------------

class KeywordOverlapBaseline(BaseSystem):
    """Ranks corpus papers by token overlap with the researcher inputs."""

    name = "keyword"
    kind = "baseline"

    def _score(self, p: SourcePaper, q: set[str]) -> float:
        title = set(p.title.lower().split())
        abstract = set(p.abstract.lower().split())
        topics = set()
        for t in p.topics:
            topics.update(t.lower().split())
        for m in p.methods:
            topics.update(m.lower().split())
        return 3.0 * len(q & topics) + 2.0 * len(q & title) + 1.0 * len(q & abstract)

    async def run(self, case: EvaluationCase) -> SystemOutput:
        q = _topic_tokens(case)
        ranked = sorted(case.source_papers, key=lambda p: self._score(p, q), reverse=True)
        refs = [SystemRef(title=p.title, paper_id=p.paper_id) for p in ranked[:3]]

        covered: set[str] = set()
        for p in ranked[:3]:
            for t in p.topics:
                covered.update(t.lower().split())
        miss_topics = [
            t for t in (case.researcher_a.topics + (case.researcher_b.topics if case.researcher_b else []))
            if not (set(t.lower().split()) & covered)
        ][:3]

        a_name = case.researcher_a.name
        b_name = case.researcher_b.name if case.researcher_b else (case.field_query or "a second domain")
        gaps = [
            SystemGap(
                description=(
                    f"No source paper in the retrieved set jointly covers '{t}' across "
                    f"{a_name} and {b_name}; a combined treatment is missing."
                ),
                evidence_refs=refs,
            )
            for t in miss_topics
        ] or [
            SystemGap(
                description=(
                    f"Retrieved coverage is limited to the listed papers; a deeper corpus "
                    f"would be needed to confirm gaps between {a_name} and {b_name}."
                ),
                evidence_refs=refs,
            )
        ]

        intersections: list[SystemIntersection] = []
        if len(refs) >= 2:
            intersections.append(
                SystemIntersection(
                    title=f"Bridging '{refs[0].title[:60]}' and '{refs[1].title[:60]}'",
                    description=(
                        f"The two most overlapping papers share vocabulary with the "
                        f"combined expertise of {a_name} and {b_name}; combining their "
                        f"reported methods is a plausible joint direction."
                    ),
                    research_gap=gaps[0].description,
                    evidence_refs=refs,
                )
            )
        if not intersections:
            intersections.append(
                SystemIntersection(
                    title=f"Top-candidate pairing for {a_name} and {b_name}",
                    description="Keyword overlap identified only weak ties; manual inspection required.",
                    research_gap=gaps[0].description,
                    evidence_refs=refs or [SystemRef(title=p.title, paper_id=p.paper_id) for p in ranked[:1]],
                )
            )

        hypotheses = [
            SystemHypothesis(
                text=(
                    f"Combining the methods reported in the top retrieved papers will yield "
                    f"gains on {gaps[0].description}"
                ),
                evidence_refs=refs,
            )
        ]

        return SystemOutput(system=self.name, kind=self.kind, gaps=gaps,
                            intersections=intersections, hypotheses=hypotheses,
                            known_context_titles=[p.title for p in case.source_papers])


# ---------------------------------------------------------------------------
# Embedding-similarity baseline
# ---------------------------------------------------------------------------

class EmbeddingSimilarityBaseline(BaseSystem):
    """Retrieves corpus papers by cosine similarity to the combined inputs.

    Uses the deterministic MockEmbeddingProvider directly so the framework
    never requires embedding API credentials or model downloads.
    """

    name = "embedding"
    kind = "baseline"

    async def run(self, case: EvaluationCase) -> SystemOutput:
        from app.providers.embeddings.mock import MockEmbeddingProvider

        emb = MockEmbeddingProvider()

        def _vec(tokens: list[str]) -> list[float]:
            return emb._embed_one(" ".join(tokens))

        def _cos(a: list[float], b: list[float]) -> float:
            return sum(x * y for x, y in zip(a, b)) / (
                (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5) or 1.0
            )

        query_parts: list[str] = []
        for r in (case.researcher_a, case.researcher_b):
            if r:
                query_parts += r.topics + r.methods
        if case.field_query:
            query_parts.append(case.field_query)
        query_vec = _vec(query_parts)

        scored: list[tuple[float, SourcePaper]] = []
        for p in case.source_papers:
            text = " ".join(p.topics + p.methods + [p.title, (p.abstract or "")[:400]])
            scored.append((_cos(query_vec, _vec(text.split())), p))
        scored.sort(key=lambda t: t[0], reverse=True)
        refs = [SystemRef(title=p.title, paper_id=p.paper_id) for _, p in scored[:3]]

        gaps = [
            SystemGap(
                description=(
                    f"Topics outside the top-ranked papers are least similar to the combined "
                    f"inputs for {case.researcher_a.name} and "
                    f"{(case.researcher_b.name if case.researcher_b else case.field_query)}; "
                    f"such topics are not jointly evidenced."
                ),
                evidence_refs=refs,
            )
        ]

        intersections: list[SystemIntersection] = []
        if len(scored) >= 2:
            intersections.append(
                SystemIntersection(
                    title=f"Similarity bridge: '{refs[0].title[:60]}' and '{refs[1].title[:60]}'",
                    description=(
                        "The two corpus papers most similar (embedding-wise) to the combined "
                        "researcher inputs are proposed as the basis of a joint direction."
                    ),
                    research_gap=gaps[0].description,
                    evidence_refs=refs,
                )
            )
        if not intersections:
            intersections.append(
                SystemIntersection(
                    title=f"Embedding top-candidate for {case.researcher_a.name}",
                    description="Low corpus similarity overall; direction requires human review.",
                    evidence_refs=refs or [SystemRef(title=p.title, paper_id=p.paper_id) for _, p in scored[:1]],
                )
            )

        hypotheses = [
            SystemHypothesis(
                text=(
                    "The most embedding-similar papers jointly cover the researchers' interests; "
                    "combining their methods warrants empirical evaluation."
                ),
                evidence_refs=refs,
            )
        ]
        return SystemOutput(system=self.name, kind=self.kind, gaps=gaps,
                            intersections=intersections, hypotheses=hypotheses,
                            known_context_titles=[p.title for p in case.source_papers])


# ---------------------------------------------------------------------------
# LLM-only baseline (no retrieval / no evidence machinery)
# ---------------------------------------------------------------------------

class LLMOnlyBaseline(BaseSystem):
    name = "llm_only"
    kind = "baseline"

    async def run(self, case: EvaluationCase) -> SystemOutput:
        from app.providers.llm.factory import get_llm_provider

        def profile(r: ResearcherInput | None) -> dict[str, Any]:
            return {"name": r.name, "bio": r.bio, "topics": r.topics, "methods": r.methods} if r else {}

        input_data = {
            "researcher_a": profile(case.researcher_a),
            "researcher_b": profile(case.researcher_b),
            "field_query": case.field_query,
        }
        llm = get_llm_provider()
        raw = await llm.structured_generate(
            task="evaluation_llm_only",
            input_data=input_data,
            schema_name="eval_llm_only",
            schema=LLM_ONLY_SCHEMA,
            temperature=0.2,
            max_tokens=1500,
            seed=self.seed,
        )
        gaps = [SystemGap(description=g.get("description", "")) for g in raw.get("gaps", [])]
        intersections = [
            SystemIntersection(
                title=ix.get("title", ""),
                description=ix.get("description", ""),
                evidence_refs=[],
            )
            for ix in raw.get("intersections", [])
        ]
        hypotheses = [
            SystemHypothesis(text=h.get("text", ""), evidence_refs=[]) for h in raw.get("hypotheses", [])
        ]
        # LLM-only has no retrieval context: any recalled title must resolve
        # against the corpus to be considered valid.
        return SystemOutput(
            system=self.name,
            kind=self.kind,
            gaps=gaps,
            intersections=intersections,
            hypotheses=hypotheses,
            known_context_titles=[],
        )


# ---------------------------------------------------------------------------
# ResearchCollision agentic pipeline baseline
# ---------------------------------------------------------------------------

class AgenticPipelineBaseline(BaseSystem):
    """Runs the real DiscoveryPipeline in an isolated temp database.

    Uses whatever providers are configured (mock by offline default). Queries
    the stored workspace afterwards and normalizes gaps / intersections /
    hypotheses / evidence into a SystemOutput. Retrieved papers become the
    citation-validity universe.
    """

    name = "pipeline"
    kind = "system"
    max_papers = 6

    async def run(self, case: EvaluationCase) -> SystemOutput:
        with tempfile.TemporaryDirectory(prefix="eval_pipeline_") as td:
            from app.db.database import create_db_engine, make_session_factory

            engine = create_db_engine(f"sqlite:///{Path(td) / 'eval.db'}")
            import app.db.models  # noqa: F401  register all tables
            Base.metadata.create_all(bind=engine)
            factory = make_session_factory(engine)
            try:
                with factory() as db:
                    out = await self._run_in_session(db, engine, case)
                return out
            finally:
                engine.dispose()

    async def _run_in_session(self, db, engine, case: EvaluationCase) -> SystemOutput:
        user = User(
            email=f"eval-{uuid.uuid4().hex[:12]}@researchcollision.local",
            password_hash="x",
            name="Evaluation Runner",
        )
        db.add(user)
        db.flush()
        ws = Workspace(user_id=user.id, name=f"eval-case-{case.case_id}")
        db.add(ws)
        db.flush()

        ra = Researcher(
            name=case.researcher_a.name,
            affiliation=case.researcher_a.affiliation,
            bio=case.researcher_a.bio,
        )
        db.add(ra)
        db.flush()

        if case.researcher_b:
            rb = Researcher(
                name=case.researcher_b.name,
                affiliation=case.researcher_b.affiliation,
                bio=case.researcher_b.bio,
            )
        else:
            rb = None
        if rb:
            db.add(rb)
            db.flush()

        job = ResearchJob(
            workspace_id=ws.id,
            user_id=user.id,
            job_type="discovery",
            config={
                "mode": "normal",
                "researcher_a_id": ra.id,
                "researcher_b_id": rb.id if rb else None,
                "field_query": case.field_query,
                "max_papers": self.max_papers,
                "generate_hypotheses": True,
                "write_paper_draft": False,
            },
            status=JobStatus.PENDING.value,
        )
        db.add(job)
        db.commit()

        import app.workers.tasks.discovery_pipeline as dp

        pipeline = dp.DiscoveryPipeline(db, job, seed=self.seed)
        status = await pipeline.run()
        if status != JobStatus.COMPLETED.value:
            raise RuntimeError(
                f"DiscoveryPipeline ended with status {status}: {job.error_message or 'no message'}"
            )
        return self._collect(db, ws.id)

    def _collect(self, db, workspace_id: str) -> SystemOutput:
        output = SystemOutput(system=self.name, kind=self.kind)

        evidence_rows = list(
            db.scalars(select(Evidence).where(Evidence.workspace_id == workspace_id))
        )
        ev_by_id = {ev.id: ev for ev in evidence_rows}

        def ref_for(ev: Evidence) -> SystemRef:
            paper = ev.paper
            title = (paper.title if paper else None) or ev.source_title or ""
            paper_id = paper.provider_id if paper and paper.source_provider == "mock" else None
            return SystemRef(title=title, paper_id=paper_id)

        def refs_for_evidence_ids(ids) -> list[SystemRef]:
            refs: list[SystemRef] = []
            for eid in dict.fromkeys(ids):
                ev = ev_by_id.get(eid)
                if ev is not None:
                    refs.append(ref_for(ev))
            return refs

        retrieved = list(db.scalars(select(Paper)))
        output.known_context_titles = [p.title for p in retrieved]

        for g in db.scalars(
            select(ResearchGap).where(ResearchGap.workspace_id == workspace_id)
        ):
            ev_ids = list(
                db.scalars(
                    select(ResearchGapEvidence.evidence_id).where(ResearchGapEvidence.gap_id == g.id)
                )
            )
            output.gaps.append(
                SystemGap(description=g.description, evidence_refs=refs_for_evidence_ids(ev_ids))
            )

        ix_ids = {
            ix.id: ix
            for ix in db.scalars(
                select(ResearchIntersection).where(ResearchIntersection.workspace_id == workspace_id)
            )
        }
        ix_evidence: dict[str, list[str]] = {}
        for link in db.scalars(
            select(IntersectionEvidence).where(IntersectionEvidence.intersection_id.in_(list(ix_ids) or [None]))
        ):
            ix_evidence.setdefault(link.intersection_id, []).append(link.evidence_id)

        for ix in ix_ids.values():
            output.intersections.append(
                SystemIntersection(
                    title=ix.title,
                    description=ix.description,
                    research_gap=ix.gap_description,
                    evidence_refs=refs_for_evidence_ids(ix_evidence.get(ix.id, [])),
                )
            )

        for hyp in db.scalars(
            select(Hypothesis).where(Hypothesis.workspace_id == workspace_id)
        ):
            exp = db.scalar(select(Experiment).where(Experiment.hypothesis_id == hyp.id))
            experiment: dict[str, Any] = {}
            if exp is not None:
                for f in (
                    "baseline", "proposed_approach", "dataset", "training_setup",
                    "evaluation_setup", "metrics", "ablations", "expected_outcomes",
                    "failure_conditions",
                ):
                    experiment[f] = getattr(exp, f)
            ix_refs: list[SystemRef] = []
            if hyp.intersection_id in ix_ids:
                ix_refs = refs_for_evidence_ids(ix_evidence.get(hyp.intersection_id, []))
            output.hypotheses.append(
                SystemHypothesis(text=hyp.hypothesis_text, evidence_refs=ix_refs, experiment=experiment)
            )
            if "ablations" in experiment and not isinstance(experiment["ablations"], list):
                try:
                    experiment["ablations"] = list(experiment["ablations"])
                except TypeError:
                    experiment["ablations"] = []

        return output


_SYSTEM_CLASSES: dict[str, type[BaseSystem]] = {
    "keyword": KeywordOverlapBaseline,
    "embedding": EmbeddingSimilarityBaseline,
    "llm_only": LLMOnlyBaseline,
    "pipeline": AgenticPipelineBaseline,
}

DEFAULT_SYSTEMS = ["keyword", "embedding", "llm_only", "pipeline"]


def get_system(name: str, seed: int | None = None) -> BaseSystem:
    """Return a fresh system instance for ``name`` carrying the given seed.

    Instances are stateless per call, so constructing a new one is cheap and
    guarantees no seed/mutable state leaks across cases or seeds.
    """
    if name not in _SYSTEM_CLASSES:
        raise KeyError(
            f"Unknown system {name!r}. Available: {sorted(_SYSTEM_CLASSES)}"
        )
    return _SYSTEM_CLASSES[name](seed=seed)
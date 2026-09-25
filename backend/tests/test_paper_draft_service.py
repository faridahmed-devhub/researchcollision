"""PaperDraftService: grounded storage/retrieval via the report system."""
from __future__ import annotations

from sqlalchemy import select

from app.core.constants import PAPER_DRAFT_FORMAT, DiscoveryMode, JobStatus
from app.core.exceptions import NotFoundError
from app.db.models import (
    Evidence,
    Experiment,
    GeneratedReport,
    Hypothesis,
    Paper,
    ResearchJob,
    User,
    Workspace,
)
from app.db.models.paper import normalize_title
from app.db.models.researcher import Researcher
from app.services.intersection_service import IntersectionService
from app.services.paper_draft_service import PaperDraftService


def _seed(db_session) -> dict:
    user = User(email="pd@t.dev", password_hash="x", name="U")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="Paper WS")
    db_session.add(ws)
    db_session.flush()

    paper = db_session.query(Paper).filter(Paper.source_provider == "mock").first()
    if paper is None:
        paper = Paper(
            title="Grounded Source Paper",
            normalized_title_hash=normalize_title("Grounded Source Paper"),
            source_provider="mock",
            provider_id="mock:paper-draft-test",
            venue="Test Journal",
            publication_year=2024,
        )
        db_session.add(paper)
        db_session.flush()
        db_session.flush()

    ev = Evidence(
        workspace_id=ws.id,
        claim="A verified claim from the source paper.",
        paper_id=paper.id,
        source_title=paper.title,
        status="INFERRED",
    )
    db_session.add(ev)
    db_session.flush()

    ra = Researcher(name="Researcher A", workspace_id=ws.id)
    rb = Researcher(name="Researcher B", workspace_id=ws.id)
    db_session.add_all([ra, rb])
    db_session.flush()

    svc = IntersectionService(db_session)
    ix = svc.create(
        workspace_id=ws.id,
        job_id=None,
        candidate={
            "title": "Hybrid Neuro-Symbolic Downscaling",
            "description": "Merge ML and climate expertise.",
            "research_gap": "No prior synthesis of these streams.",
            "complementary_expertise": "ML + Earth systems",
            "evidence_ids": [ev.id],
            "novelty_confidence": 0.8,
            "feasibility_confidence": 0.7,
        },
        researcher_a_id=ra.id,
        researcher_b_id=rb.id,
        research_gap_id=None,
        mode=DiscoveryMode.NORMAL,
    )
    hyp = Hypothesis(
        workspace_id=ws.id,
        intersection_id=ix.id,
        research_question="What happens when we combine the streams?",
        hypothesis_text="Hybrid outperforms baselines.",
        motivation="From the evidence.",
        method="Hybrid pipeline.",
        dataset="CMIP6",
        baseline="U-Net",
        metrics="RMSE",
    )
    db_session.add(hyp)
    db_session.flush()
    db_session.add(
        Experiment(
            hypothesis_id=hyp.id,
            proposed_approach="Train hybrid.",
            dataset="CMIP6",
            dataset_status="INFERRED",
            ablations=["drop symbolic"],
        )
    )

    job = ResearchJob(
        workspace_id=ws.id,
        user_id=user.id,
        job_type="discovery",
        config={"mode": "normal"},
        status=JobStatus.COMPLETED.value,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(ix)
    return {"user": user, "ws": ws, "ev": ev, "ix": ix, "job": job, "paper": paper, "hyp": hyp}


async def test_generate_for_job_stores_report_and_grounds_evidence(db_session):
    s = _seed(db_session)
    out = await PaperDraftService(db_session).generate_for_job(s["job"])

    assert out.job_id == s["job"].id
    assert out.report_id
    report = db_session.get(GeneratedReport, out.report_id)
    assert report is not None
    assert report.format == PAPER_DRAFT_FORMAT
    assert report.job_id == s["job"].id
    assert report.workspace_id == s["ws"].id

    assert {e.evidence_id for e in out.evidence} == {s["ev"].id}
    assert out.citations, "citations should resolve from the linked paper"
    assert "Grounded Source Paper" in out.citations[0].text
    assert out.citations[0].status == "INFERRED"
    assert "EXPECTED / PROPOSED" in out.expected_results
    assert "NOT EMPIRICALLY VALIDATED" in out.expected_results_label


async def test_generate_for_job_is_idempotent_per_job(db_session):
    s = _seed(db_session)
    svc = PaperDraftService(db_session)
    first = await svc.generate_for_job(s["job"])
    second = await svc.generate_for_job(s["job"])

    rows = list(
        db_session.scalars(
            select(GeneratedReport).where(
                GeneratedReport.job_id == s["job"].id,
                GeneratedReport.format == PAPER_DRAFT_FORMAT,
            )
        )
    )
    assert len(rows) == 1, "rerunning a job must replace, not duplicate, its draft"
    assert rows[0].id == second.report_id != first.report_id
    assert db_session.get(GeneratedReport, first.report_id) is None


def test_get_draft_raises_not_found_when_missing(db_session):
    s = _seed(db_session)
    try:
        PaperDraftService(db_session).get_draft(s["job"])
        raise AssertionError("expected NotFoundError")
    except NotFoundError:
        pass


async def test_get_draft_returns_stored_out(db_session):
    s = _seed(db_session)
    svc = PaperDraftService(db_session)
    generated = await svc.generate_for_job(s["job"])
    fetched = svc.get_draft(s["job"])
    assert fetched.report_id == generated.report_id
    assert fetched.title == generated.title
    assert fetched.created_at == generated.created_at
    assert [e.evidence_id for e in fetched.evidence] == [s["ev"].id]
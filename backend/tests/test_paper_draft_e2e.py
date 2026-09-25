"""End-to-end: a mock discovery run produces a stored, grounded paper draft."""
from __future__ import annotations

from sqlalchemy import select

from app.core.constants import JobStatus
from app.db.models import (
    Evidence,
    GeneratedReport,
    ResearchJob,
    User,
    Workspace,
)
from app.db.models.paper import normalize_title
from app.db.models.paper import Paper
from app.db.models.researcher import Researcher


async def test_mock_discovery_pipeline_writes_paper_draft(db_session):
    user = User(email="e2e@t.dev", password_hash="x", name="E2E")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="E2E WS")
    db_session.add(ws)
    db_session.flush()

    ra = Researcher(name="Dr. Priya Raghavan", affiliation="Lattice Dynamics Lab")
    db_session.add(ra)
    db_session.flush()

    job = ResearchJob(
        workspace_id=ws.id,
        user_id=user.id,
        job_type="discovery",
        config={
            "mode": "normal",
            "researcher_a_id": ra.id,
            "field_query": "Machine Learning for Healthcare",
            "max_papers": 8,
            "generate_hypotheses": True,
        },
        status=JobStatus.PENDING.value,
    )
    db_session.add(job)
    db_session.commit()

    import app.workers.tasks.discovery_pipeline as dp

    pipeline = dp.DiscoveryPipeline(db_session, job)
    status = await pipeline.run()

    assert status == JobStatus.COMPLETED.value, job.error_message
    assert job.result_summary.get("paper_draft"), "pipeline must store a paper draft"

    report_id = job.result_summary["paper_draft"]
    report = db_session.get(GeneratedReport, report_id)
    assert report is not None
    assert report.format == "paper_draft"
    assert report.job_id == job.id

    from app.services.paper_draft_service import PaperDraftService

    out = PaperDraftService(db_session).get_draft(job)
    allowed = set(
        db_session.scalars(
            select(Evidence.id).where(Evidence.workspace_id == ws.id)
        ).all()
    )
    assert out.evidence, "draft should be grounded in workspace evidence"
    assert {e.evidence_id for e in out.evidence} <= allowed, (
        "draft evidence must belong to the job's workspace"
    )
    for c in out.citations:
        assert c.evidence_id in allowed
    assert "NOT EMPIRICALLY VALIDATED" in out.expected_results_label
    assert "EXPECTED / PROPOSED" in out.expected_results


# -- re-run safety: an on-demand POST for an already-completed job replaces the draft

async def test_pipeline_rerun_replaces_draft_only_for_that_job(db_session):
    user = User(email="e2e2@t.dev", password_hash="x", name="E2E 2")
    db_session.add(user)
    db_session.flush()

    ws = Workspace(user_id=user.id, name="E2E2 WS")
    ds = db_session
    ds.add(ws)
    ds.flush()

    paper = Paper(
        title="Rerun Source",
        normalized_title_hash=normalize_title("Rerun Source"),
        source_provider="mock",
        provider_id="mock:e2e2",
    )
    ds.add(paper)
    ds.flush()
    ev = Evidence(workspace_id=ws.id, claim="rerun claim", paper_id=paper.id, status="VERIFIED")
    ds.add(ev)
    ds.flush()

    job = ResearchJob(
        workspace_id=ws.id, user_id=user.id, job_type="discovery",
        config={"mode": "normal"}, status=JobStatus.COMPLETED.value,
    )
    ds.add(job)
    ds.commit()

    from app.core.constants import DiscoveryMode
    from app.db.models import Researcher as R2
    from app.services.intersection_service import IntersectionService

    ra = R2(name="R Alpha")
    rb = R2(name="R Beta")
    ds.add_all([ra, rb])
    ds.flush()
    IntersectionService(ds).create(
        workspace_id=ws.id,
        job_id=job.id,
        candidate={
            "title": "Rerun Intersection", "description": "d",
            "research_gap": "g", "evidence_ids": [ev.id],
        },
        researcher_a_id=ra.id,
        researcher_b_id=rb.id,
        research_gap_id=None,
        mode=DiscoveryMode.NORMAL,
    )
    ds.commit()

    from app.services.paper_draft_service import PaperDraftService

    svc = PaperDraftService(ds)
    first = await svc.generate_for_job(job)
    second = await svc.generate_for_job(job)

    from sqlalchemy import select

    rows = list(
        ds.scalars(
            select(GeneratedReport).where(
                GeneratedReport.job_id == job.id, GeneratedReport.format == "paper_draft"
            )
        )
    )
    assert len(rows) == 1
    assert rows[0].id == second.report_id
    assert first.report_id != second.report_id
"""Regression tests: detect_gaps must not erase other jobs' gaps."""
from __future__ import annotations

from sqlalchemy import select

import app.workers.tasks.discovery_pipeline as dp
from app.core.constants import JobStatus
from app.db.models import Evidence, ResearchGap, ResearchJob, User, Workspace
from app.providers.llm.base import GapCandidate, GapDetectionResult


async def test_detect_gaps_preserves_other_jobs_output(db_session, monkeypatch):
    user = User(email="gap@t.dev", password_hash="x", name="U")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="WS")
    db_session.add(ws)
    db_session.flush()

    job1 = ResearchJob(
        workspace_id=ws.id, user_id=user.id, job_type="discovery",
        config={"mode": "normal"}, status=JobStatus.COMPLETED.value,
    )
    job2 = ResearchJob(
        workspace_id=ws.id, user_id=user.id, job_type="discovery",
        config={"mode": "normal"}, status=JobStatus.RUNNING.value,
    )
    db_session.add_all([job1, job2])
    db_session.flush()

    ev = Evidence(workspace_id=ws.id, claim="c", status="INFERRED")
    db_session.add(ev)
    db_session.flush()

    other_job_gap = ResearchGap(
        workspace_id=ws.id, job_id=job1.id, description="gap from an earlier job",
        gap_type="future_work_opportunity", confidence=0.5, status="INFERRED",
    )
    db_session.add(other_job_gap)
    db_session.commit()

    class FakeGapAgent:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003 – pipeline ctor args
            pass

        async def detect(self, paper_analyses):  # noqa: ARG002
            return GapDetectionResult(
                gaps=[
                    GapCandidate(
                        description="newly detected gap",
                        gap_type="explicit_limitation",
                        confidence=0.7,
                        evidence_ids=[ev.id],
                    )
                ]
            )

    monkeypatch.setattr(dp, "GapAgent", FakeGapAgent)

    pipeline = dp.DiscoveryPipeline(db_session, job2)
    pipeline._paper_analyses = []
    await pipeline.step_detect_gaps()

    rows = list(db_session.scalars(select(ResearchGap).order_by(ResearchGap.created_at)))
    assert len(rows) == 2, "gaps from another job must survive regeneration"
    descriptions = {g.description for g in rows}
    assert descriptions == {"gap from an earlier job", "newly detected gap"}
    new_gap = next(g for g in rows if g.description == "newly detected gap")
    assert new_gap.job_id == job2.id


async def test_detect_gaps_replaces_only_this_job_previous_gaps(db_session, monkeypatch):
    user = User(email="gap2@t.dev", password_hash="x", name="U")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="WS")
    db_session.add(ws)
    db_session.flush()

    job = ResearchJob(
        workspace_id=ws.id, user_id=user.id, job_type="discovery",
        config={"mode": "normal"}, status=JobStatus.RUNNING.value,
    )
    db_session.add(job)
    db_session.commit()

    ev = Evidence(workspace_id=ws.id, claim="c", status="INFERRED")
    db_session.add(ev)
    db_session.flush()

    old_row = ResearchGap(
        workspace_id=ws.id, job_id=job.id, description="stale previous run",
        gap_type="methodological_limitation", confidence=0.4, status="INFERRED",
    )
    db_session.add(old_row)
    db_session.commit()
    old_row_id = old_row.id

    class FakeGapAgent:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003 – pipeline ctor args
            pass

        async def detect(self, paper_analyses):  # noqa: ARG002
            return GapDetectionResult(
                gaps=[
                    GapCandidate(
                        description="refreshed gap", gap_type="domain_transfer_opportunity",
                        confidence=0.9, evidence_ids=[ev.id],
                    )
                ]
            )

    monkeypatch.setattr(dp, "GapAgent", FakeGapAgent)

    pipeline = dp.DiscoveryPipeline(db_session, job)
    pipeline._paper_analyses = []
    await pipeline.step_detect_gaps()

    db_session.expire_all()
    assert db_session.get(ResearchGap, old_row_id) is None
    rows = list(db_session.scalars(select(ResearchGap)))
    assert len(rows) == 1
    assert rows[0].description == "refreshed gap"
    assert rows[0].job_id == job.id
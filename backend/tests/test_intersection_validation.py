"""Regression tests: intersections only link evidence owned by the workspace."""
from __future__ import annotations

from app.core.constants import DiscoveryMode
from app.db.models import Evidence, Paper, Researcher, User, Workspace
from app.db.models.paper import normalize_title
from app.services.intersection_service import IntersectionService


def _seed(user, db_session):
    ws_a = Workspace(user_id=user.id, name="WS A")
    ws_b = Workspace(user_id=user.id, name="WS B")
    db_session.add_all([ws_a, ws_b])
    db_session.flush()

    paper = db_session.query(Paper).filter(Paper.source_provider == "mock").first()
    if paper is None:
        paper = Paper(
            title="Intersection Test Paper",
            normalized_title_hash=normalize_title("Intersection Test Paper"),
            source_provider="mock",
            provider_id="mock:ix-test",
        )
        db_session.add(paper)
        db_session.flush()

    ev_own = Evidence(
        workspace_id=ws_a.id, claim="own", evidence_text="text",
        paper_id=paper.id, status="INFERRED",
    )
    ev_foreign = Evidence(
        workspace_id=ws_b.id, claim="foreign", evidence_text="text",
        paper_id=paper.id, status="INFERRED",
    )
    db_session.add_all([ev_own, ev_foreign])
    db_session.flush()

    ra = Researcher(name="Researcher A")
    rb = Researcher(name="Researcher B")
    db_session.add_all([ra, rb])
    db_session.flush()
    return ws_a, ws_b, ev_own, ev_foreign, ra, rb


def test_intersection_ignores_foreign_and_bogus_evidence(db_session):
    user = User(email="ix@t.dev", password_hash="x", name="U")
    db_session.add(user)
    db_session.flush()
    ws_a, _ws_b, ev_own, ev_foreign, ra, rb = _seed(user, db_session)

    svc = IntersectionService(db_session)
    ix = svc.create(
        workspace_id=ws_a.id,
        job_id=None,
        candidate={
            "title": "A Novel Intersection",
            "description": "desc",
            "evidence_ids": [ev_own.id, ev_foreign.id, "not-a-real-evidence"],
        },
        researcher_a_id=ra.id,
        researcher_b_id=rb.id,
        research_gap_id=None,
        mode=DiscoveryMode.NORMAL,
    )
    db_session.commit()

    assert svc.evidence_ids_for(ix.id) == [ev_own.id]
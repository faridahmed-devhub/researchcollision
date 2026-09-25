"""Paper draft API endpoints: retrieve, regenerate, export, authorization."""
from __future__ import annotations

from app.core.constants import JobStatus
from app.db.models import ResearchJob, User, Workspace


def _seed_job_with_intersection(db_session, ac) -> tuple[str, str]:
    """Create user/workspace/researchers/evidence/intersection + a completed job."""
    from app.core.constants import DiscoveryMode
    from app.db.models import (
        Evidence,
        Paper,
        Researcher,
    )
    from app.db.models.paper import normalize_title
    from app.services.intersection_service import IntersectionService

    ws = Workspace(user_id=ac.user_id, name="API WS")
    db_session.add(ws)
    db_session.flush()

    paper = Paper(
        title="API Source Paper",
        normalized_title_hash=normalize_title("API Source Paper"),
        source_provider="mock",
        provider_id="mock:api-draft-test",
        venue="Venue X",
    )
    db_session.add(paper)
    db_session.flush()

    ev = Evidence(
        workspace_id=ws.id, claim="API verified claim", paper_id=paper.id,
        source_title=paper.title, status="VERIFIED",
    )
    db_session.add(ev)
    db_session.flush()

    ra = Researcher(name="R A", workspace_id=ws.id)
    rb = Researcher(name="R B", workspace_id=ws.id)
    db_session.add_all([ra, rb])
    db_session.flush()

    ix = IntersectionService(db_session).create(
        workspace_id=ws.id,
        job_id=None,
        candidate={
            "title": "API Draft Intersection",
            "description": "desc",
            "research_gap": "gap",
            "complementary_expertise": "expertise",
            "evidence_ids": [ev.id],
        },
        researcher_a_id=ra.id,
        researcher_b_id=rb.id,
        research_gap_id=None,
        mode=DiscoveryMode.NORMAL,
    )

    job = ResearchJob(
        workspace_id=ws.id,
        user_id=ac.user_id,
        job_type="discovery",
        config={"mode": "normal"},
        status=JobStatus.COMPLETED.value,
    )
    db_session.add(job)
    db_session.commit()
    return ws.id, job.id


async def test_get_paper_draft_404_before_generation(client, auth, db_session):
    ac = auth
    ws_id, job_id = _seed_job_with_intersection(db_session, ac)
    r = await client.get(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)
    assert r.status_code == 404


async def test_generate_then_retrieve_and_export_markdown(client, auth, db_session):
    ac = auth
    _ws_id, job_id = _seed_job_with_intersection(db_session, ac)

    r = await client.post(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["job_id"] == job_id
    assert data["report_id"]
    assert data["expected_results_label"].endswith("NOT EMPIRICALLY VALIDATED")
    assert [e["evidence_id"] for e in data["evidence"]]
    assert "actual_results" not in data

    r2 = await client.get(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)
    assert r2.status_code == 200
    assert r2.json()["report_id"] == data["report_id"]

    r3 = await client.get(
        f"/api/v1/discovery/jobs/{job_id}/paper-draft/export?format=markdown",
        headers=ac.headers,
    )
    assert r3.status_code == 200
    assert r3.headers["content-type"].startswith("text/markdown")
    assert 'attachment; filename="' in r3.headers["content-disposition"]
    assert "## Abstract" in r3.text


async def test_export_pdf_succeeds(client, auth, db_session):
    ac = auth
    _ws_id, job_id = _seed_job_with_intersection(db_session, ac)
    await client.post(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)
    r = await client.get(
        f"/api/v1/discovery/jobs/{job_id}/paper-draft/export?format=pdf", headers=ac.headers
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF"


async def test_export_rejects_unknown_format(client, auth, db_session):
    ac = auth
    _ws_id, job_id = _seed_job_with_intersection(db_session, ac)
    await client.post(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)
    r = await client.get(
        f"/api/v1/discovery/jobs/{job_id}/paper-draft/export?format=docx", headers=ac.headers
    )
    assert r.status_code == 422


async def test_other_user_cannot_read_job(client, auth, db_session):
    ac = auth
    _ws_id, job_id = _seed_job_with_intersection(db_session, ac)
    await client.post(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=ac.headers)

    other = User(email="other@t.dev", password_hash="x", name="Other")
    db_session.add(other)
    db_session.commit()

    from app.core.security import create_access_token

    token = create_access_token(other.id)
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get(f"/api/v1/discovery/jobs/{job_id}/paper-draft", headers=headers)
    assert r.status_code == 404  # no existence leak
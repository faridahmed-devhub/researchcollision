"""Regression tests: discovery job API (mode vocabulary, field_query) + export auth."""
from __future__ import annotations


async def test_create_job_with_field_query_and_serendipity(auth, client):
    ws = await auth.create_workspace()
    r = await client.post(
        "/api/v1/discovery/jobs",
        json={
            "workspace_id": ws["id"],
            "researcher_a_id": "res-abc",
            "field_query": "climate science",
            "mode": "serendipity",
            "max_papers": 8,
        },
        headers=auth.headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["job_type"] == "discovery"
    assert data["config"]["field_query"] == "climate science"
    assert data["config"]["mode"] == "serendipity"
    assert data["config"]["researcher_b_id"] is None


async def test_create_job_rejects_legacy_mode_names(auth, client):
    ws = await auth.create_workspace()
    for bad in ("exploratory", "targeted"):
        r = await client.post(
            "/api/v1/discovery/jobs",
            json={"workspace_id": ws["id"], "researcher_a_id": "r", "mode": bad},
            headers=auth.headers,
        )
        assert r.status_code == 422, f"mode={bad}: {r.text}"


async def test_export_requires_authentication(client, auth):
    ws = await auth.create_workspace()
    anon = await client.get(f"/api/v1/workspaces/{ws['id']}/export")
    assert anon.status_code in (401, 403)

    authed = await client.get(f"/api/v1/workspaces/{ws['id']}/export", headers=auth.headers)
    assert authed.status_code == 200
    assert "intersections" in authed.json()
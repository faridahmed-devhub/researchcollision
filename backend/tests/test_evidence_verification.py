"""Regression tests: synthetic evidence can never reach VERIFIED."""
from __future__ import annotations

from types import SimpleNamespace

from app.agents.verification_agent import VerificationAgent
from app.core.constants import EvidenceStatus

QUOTE = "We demonstrate a novel transformer baseline for clinical time series."
ABSTRACT = (
    QUOTE
    + " Results show consistent gains over prior state-of-the-art models."
)


def _ev(ev_id, paper_id, text, status):
    return SimpleNamespace(id=ev_id, paper_id=paper_id, evidence_text=text, status=status)


def _paper(synthetic: bool):
    return SimpleNamespace(abstract=ABSTRACT, is_synthetic=synthetic)


def test_real_paper_quote_match_still_verifies():
    ev = _ev("e1", "p1", QUOTE, EvidenceStatus.UNVERIFIED.value)
    updates = VerificationAgent().verify_evidence(
        evidence_rows=[ev], papers_by_id={"p1": _paper(synthetic=False)}
    )
    assert updates == [
        {"evidence_id": "e1", "status": EvidenceStatus.VERIFIED.value, "reason": "Quote matched stored abstract."}
    ]


def test_synthetic_paper_never_verified():
    ev = _ev("e1", "p1", QUOTE, EvidenceStatus.UNVERIFIED.value)
    updates = VerificationAgent().verify_evidence(
        evidence_rows=[ev], papers_by_id={"p1": _paper(synthetic=True)}
    )
    assert updates == []


def test_synthetic_paper_downgrades_existing_verified():
    ev = _ev("e1", "p1", QUOTE, EvidenceStatus.VERIFIED.value)
    updates = VerificationAgent().verify_evidence(
        evidence_rows=[ev], papers_by_id={"p1": _paper(synthetic=True)}
    )
    assert len(updates) == 1
    assert updates[0]["status"] == EvidenceStatus.INFERRED.value


def test_synthetic_unverified_without_quote_stays_unverified():
    ev = _ev("e1", "p1", "short", EvidenceStatus.UNVERIFIED.value)
    updates = VerificationAgent().verify_evidence(
        evidence_rows=[ev], papers_by_id={"p1": _paper(synthetic=True)}
    )
    assert updates == []


def test_run_verification_service_no_verified_for_synthetic(db_session):
    from app.db.models import Evidence, Paper, User, Workspace
    from app.db.models.paper import normalize_title
    from app.services.evidence_service import EvidenceService

    user = User(email="u@t.dev", password_hash="x", name="U")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="WS")
    db_session.add(ws)
    db_session.flush()

    paper = Paper(
        title="Synthetic Clinical Time Series Paper",
        normalized_title_hash=normalize_title("Synthetic Clinical Time Series Paper"),
        abstract=ABSTRACT,
        source_provider="mock",
        provider_id="mock:synth-1",
        is_synthetic=True,
    )
    db_session.add(paper)
    db_session.flush()

    ev = Evidence(
        workspace_id=ws.id,
        claim="Synthetic paper reports novel findings.",
        evidence_text=QUOTE,
        paper_id=paper.id,
        status=EvidenceStatus.UNVERIFIED.value,
    )
    db_session.add(ev)
    db_session.commit()

    applied = EvidenceService(db_session).run_verification(ws.id)
    assert all(u["status"] != EvidenceStatus.VERIFIED.value for u in applied)
    db_session.expire_all()
    assert db_session.get(Evidence, ev.id).status == EvidenceStatus.UNVERIFIED.value
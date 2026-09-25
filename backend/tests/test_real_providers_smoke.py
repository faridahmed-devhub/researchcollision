"""Live-provider smoke tests (Phase 3 real-provider validation).

These tests are SKIPPED unless the operator explicitly opts in:

    set RUN_REAL_PROVIDER_TESTS=1
    set OPENROUTER_API_KEY=...          (or OPENAI_API_KEY + OPENAI_BASE_URL)
    set LLM_MODEL=optional-override
    set OPENALEX_EMAIL=you@example.org  (optional, recommended)

They call real external APIs and assert that the pipeline is compatible with
a real LLM and real scholarly literature. Safety rules:
  - No credentials are printed or asserted on (presence is checked only).
  - synthetic (mock) papers are never accepted from a real run.
  - the strict literature chain must exclude the mock provider.
"""
from __future__ import annotations

import os

import pytest

LIVE = os.getenv("RUN_REAL_PROVIDER_TESTS") == "1"

LLM_OK = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
PRIMARY_LIT = os.getenv("LITERATURE_PROVIDER", "openalex").lower()


def _real_llm():
    """Build the configured real LLM provider, bypassing the cached mock settings."""
    if os.getenv("OPENROUTER_API_KEY"):
        from app.providers.llm.openrouter import OpenRouterProvider

        return OpenRouterProvider(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("LLM_MODEL") or None,
        )
    if os.getenv("OPENAI_API_KEY"):
        from app.providers.llm.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL") or None,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
    return None


@pytest.fixture
def real_llm():
    if not (LIVE and LLM_OK):
        pytest.skip("set RUN_REAL_PROVIDER_TESTS=1 and an LLM API key to run")
    return _real_llm()


# --- strict-chain unit test (always runs: pure logic, no network) -----------

def test_strict_literature_chain_excludes_mock_by_default():
    from app.providers.literature.factory import LiteratureProviderChain

    strict = LiteratureProviderChain("openalex", allow_mock=False)
    assert "mock" not in strict.provider_names
    assert strict.provider_names == ["openalex", "semantic_scholar", "crossref", "arxiv"]

    lax = LiteratureProviderChain("openalex", allow_mock=True)
    assert lax.provider_names == ["openalex", "semantic_scholar", "crossref", "arxiv", "mock"]


# --- real LLM agent smoke tests ---------------------------------------------

@pytest.mark.llm_live
@pytest.mark.skipif(not (LIVE and LLM_OK), reason="no real LLM credentials configured")
async def test_profile_agent_real_llm(real_llm):
    from app.agents.profile_agent import ProfileAgent

    agent = ProfileAgent(real_llm)
    dna = await agent.extract_dna(
        "Dr. Elena Vasquez\nResearch Scientist\n\nResearch Interests:\n"
        "- machine learning for healthcare\n- clinical time series\n\n"
        "Publications:\n- 2023: Transformer Models for ICU Monitoring (JAMIA)\n"
        "- 2021: Early Sepsis Prediction (KDD)\n\nSkills:\n- Python, PyTorch, SQL\n"
    )
    assert dna.domains, "real LLM must extract at least one domain"
    assert isinstance(dna.research_interests, list)


@pytest.mark.llm_live
@pytest.mark.skipif(not (LIVE and LLM_OK), reason="no real LLM credentials configured")
async def test_paper_analysis_agent_real_llm(real_llm):
    from app.agents.paper_analysis_agent import PaperAnalysisAgent

    agent = PaperAnalysisAgent(real_llm)
    result = await agent.analyze(
        title="Deep Learning for Predictive Maintenance in Manufacturing",
        abstract=(
            "We study predictive maintenance using deep learning on sensor logs. "
            "A convolutional model reduces unplanned downtime by 18% in a pilot. "
            "Future work addresses domain shift across factories."
        ),
        year=2023,
        venue="IEEE TII",
        domain_hint="industrial AI",
    )
    assert result.research_problem
    assert isinstance(result.limitations, list)


@pytest.mark.llm_live
@pytest.mark.skipif(not (LIVE and LLM_OK), reason="no real LLM credentials configured")
async def test_intersection_agent_real_llm(real_llm):
    from app.agents.intersection_agent import IntersectionAgent
    from app.core.constants import DiscoveryMode

    agent = IntersectionAgent(real_llm)
    result = await agent.discover(
        researcher_a={
            "name": "Dr. A", "affiliation": "Lab A",
            "topics": ["graph neural networks", "drug discovery"],
            "methods": ["GNN", "VAE"],
            "trajectory": {
                "historical_focus": ["molecular modeling"],
                "current_focus": ["graph neural networks"],
                "emerging_interests": ["generative chemistry"],
                "evidence_ids": [],
                "methods_pool": ["GNN", "VAE"],
            },
        },
        researcher_b={
            "name": "Dr. B", "affiliation": "Lab B",
            "topics": ["reinforcement learning", "clinical trials"],
            "methods": ["RL", "bandits"],
            "trajectory": {
                "historical_focus": ["bandit algorithms"],
                "current_focus": ["reinforcement learning"],
                "emerging_interests": ["adaptive trial design"],
                "evidence_ids": [],
                "methods_pool": ["RL", "bandits"],
            },
        },
        gaps=[{
            "description": "Adaptive trial design ignores generative chemistry candidates.",
            "gap_type": "future_work_opportunity",
            "confidence": 0.7,
            "evidence_ids": [],
        }],
        mode=DiscoveryMode.NORMAL,
        max_intersections=3,
    )
    assert result.intersections, "real LLM must propose at least one intersection"
    for cand in result.intersections:
        assert cand.title
        assert 0.0 <= cand.novelty_confidence <= 1.0


@pytest.mark.llm_live
@pytest.mark.skipif(not (LIVE and LLM_OK), reason="no real LLM credentials configured")
async def test_hypothesis_agent_real_llm(real_llm):
    from app.agents.hypothesis_agent import HypothesisAgent

    agent = HypothesisAgent(real_llm)
    draft = await agent.generate_hypothesis(
        intersection={
            "title": "Adaptive generative trial design",
            "description": "Combining generative chemistry with adaptive clinical trial RL.",
            "shared_problem": "Sample-efficient molecular candidate selection in trials.",
            "complementary_expertise": "A: GNN/VAE generative models; B: RL/bandit adaptive design.",
            "research_gap": "No existing adaptive design consumes generative candidates.",
            "evidence_ids": [],
        },
        verified_datasets=["MIMIC-III", "PubChem"],
    )
    assert draft.hypothesis
    assert draft.dataset
    design = await agent.design_experiment(draft.model_dump(), ["MIMIC-III", "PubChem"])
    assert design.proposed_approach
    assert design.dataset_status in {"VERIFIED", "INFERRED"}


@pytest.mark.llm_live
@pytest.mark.skipif(not (LIVE and LLM_OK), reason="no real LLM credentials configured")
async def test_paper_writer_agent_real_llm(real_llm):
    from app.agents.paper_writer_agent import PaperWriterAgent

    agent = PaperWriterAgent(real_llm)
    draft = await agent.generate_draft(
        {
            "intersection": {
                "title": "Adaptive generative trial design",
                "description": "Combining generative chemistry with adaptive clinical trial RL.",
                "gap_description": "No existing adaptive design consumes generative candidates.",
                "researcher_a_name": "Dr. A",
                "researcher_b_name": "Dr. B",
            },
            "hypothesis": {
                "research_question": "Can generative candidates improve adaptive trial efficiency?",
                "hypothesis_text": "Combining the two expertises yields measurable gains.",
                "motivation": "Gap in existing designs.",
                "method": "GNN + RL pipeline.",
                "dataset": "MIMIC-III",
                "baseline": "Standard bandit baselines.",
                "metrics": "fraction of informative arm pulls",
            },
            "experiment": {
                "proposed_approach": "GNN-generated candidates ranked by a bandit policy.",
                "dataset": "MIMIC-III", "dataset_status": "INFERRED",
                "evaluation_setup": "100 simulated trial replications.",
                "ablations": ["GNN removed"],
                "failure_conditions": "no improvement over random candidate selection",
            },
            "evidence": [
                {
                    "id": "ev-real-1",
                    "claim": "Generative models accelerate candidate design.",
                    "status": "VERIFIED",
                    "source_title": "Deep generative chemistry survey",
                }
            ],
        }
    )
    final = agent.finalize(draft, allowed_evidence_ids=["ev-real-1"])
    assert final.title
    assert final.abstract
    assert set(final.evidence_ids) <= {"ev-real-1"}
    assert "NOT EMPIRICALLY VALIDATED" in final.expected_results_label


# --- real literature smoke tests ---------------------------------------------

@pytest.mark.literature_live
@pytest.mark.skipif(not LIVE, reason="set RUN_REAL_PROVIDER_TESTS=1 to run")
async def test_openalex_real_search(db_session):
    from app.providers.literature.factory import LiteratureProviderChain

    chain = LiteratureProviderChain(PRIMARY_LIT, allow_mock=False)
    assert chain.provider_names, "chain must contain at least one real provider"
    assert "mock" not in chain.provider_names, "real run must never include synthetic papers"

    papers, provider = await chain.search("machine learning for healthcare", limit=5)
    assert papers, "real literature search returned no papers"
    assert provider != "mock", "real run must not silently fall back to mock data"
    for p in papers:
        assert p.title
        assert not p.is_synthetic, "synthetic paper surfaced from a real-provider run"


@pytest.mark.literature_live
@pytest.mark.skipif(not LIVE, reason="set RUN_REAL_PROVIDER_TESTS=1 to run")
async def test_openalex_paper_metadata_is_real(db_session):
    from app.providers.literature.openalex import OpenAlexProvider

    provider = OpenAlexProvider()
    papers = await provider.search("graph neural networks drug discovery", limit=3)
    assert papers, "no real papers returned"
    real = [p for p in papers if not p.is_synthetic]
    assert real, "a non-mock provider must only return real papers"
    assert all(p.doi or p.provider_id for p in real), "papers must carry traceable IDs"


# --- full real flow ----------------------------------------------------------

@pytest.mark.slow
@pytest.mark.llm_live
@pytest.mark.literature_live
@pytest.mark.skipif(
    not (LIVE and LLM_OK and PRIMARY_LIT != "mock"),
    reason="needs RUN_REAL_PROVIDER_TESTS=1 + real LLM + real literature",
)
async def test_full_real_flow(db_session):
    """The complete pipeline with a real LLM and real literature."""
    from app.core.constants import JobStatus
    from app.db.models import ResearchJob, User, Workspace
    from app.db.models.researcher import Researcher
    from app.providers.literature.factory import LiteratureProviderChain
    from app.services.literature_service import LiteratureService

    import app.workers.tasks.discovery_pipeline as dp

    user = User(email="live-flow@t.dev", password_hash="x", name="Live Flow")
    db_session.add(user)
    db_session.flush()
    ws = Workspace(user_id=user.id, name="Live Flow WS")
    db_session.add(ws)
    db_session.flush()

    ra = Researcher(name="Dr. Priya Raghavan", affiliation="Health AI Lab")
    db_session.add(ra)
    db_session.flush()

    job = ResearchJob(
        workspace_id=ws.id,
        user_id=user.id,
        job_type="discovery",
        config={
            "mode": "normal",
            "researcher_a_id": ra.id,
            "field_query": "machine learning for healthcare",
            "max_papers": 5,
            "generate_hypotheses": True,
            "write_paper_draft": True,
        },
        status=JobStatus.PENDING.value,
    )
    db_session.add(job)
    db_session.commit()

    pipeline = dp.DiscoveryPipeline(db_session, job)
    pipeline.llm = _real_llm()
    pipeline.literature = LiteratureService(
        LiteratureProviderChain(PRIMARY_LIT, allow_mock=False)
    )

    status = await pipeline.run()
    assert status == JobStatus.COMPLETED.value, job.error_message

    assert job.result_summary.get("papers_analyzed", 0) > 0, (
        "real run must analyze real papers; check literature credentials/network"
    )
    assert job.result_summary.get("paper_draft"), "full real flow must produce a paper draft"
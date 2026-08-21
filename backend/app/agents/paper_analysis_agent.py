"""Paper Analysis Agent — structured extraction per paper."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.providers.llm.base import PaperAnalysis


class PaperAnalysisAgent(BaseAgent):
    name = "paper_analysis_agent"
    prompt_file = "paper_analysis.txt"
    prompt_version = "v1"
    task_name = "paper_analysis"
    output_schema_name = "PaperAnalysis"
    output_model = PaperAnalysis

    async def analyze(
        self,
        *,
        title: str,
        abstract: str,
        year: int | None = None,
        venue: str | None = None,
        domain_hint: str | None = None,
        dataset_hint: str | None = None,
        evidence_id: str | None = None,
    ) -> PaperAnalysis:
        input_data = {
            "title": title,
            "abstract": (abstract or "")[:6000],
            "year": year,
            "venue": venue,
            "domain_hint": domain_hint,
            "dataset_hint": dataset_hint,
            "evidence_id": evidence_id,
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]

"""Gap Agent — evidence-backed research gap detection."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.providers.llm.base import GapDetectionResult


class GapAgent(BaseAgent):
    name = "gap_agent"
    prompt_file = "gap_detection.txt"
    prompt_version = "v1"
    task_name = "gap_detection"
    output_schema_name = "GapDetectionResult"
    output_model = GapDetectionResult

    async def detect(self, paper_analyses: list[dict]) -> GapDetectionResult:
        input_data = {
            "paper_analyses": [
                {
                    "title": pa.get("title", ""),
                    "domain": pa.get("domain"),
                    "limitations": pa.get("limitations", [])[:3],
                    "future_work": pa.get("future_work", [])[:3],
                    "evidence_id": pa.get("evidence_id"),
                }
                for pa in paper_analyses[:40]
            ]
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]

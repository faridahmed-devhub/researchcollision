"""Hypothesis Agent — hypothesis + experiment design generation."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.providers.llm.base import ExperimentDraft, HypothesisDraft


class HypothesisAgent(BaseAgent):
    name = "hypothesis_agent"
    prompt_file = "hypothesis_generation.txt"
    prompt_version = "v1"
    task_name = "hypothesis_generation"
    output_schema_name = "HypothesisDraft"
    output_model = HypothesisDraft

    async def generate_hypothesis(
        self, intersection: dict, verified_datasets: list[str]
    ) -> HypothesisDraft:
        input_data = {
            "intersection": {
                "title": intersection.get("title", ""),
                "description": (intersection.get("description") or "")[:800],
                "shared_problem": intersection.get("shared_problem"),
                "complementary_expertise": intersection.get("complementary_expertise"),
                "research_gap": intersection.get("research_gap"),
                "evidence_ids": intersection.get("evidence_ids", []),
            },
            "verified_datasets": verified_datasets[:10],
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]

    async def design_experiment(
        self, hypothesis: dict, known_datasets: list[str]
    ) -> ExperimentDraft:
        # Switch prompt/schema for the experiment-design step.
        saved = (self.prompt_file, self.task_name, self.output_schema_name, self.output_model)
        self.prompt_file, self.task_name = "experiment_design.txt", "experiment_design"
        self.output_schema_name, self.output_model = "ExperimentDraft", ExperimentDraft
        try:
            result = await self.run_structured({"hypothesis": hypothesis, "verified_datasets": known_datasets})
        finally:
            self.prompt_file, self.task_name, self.output_schema_name, self.output_model = saved
        return result  # type: ignore[return-value]

"""Paper Writer Agent — grounded research-paper draft generation.

Produces a structured *research proposal* draft. Outputs are grounded: the
model receives only stored evidence, the selected intersection, and the
hypothesis/experiment design, and the returned evidence/citation IDs are
clamped to the supplied set before anything is persisted.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.providers.llm.base import PaperDraft


class PaperWriterAgent(BaseAgent):
    name = "paper_writer_agent"
    prompt_file = "paper_writing.txt"
    prompt_version = "v1"
    task_name = "paper_writing"
    output_schema_name = "PaperDraft"
    output_model = PaperDraft

    async def generate_draft(self, context: dict) -> PaperDraft:
        """Build a grounded prompt from backend-supplied context only."""
        input_data = {
            "intersection": {
                "title": (context.get("intersection") or {}).get("title", ""),
                "description": ((context.get("intersection") or {}).get("description") or "")[:800],
                "research_gap": (context.get("intersection") or {}).get("gap_description"),
                "complementary_expertise": (context.get("intersection") or {}).get(
                    "complementary_expertise"
                ),
                "researcher_a": (context.get("intersection") or {}).get("researcher_a_name"),
                "researcher_b": (context.get("intersection") or {}).get("researcher_b_name"),
            },
            "hypothesis": {
                "research_question": (context.get("hypothesis") or {}).get("research_question"),
                "hypothesis_text": (context.get("hypothesis") or {}).get("hypothesis_text"),
                "motivation": (context.get("hypothesis") or {}).get("motivation"),
                "method": (context.get("hypothesis") or {}).get("method"),
                "dataset": (context.get("hypothesis") or {}).get("dataset"),
                "baseline": (context.get("hypothesis") or {}).get("baseline"),
                "metrics": (context.get("hypothesis") or {}).get("metrics"),
            },
            "experiment": {
                "proposed_approach": (context.get("experiment") or {}).get("proposed_approach"),
                "dataset": (context.get("experiment") or {}).get("dataset"),
                "dataset_status": (context.get("experiment") or {}).get("dataset_status"),
                "evaluation_setup": (context.get("experiment") or {}).get("evaluation_setup"),
                "ablations": (context.get("experiment") or {}).get("ablations", []),
                "failure_conditions": (context.get("experiment") or {}).get("failure_conditions"),
            },
            "evidence": [
                {
                    "id": e["id"],
                    "claim": e["claim"],
                    "status": e["status"],
                    "source_title": e.get("source_title"),
                }
                for e in context.get("evidence", [])
            ],
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]

    def finalize(self, draft: PaperDraft, allowed_evidence_ids: list[str]) -> PaperDraft:
        """Clamp every evidence reference to the backend-supplied set.

        The model cannot invent evidence IDs: anything outside `allowed`
        is dropped, preserving statuses that are already embedded in the
        stored evidence themselves.
        """
        allowed = set(allowed_evidence_ids or [])
        data = draft.model_dump()
        data["evidence_ids"] = [e for e in list(dict.fromkeys(draft.evidence_ids)) if e in allowed]
        data["citation_evidence_ids"] = [
            e for e in list(dict.fromkeys(draft.citation_evidence_ids)) if e in allowed
        ]
        return self.output_model.model_validate(data)
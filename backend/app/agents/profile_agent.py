"""Profile Agent — extracts Research DNA from CV text."""
from __future__ import annotations

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.profile import ResearchDNA


class ProfileAgent(BaseAgent):
    name = "profile_agent"
    prompt_file = "profile_extraction.txt"
    prompt_version = "v1"
    task_name = "profile_extraction"
    output_schema_name = "ResearchDNA"
    output_model = ResearchDNA

    async def extract_dna(self, cv_text: str) -> ResearchDNA:
        result: BaseModel = await self.run_structured({"cv_text": cv_text[:20000]})
        return result  # type: ignore[return-value]

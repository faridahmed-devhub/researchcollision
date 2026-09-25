"""Dataset and system-output schemas for the evaluation framework.

The dataset schema captures everything a discovery evaluation needs on the
input side (researcher/domain context, source papers, known topics/methods,
expected research gaps with their supporting evidence) plus the ground-truth
supporting-evidence set used by the automatic grounding metrics.

Two kinds of datasets are supported:

* **Synthetic fixtures** (``is_synthetic=true``, ``provenance="synthetic_fixture"``)
  — clearly labeled test artifacts, never evidence of real-world performance.
* **Real case studies** (``is_synthetic=false``, ``provenance="curated"``) — built
  from publicly traceable scholarly records. For these, every source paper MUST
  carry a DOI or provider id so provenance is auditable, and each annotation
  must declare whether it is ``machine_generated`` or ``independent_human`` via
  ``EvaluationDataset.annotation_provenance``. No annotation may be invented.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

SYNTHETIC_FIXTURE_LABEL = "SYNTHETIC EVALUATION FIXTURE — NOT REAL RESEARCH EVIDENCE"

# v2-only metadata fields added in Phase 3 (always None on frozen v1 cases).
# Kept out of the canonical hash when None so v1 remains byte-identical.
_V2_CASE_FIELDS = (
    "sampling_stratum",
    "candidate_id",
    "selection_utc",
    "inclusion_rationale",
    "citation_gap_rationale",
)
_V2_PAPER_FIELDS = ("retrieved_utc",)

# Provenance vocabulary for annotations. ``none`` means the annotation is
# genuinely unavailable (metrics that depend on it must report n/a).
ANNOTATION_SOURCES = (
    "provider_metadata", "machine_generated", "independent_human", "none", "unspecified"
)


class ResearcherInput(BaseModel):
    """A researcher's public profile as exposed to a discovery system."""

    name: str
    affiliation: str | None = None
    bio: str | None = None
    topics: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    papers: list[str] = Field(
        default_factory=list,
        description="IDs of this researcher's papers within the case source_papers.",
    )


class SourcePaper(BaseModel):
    """A paper record belonging to the evaluation case's reference corpus."""

    paper_id: str
    title: str
    abstract: str = ""
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    topics: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    # --- real-source provenance (required for non-synthetic datasets) ---
    provider_id: str | None = Field(
        default=None, description="Provider-native id, e.g. OpenAlex W123456789."
    )
    source_provider: str | None = Field(
        default=None, description="Where the record was retrieved, e.g. 'openalex'."
    )
    source_url: str | None = Field(
        default=None, description="Resolvable URL (DOI link or provider landing page)."
    )
    citation_count: int | None = None
    evidence_text: str | None = Field(
        default=None,
        description="Verbatim/paraphrased excerpt used as the paper's evidence text (e.g. abstract).",
    )
    retrieved_utc: str | None = Field(
        default=None,
        description="ISO-8601 timestamp of the corpus retrieval of this record (corpus access date).",
    )


class ExpectedGap(BaseModel):
    """A known/expected research gap with supporting evidence references."""

    gap_id: str
    description: str
    gap_type: str = "research_gap"
    evidence_paper_ids: list[str] = Field(default_factory=list)
    annotation_source: str = Field(
        default="unspecified",
        description="One of ANNOTATION_SOURCES: provider_metadata | machine_generated | "
        "independent_human | none | unspecified.",
    )
    source_note: str | None = None


class EvaluationCase(BaseModel):
    case_id: str
    label: str = ""
    evaluation_question: str | None = Field(
        default=None,
        description="The question this case is meant to help answer (recorded at build time).",
    )
    researcher_a: ResearcherInput
    researcher_b: ResearcherInput | None = None
    field_query: str | None = None
    source_papers: list[SourcePaper]
    expected_topics: list[str] = Field(default_factory=list)
    expected_methods: list[str] = Field(default_factory=list)
    expected_gaps: list[ExpectedGap] = Field(default_factory=list)
    expected_evidence_references: list[str] = Field(
        default_factory=list,
        description="Gold supporting-evidence paper_ids a good system should cite.",
    )
    expected_evidence_source: str = Field(
        default="unspecified",
        description="Provenance of expected_evidence_references (ANNOTATION_SOURCES).",
    )
    # --- v2 sampling/metadata (Phase 3; None for v1 pilot cases) ---
    sampling_stratum: str | None = Field(
        default=None,
        description="Stratum group the case was sampled from, e.g. 'inter_cs_ai_life_health'.",
    )
    candidate_id: str | None = Field(
        default=None,
        description="Candidate-population entry this case was selected from (e.g. 'cand_042').",
    )
    selection_utc: str | None = Field(
        default=None,
        description="UTC timestamp of the final sample selection.",
    )
    inclusion_rationale: str | None = Field(
        default=None,
        description="Why this candidate was included (protocol rule + eligibility counts).",
    )
    citation_gap_rationale: str | None = Field(
        default=None,
        description="Citation-gap rationale recorded at selection time (protocol §12; not an output).",
    )

    @model_validator(mode="after")
    def _check_case_references(self) -> EvaluationCase:
        paper_ids = {p.paper_id for p in self.source_papers}
        for ref in self.expected_evidence_references:
            if ref not in paper_ids:
                raise ValueError(
                    f"expected_evidence_references contains unknown paper_id {ref!r} "
                    f"(not among source_papers of {self.case_id})"
                )
        for g in self.expected_gaps:
            for ref in g.evidence_paper_ids:
                if ref not in paper_ids:
                    raise ValueError(
                        f"expected_gaps[{g.gap_id}] references unknown paper {ref!r}"
                    )
        for r in (self.researcher_a, self.researcher_b):
            if r:
                for pid in r.papers:
                    if pid not in paper_ids:
                        raise ValueError(
                            f"researcher {r.name!r} papers contain unknown id {pid!r}"
                        )
        return self

    @property
    def all_expected_paper_ids(self) -> set[str]:
        return {p.paper_id for p in self.source_papers}


class EvaluationDataset(BaseModel):
    dataset_id: str
    version: str = "0.0.0"
    description: str = ""
    provenance: Literal["synthetic_fixture", "manual", "curated"] = "synthetic_fixture"
    is_synthetic: bool = True
    label: str = SYNTHETIC_FIXTURE_LABEL
    created_utc: str | None = None
    source_providers: list[str] = Field(
        default_factory=list,
        description="External providers the real source records came from, e.g. ['openalex'].",
    )
    annotation_provenance: dict[str, str] = Field(
        default_factory=dict,
        description="Map of annotation field -> ANNOTATION_SOURCES value.",
    )
    notes: str | None = None
    content_sha256: str | None = Field(
        default=None,
        description="sha256 of the canonical case content (traceability / version pinning).",
    )
    cases: list[EvaluationCase]

    @model_validator(mode="after")
    def _check_dataset(self) -> EvaluationDataset:
        ids = [c.case_id for c in self.cases]
        if len(set(ids)) != len(ids):
            dupes = {c for c in ids if ids.count(c) > 1}
            raise ValueError(f"Duplicate case_id(s): {sorted(dupes)}")
        for case in self.cases:
            paper_ids = {p.paper_id for p in case.source_papers}
            if len(paper_ids) != len(case.source_papers):
                raise ValueError(f"Duplicate source_paper ids in case {case.case_id}")
        if self.is_synthetic and not self.label.startswith("SYNTHETIC"):
            # canonical label required so fixtures can never be mistaken for real data
            raise ValueError("Synthetic datasets must use a SYNTHETIC-* label")
        if not self.is_synthetic:
            for case in self.cases:
                for p in case.source_papers:
                    if not (p.doi or p.provider_id):
                        raise ValueError(
                            f"Non-synthetic dataset: paper {p.paper_id!r} in {case.case_id} "
                            "has no DOI or provider_id (required for traceability)"
                        )
                    if p.evidence_text is None:
                        raise ValueError(
                            f"Non-synthetic dataset: paper {p.paper_id!r} in {case.case_id} "
                            "has no evidence_text"
                        )
            for field, source in self.annotation_provenance.items():
                if source not in ANNOTATION_SOURCES:
                    raise ValueError(
                        f"annotation_provenance[{field!r}]={source!r} is not one of "
                        f"{ANNOTATION_SOURCES}"
                    )
        return self

    def canonical_case_payload(self) -> list[dict[str, Any]]:
        """Content that defines the dataset identity (for hashing/pinning).

        Phase-3 v2-only metadata fields are dropped when None so the canonical
        payload of frozen v1 pilot cases is byte-identical to the Phase-2 pin
        (v1 immutability is contract, see CASE_SAMPLING_PROTOCOL §3I).
        """
        out: list[dict[str, Any]] = []
        for c in self.cases:
            d = c.model_dump(mode="json")
            for f in _V2_CASE_FIELDS:
                if d.get(f) is None:
                    d.pop(f, None)
            for p in d.get("source_papers", []):
                for f in _V2_PAPER_FIELDS:
                    if p.get(f) is None:
                        p.pop(f, None)
            out.append(d)
        return out

    def compute_content_sha256(self) -> str:
        payload = json.dumps(
            self.canonical_case_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def all_expected_paper_ids(self) -> set[str]:
        return {p.paper_id for c in self.cases for p in c.source_papers}


# ---------------------------------------------------------------------------
# Normalized system outputs (what each baseline/system produces per case)
# ---------------------------------------------------------------------------


class SystemRef(BaseModel):
    """A cited evidence reference. ``paper_id`` is a dataset paper_id when known."""

    title: str
    paper_id: str | None = None
    doi: str | None = None


class SystemGap(BaseModel):
    description: str
    evidence_refs: list[SystemRef] = Field(default_factory=list)


class SystemIntersection(BaseModel):
    title: str
    description: str
    research_gap: str | None = None
    evidence_refs: list[SystemRef] = Field(default_factory=list)


class SystemHypothesis(BaseModel):
    text: str
    evidence_refs: list[SystemRef] = Field(default_factory=list)
    experiment: dict[str, Any] = Field(
        default_factory=dict,
        description="Experiment-design fields when the system produces them.",
    )


class SystemOutput(BaseModel):
    system: str = ""
    kind: str = ""  # 'baseline' | 'system'
    gaps: list[SystemGap] = Field(default_factory=list)
    intersections: list[SystemIntersection] = Field(default_factory=list)
    hypotheses: list[SystemHypothesis] = Field(default_factory=list)
    known_context_titles: list[str] = Field(
        default_factory=list,
        description="Titles of papers the system actually retrieved (citation-validity universe).",
    )

    @property
    def all_refs(self) -> list[SystemRef]:
        """Unique references across all output surfaces (by title / paper id)."""
        seen: set[tuple[str | None, str]] = set()
        out: list[SystemRef] = []
        for r in self._iter_refs():
            key = (r.paper_id, r.title.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out

    def _iter_refs(self):
        for g in self.gaps:
            yield from g.evidence_refs
        for ix in self.intersections:
            yield from ix.evidence_refs
        for h in self.hypotheses:
            yield from h.evidence_refs
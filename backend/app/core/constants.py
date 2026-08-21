"""Domain constants and enums used across the application."""
from __future__ import annotations

from enum import Enum

# Language rules (hallucination guardrails, see docs/agents.md)
NOVELTY_LANGUAGE = "No relevant evidence was found in the searched literature."
UNDEREXPLORED_LANGUAGE = "This appears underexplored based on the retrieved literature."
TRAJECTORY_HEDGE = "The available publications suggest"
COLLAB_LANGUAGE = (
    "appears potentially relevant based on their published research"
)
AI_GENERATED_LABEL = "AI-GENERATED HYPOTHESIS"
SYNTHETIC_DATA_LABEL = "SYNTHETIC DEMO DATA"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    DISCOVERY = "discovery"
    PROFILE_EXTRACTION = "profile_extraction"
    REPORT = "report"


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    SPECULATIVE = "SPECULATIVE"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"


class DiscoveryMode(str, Enum):
    NORMAL = "normal"
    SERENDIPITY = "serendipity"


class GapType(str, Enum):
    EXPLICIT_LIMITATION = "explicit_limitation"
    FUTURE_WORK = "future_work_opportunity"
    MISSING_EVALUATION = "missing_evaluation"
    CONTRADICTORY_FINDINGS = "contradictory_findings"
    METHODOLOGICAL_LIMITATION = "methodological_limitation"
    DOMAIN_TRANSFER = "domain_transfer_opportunity"
    DATASET_LIMITATION = "dataset_limitation"
    REPRODUCIBILITY = "reproducibility_issue"


class ReportFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class CollaborationCategory(str, Enum):
    EXCEPTIONAL = "Exceptional"  # 90-100
    STRONG = "Strong"  # 80-89
    PROMISING = "Promising"  # 70-79
    EXPLORATORY = "Exploratory"  # 60-69
    WEAK = "Weak"  # <60


class DocumentType(str, Enum):
    CV = "cv"
    PAPER = "paper"


class SourceType(str, Enum):
    PAPER_ABSTRACT = "paper_abstract"
    PAPER_FULLTEXT = "paper_fulltext"
    TRAJECTORY = "trajectory"
    PROFILE = "profile"
    SYNTHETIC = "synthetic"


class EntityType(str, Enum):
    PAPER = "paper"
    RESEARCHER = "researcher"
    DOCUMENT_CHUNK = "document_chunk"
    INTERSECTION = "intersection"


DEFAULT_COLLABORATION_WEIGHTS: dict[str, float] = {
    "research_relevance": 0.25,
    "method_complementarity": 0.20,
    "trajectory_alignment": 0.20,
    "gap_relevance": 0.15,
    "evidence_strength": 0.10,
    "feasibility": 0.10,
}

DISCOVERY_STEPS: list[str] = [
    "resolve_inputs",
    "literature_search",
    "analyze_papers",
    "analyze_trajectories",
    "detect_gaps",
    "discover_intersections",
    "verify_evidence",
    "generate_hypotheses",
    "rank_collaborations",
]

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx", ".txt"}

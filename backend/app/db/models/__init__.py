"""All SQLAlchemy models. Importing this package registers every table."""
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.profile import ResearchProfile, ResearchProfileVersion
from app.db.models.document import Document, DocumentChunk
from app.db.models.researcher import Researcher, ResearcherAlias
from app.db.models.paper import Paper, PaperAuthor
from app.db.models.taxonomy import (
    DatasetEntity,
    Method,
    PaperDataset,
    PaperMethod,
    PaperTopic,
    Topic,
)
from app.db.models.trajectory import ResearchTrajectory
from app.db.models.gap import ResearchGap, ResearchGapEvidence
from app.db.models.intersection import IntersectionEvidence, ResearchIntersection
from app.db.models.hypothesis import Experiment, Hypothesis
from app.db.models.collaboration import CollaborationCandidate
from app.db.models.evidence import Evidence
from app.db.models.embedding import EmbeddingRecord
from app.db.models.job import JobEvent, ResearchJob
from app.db.models.report import GeneratedReport
from app.db.models.setting import AgentCall, AuditLog, Setting

__all__ = [
    "User",
    "Workspace",
    "ResearchProfile",
    "ResearchProfileVersion",
    "Document",
    "DocumentChunk",
    "Researcher",
    "ResearcherAlias",
    "Paper",
    "PaperAuthor",
    "Topic",
    "Method",
    "DatasetEntity",
    "PaperTopic",
    "PaperMethod",
    "PaperDataset",
    "ResearchTrajectory",
    "ResearchGap",
    "ResearchGapEvidence",
    "ResearchIntersection",
    "IntersectionEvidence",
    "Hypothesis",
    "Experiment",
    "CollaborationCandidate",
    "Evidence",
    "EmbeddingRecord",
    "ResearchJob",
    "JobEvent",
    "GeneratedReport",
    "Setting",
    "AuditLog",
    "AgentCall",
]

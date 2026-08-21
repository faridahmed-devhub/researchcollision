# ResearchCollision

<p align="center">
  <strong>An Evidence-Aware Agentic AI Platform for Discovering Non-Obvious Research Collaborations and Research Opportunities.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#agentic-workflow">Agentic Workflow</a> •
  <a href="#installation">Installation</a> •
  <a href="#api">API</a> •
  <a href="#development">Development</a>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18%2B-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5%2B-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

</p>

---

## What is ResearchCollision?

ResearchCollision is an **Agentic AI Research Discovery Platform** designed to identify meaningful connections between researchers, research domains, scientific literature, research gaps, methods, datasets, and emerging research directions.

Traditional research discovery usually looks like:

```text
Research Question
       ↓
Search
       ↓
Similar Papers
       ↓
Similar Researchers

ResearchCollision takes a different approach:

Researcher A
      +
Researcher B
      +
Scientific Literature
      +
Research Trajectories
      +
Research Gaps
      +
Methods
      +
Datasets
      ↓
Research Intersection
      ↓
Evidence Verification
      ↓
Research Hypothesis
      ↓
Experiment Design
      ↓
Potential Collaboration

The central question is:

Who could potentially be working together, and what research opportunity might exist between their research trajectories?

ResearchCollision does not claim that a researcher wants to collaborate.

Instead, it identifies evidence-supported potential research intersections that a human researcher can evaluate.

Why ResearchCollision?
Modern research is increasingly interdisciplinary.

A researcher working on:

Large Language Models

may benefit from someone working on:

Scientific Machine Learning

while another researcher may contribute:

Domain-specific datasets

and another:

Evaluation methodology

However, conventional literature search tends to stay within known keywords and research communities.

ResearchCollision attempts to find the collision point between these research trajectories.

Core Concept
Research Collision
A Research Collision occurs when two or more research trajectories contain complementary:

Problems
Methods
Expertise
Datasets
Domains
Research questions
Scientific objectives
Example:

Researcher A

LLM Evaluation
RAG
NLP
Hallucination Detection

              +

Researcher B

Climate Modeling
Scientific ML
Environmental Data

              ↓

Potential Research Collision

Domain-aware evaluation of
LLM scientific reasoning
for climate-related tasks

The system then searches the literature and evaluates whether this intersection is:

Relevant
Evidence-supported
Underexplored
Feasible
Experimentally testable
Key Principles
ResearchCollision is built around five principles.

1. Evidence First
AI-generated claims should be connected to evidence whenever possible.

2. No Fabricated Research
The system must never invent:

Papers
Researchers
Universities
DOI
URLs
Findings
Datasets
Funding
Research positions
Collaboration intentions
3. Separate Facts From Inference
The platform distinguishes:

VERIFIED
INFERRED
SPECULATIVE
UNKNOWN

4. Human-in-the-Loop
AI proposes.

Researchers validate.

AI Discovery
      ↓
Evidence Review
      ↓
Human Validation
      ↓
Research Decision

5. Scientific Novelty Is Not Guaranteed
The system must never say:

"Nobody has researched this."

Instead:

"No relevant evidence was found in the searched literature."

or:

"This appears underexplored based on the retrieved literature."

Features
Research DNA Extraction
Upload a CV or research document.

The system extracts:

Research interests
Research questions
Research problems
Academic background
Publications
Projects
Methods
Technical skills
Datasets
Domains
Research experience
Emerging interests
Example:

{
  "domains": [
    "Natural Language Processing",
    "Machine Learning"
  ],
  "research_problems": [
    "LLM hallucination",
    "RAG evaluation"
  ],
  "methods": [
    "Transformers",
    "Deep Learning",
    "Retrieval-Augmented Generation"
  ],
  "technical_skills": [
    "Python",
    "PyTorch"
  ]
}

The extracted profile can be edited before research discovery starts.

Literature Discovery
ResearchCollision uses a provider abstraction for scholarly discovery.

Initial providers:

OpenAlex
Semantic Scholar
Crossref
arXiv
Architecture:

                    LiteratureProvider
                           |
          +----------------+----------------+
          |                |                |
       OpenAlex      Semantic Scholar    Crossref
                                             |
                                           arXiv

The application does not depend on one provider.

Researcher Discovery
The platform discovers researchers using multiple signals:

Research interests
Publications
Topics
Methods
Institutions
Research trajectory
Domain expertise
Complementary skills
Keyword similarity alone is not sufficient.

Research Trajectory Analysis
A researcher's most recent publication may not fully represent their research direction.

ResearchCollision analyzes:

Historical Research
        ↓
Research Evolution
        ↓
Current Research
        ↓
Emerging Research Direction

Potential signals:

Persistent topics
Emerging topics
Topic transitions
Methodological changes
Interdisciplinary movement
Domain shifts
The system must not infer private intentions.

Research Gap Detection
The Research Gap Agent analyzes literature for:

Explicit limitations
Future work
Missing evaluations
Dataset limitations
Methodological limitations
Contradictory findings
Domain transfer opportunities
Reproducibility concerns
Evaluation gaps
Example:

Existing literature:

Method X
    ↓
Dataset Y
    ↓
Strong results

But multiple papers identify:

- Limited domain diversity
- Poor generalization
- Limited evaluation

Potential research direction:

Evaluate Method X across
another scientific domain.

This is an AI-generated research direction, not a guaranteed research gap.

Research Intersection Discovery
This is the core ResearchCollision capability.

The system compares research trajectories and literature.

Researcher A
      +
Researcher B
      +
Papers
      +
Research Gaps
      +
Methods
      +
Datasets
      ↓
Intersection Candidate

Each candidate contains:

Title
Description
Shared research problem
Complementary expertise
Research gap
Supporting evidence
Researcher A relevance
Researcher B relevance
Novelty confidence
Feasibility confidence
Evidence System
Every important externally sourced claim should have an evidence record.

Example:

Claim:
Researcher A works on LLM evaluation.

Source:
Official university profile

Source Type:
University Profile

Status:
VERIFIED

Retrieved:
2026-08-21

Evidence statuses:

Status	Description
VERIFIED	Directly supported by available evidence
INFERRED	AI inference from available evidence
SPECULATIVE	Possible idea requiring validation
UNKNOWN	Evidence unavailable

Citation Verification
ResearchCollision validates scholarly metadata where possible.

Validation signals include:

DOI
Paper title
Authors
Provider ID
Publication year
Source URL
A citation must not be marked as verified unless the underlying source can be validated.

Hypothesis Generation
For promising research intersections, the system generates a structured hypothesis.

Example:

Research Question

Can domain-aware evaluation improve
the reliability assessment of LLMs
on scientific reasoning tasks?

Hypothesis

Domain-specific evaluation protocols
will reveal failure modes that are not
captured by general-purpose benchmarks.

Hypotheses may include:

Research question
Hypothesis
Motivation
Research gap
Supporting evidence
Proposed method
Dataset
Baseline
Metrics
Expected contribution
Risks
AI-generated hypotheses are clearly labeled.

Experiment Design
ResearchCollision can transform a research intersection into an initial experiment plan.

Research Question
        ↓
Hypothesis
        ↓
Dataset
        ↓
Baseline
        ↓
Proposed Method
        ↓
Evaluation Metrics
        ↓
Ablation
        ↓
Expected Outcome

The system separates:

Verified Resources

from:

AI-Proposed Resources

Collaboration Discovery
ResearchCollision ranks researchers who may be relevant to a research opportunity.

Example scoring:

Research relevance          25%
Method complementarity      20%
Research trajectory         20%
Research gap relevance      15%
Evidence strength           10%
Feasibility                 10%

Example:

Collaboration Score: 91

Research relevance:        Strong
Method complementarity:    Strong
Trajectory relevance:      Strong
Evidence coverage:         High
Feasibility:               Good

The system should say:

"This researcher appears potentially relevant based on available research evidence."

It should never say:

"This researcher wants to collaborate."

Agentic Architecture
ResearchCollision uses specialized agents rather than one large prompt.

                         ┌─────────────────────┐
                         │   Research DNA      │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Literature       │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Paper Analysis    │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Trajectory       │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Research Gap     │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Research Intersection│
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Verification     │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Hypothesis       │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Experiment       │
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Collaboration Rank  │
                         │       Agent         │
                         └─────────────────────┘

Each agent must have:

Structured input
Structured output
Pydantic schema
Validation
Evidence requirements
Retry strategy
Error handling
Versioned prompts
Agent Responsibilities
Research DNA Agent
Input:

CV
Research Statement
Publication List

Output:

ResearchProfile

Literature Agent
Responsibilities:

Search scholarly providers
Normalize metadata
Deduplicate papers
Cache results
Store provenance
Paper Analysis Agent
Responsibilities:

Extract research topics
Identify methods
Identify datasets
Identify limitations
Identify future work
Extract evidence
Trajectory Agent
Responsibilities:

Analyze publication history
Detect persistent themes
Detect emerging themes
Detect topic transitions
Build research trajectory
Research Gap Agent
Responsibilities:

Analyze limitations
Analyze future work
Detect missing evaluations
Detect domain-transfer opportunities
Build candidate gaps
Intersection Agent
Responsibilities:

Compare research trajectories
Identify complementary expertise
Generate intersection candidates
Score relevance
Link evidence
Verification Agent
Responsibilities:

Validate claims
Validate citations
Validate URLs
Check source quality
Mark evidence status
Hypothesis Agent
Responsibilities:

Generate research questions
Generate hypotheses
Connect hypotheses to evidence
Identify risks
Experiment Agent
Responsibilities:

Propose datasets
Propose baselines
Propose methodology
Propose evaluation metrics
Generate experiment plans
Ranking Agent
Responsibilities:

Rank collaboration candidates
Calculate confidence
Explain ranking
Return evidence-backed reasons
Architecture
ResearchCollision follows a modular monolith architecture.

This provides:

Simple local development
Clear domain boundaries
Easy testing
Lower operational complexity
Future migration to distributed services
┌─────────────────────────────────────┐
│             React UI                │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│             FastAPI                 │
│          REST API Layer              │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│        Application Services         │
└──────────────────┬──────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Agents      Providers    Evidence
       │           │           │
       └───────────┼───────────┘
                   ▼
┌─────────────────────────────────────┐
│         Domain / Repository         │
│              Layer                  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          SQLite + FTS5              │
└─────────────────────────────────────┘

Technology Stack
Backend
Python 3.11+
FastAPI
Pydantic v2
SQLAlchemy 2
Alembic
SQLite
SQLite FTS5
httpx
BeautifulSoup4
PyMuPDF
python-docx
pandas
openpyxl
sentence-transformers
pytest
pytest-asyncio
Ruff
MyPy
Frontend
React
TypeScript
Vite
Tailwind CSS
React Router
TanStack Query
Zustand
Recharts
Lucide React
Vitest
React Testing Library
Playwright
AI
Provider abstraction supports:

OpenRouter
OpenAI-compatible APIs
Hugging Face
Mock LLM provider
Scholarly Data
Provider abstraction supports:

OpenAlex
Semantic Scholar
Crossref
arXiv
Project Structure
researchcollision/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py
│   │   │       ├── workspaces.py
│   │   │       ├── research_profiles.py
│   │   │       ├── researchers.py
│   │   │       ├── papers.py
│   │   │       ├── discovery.py
│   │   │       ├── trajectories.py
│   │   │       ├── gaps.py
│   │   │       ├── intersections.py
│   │   │       ├── hypotheses.py
│   │   │       ├── experiments.py
│   │   │       ├── collaborations.py
│   │   │       ├── evidence.py
│   │   │       └── reports.py
│   │   │
│   │   ├── agents/
│   │   │   ├── base.py
│   │   │   ├── profile_agent.py
│   │   │   ├── literature_agent.py
│   │   │   ├── paper_analysis_agent.py
│   │   │   ├── trajectory_agent.py
│   │   │   ├── gap_agent.py
│   │   │   ├── intersection_agent.py
│   │   │   ├── verification_agent.py
│   │   │   ├── hypothesis_agent.py
│   │   │   ├── experiment_agent.py
│   │   │   └── ranking_agent.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   │
│   │   ├── providers/
│   │   │   ├── ai/
│   │   │   │   ├── base.py
│   │   │   │   ├── openrouter.py
│   │   │   │   ├── huggingface.py
│   │   │   │   └── mock.py
│   │   │   │
│   │   │   ├── literature/
│   │   │   │   ├── base.py
│   │   │   │   ├── openalex.py
│   │   │   │   ├── semantic_scholar.py
│   │   │   │   ├── crossref.py
│   │   │   │   └── arxiv.py
│   │   │   │
│   │   │   └── embeddings/
│   │   │
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── prompts/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   │
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── profile/
│   │   │   ├── discovery/
│   │   │   ├── researchers/
│   │   │   ├── intersections/
│   │   │   ├── hypotheses/
│   │   │   └── experiments/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── stores/
│   │   ├── types/
│   │   └── utils/
│   │
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
│
├── evaluation/
│   ├── datasets/
│   ├── benchmarks/
│   └── reports/
│
├── sample_data/
│   ├── sample_cv.pdf
│   ├── sample_researchers.json
│   └── sample_papers.json
│
├── scripts/
│   ├── seed.py
│   ├── reset_db.py
│   └── benchmark.py
│
├── docs/
│   ├── architecture.md
│   ├── agents.md
│   ├── database.md
│   ├── providers.md
│   └── evaluation.md
│
├── data/
│
├── .env.example
├── docker-compose.yml
├── Makefile
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md

Database Architecture
SQLite is the default database for local development.

The schema is designed to allow future migration to PostgreSQL.

Core entities:

users
workspaces

research_profiles
research_profile_versions

documents
document_chunks

researchers
researcher_aliases

papers
paper_authors

topics
methods
datasets

research_trajectories

research_gaps
research_gap_evidence

research_intersections
intersection_evidence

hypotheses
experiments

collaboration_candidates

evidence
embeddings

research_jobs
job_events

generated_reports

settings
audit_logs

All major tables should contain:

id
created_at
updated_at

Foreign keys, indexes, uniqueness constraints, and appropriate cascading behavior should be enforced.

Full Discovery Workflow
1. Create Workspace
        ↓
2. Upload CV / Research Profile
        ↓
3. Research DNA Agent
        ↓
4. Review Research Profile
        ↓
5. Select Research Domains
        ↓
6. Discover Relevant Researchers
        ↓
7. Collect Publications
        ↓
8. Analyze Publications
        ↓
9. Build Research Trajectories
        ↓
10. Detect Research Gaps
        ↓
11. Generate Research Intersections
        ↓
12. Verify Evidence
        ↓
13. Rank Intersections
        ↓
14. Generate Hypotheses
        ↓
15. Design Experiments
        ↓
16. Rank Collaboration Candidates
        ↓
17. Human Review
        ↓
18. Export Research Report

Job System
Research discovery may require hundreds or thousands of operations.

The job system supports:

PENDING
RUNNING
PAUSED
COMPLETED
FAILED
CANCELLED

Operations:

START
PAUSE
RESUME
CANCEL
RETRY

Example:

Research Discovery Job

Status: RUNNING

Researchers:
124 / 250

Papers:
1,284 / 2,000

Evidence:
3,412 records

Intersections:
37 candidates

A failed researcher should not terminate the entire job.

Errors are logged and processing continues where possible.

Caching
ResearchCollision caches expensive research operations.

Cached objects include:

Provider responses
Paper metadata
Researcher metadata
Extracted text
Embeddings
Evidence
AI analysis
Research trajectories
Cache metadata:

URL
Content Hash
Provider
Retrieved At
Expires At

The system should avoid repeatedly requesting the same public resource unless the user explicitly chooses:

Refresh Research

Provider Architecture
Providers use interfaces.

Example:

class LiteratureProvider(Protocol):

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[PaperRecord]:
        ...

AI providers follow a similar interface:

class LLMProvider(Protocol):

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        ...

This allows providers to be replaced without changing business logic.

AI Provider Configuration
Example:

LLM_PROVIDER=openrouter
LLM_MODEL=your-model
OPENROUTER_API_KEY=your-key

Alternative:

LLM_PROVIDER=huggingface

Development:

LLM_PROVIDER=mock

API keys must never be hard-coded.

Literature Provider Configuration
OpenAlex:

LITERATURE_PROVIDER=openalex
OPENALEX_EMAIL=your-email@example.com

Semantic Scholar:

SEMANTIC_SCHOLAR_API_KEY=your-key

The application should gracefully handle unavailable providers.

Environment Variables
Copy:

cp .env.example .env

Example:

APP_ENV=development

SECRET_KEY=change-this-in-production

DATABASE_URL=sqlite:///./data/researchcollision.db

LLM_PROVIDER=mock
LLM_MODEL=

OPENROUTER_API_KEY=

LITERATURE_PROVIDER=openalex

OPENALEX_EMAIL=

SEMANTIC_SCHOLAR_API_KEY=

EMBEDDING_PROVIDER=mock

MAX_UPLOAD_SIZE_MB=10

CORS_ORIGINS=http://localhost:5173

LOG_LEVEL=INFO

Installation
Requirements
Python 3.11+
Node.js 20+
npm
Git
Optional:

Docker
Docker Compose
Clone Repository
git clone https://github.com/YOUR_USERNAME/researchcollision.git

cd researchcollision

Backend Setup
cd backend

python -m venv .venv

Linux/macOS:

source .venv/bin/activate

Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run migrations:

alembic upgrade head

Seed sample data:

python ../scripts/seed.py

Start backend:

uvicorn app.main:app --reload

Backend:

http://localhost:8000

API documentation:

http://localhost:8000/docs

Frontend Setup
Open a second terminal:

cd frontend

npm install

npm run dev

Frontend:

http://localhost:5173

Docker
Build and start:

docker compose up --build

Stop:

docker compose down

Run in background:

docker compose up -d

View logs:

docker compose logs -f

Development Commands
From the repository root:

make install

Run backend:

make backend

Run frontend:

make frontend

Run tests:

make test

Run lint:

make lint

Run type checking:

make typecheck

Run formatting:

make format

Run all checks:

make check

Testing
Backend
cd backend
pytest

With coverage:

pytest --cov=app --cov-report=term-missing

Frontend
cd frontend
npm run test

End-to-End
npm run test:e2e

or:

make e2e

API
The backend exposes REST APIs under:

/api/v1

Core endpoints:

GET    /api/v1/health

POST   /api/v1/workspaces
GET    /api/v1/workspaces

POST   /api/v1/research-profiles
GET    /api/v1/research-profiles/{id}
PUT    /api/v1/research-profiles/{id}

POST   /api/v1/documents/upload

POST   /api/v1/discovery/jobs
GET    /api/v1/discovery/jobs/{id}

POST   /api/v1/discovery/jobs/{id}/pause
POST   /api/v1/discovery/jobs/{id}/resume
POST   /api/v1/discovery/jobs/{id}/cancel

GET    /api/v1/researchers
GET    /api/v1/researchers/{id}

GET    /api/v1/papers
GET    /api/v1/papers/{id}

GET    /api/v1/trajectories/{id}

GET    /api/v1/gaps
GET    /api/v1/gaps/{id}

GET    /api/v1/intersections
GET    /api/v1/intersections/{id}

POST   /api/v1/hypotheses
GET    /api/v1/hypotheses/{id}

POST   /api/v1/experiments
GET    /api/v1/experiments/{id}

GET    /api/v1/collaborations
GET    /api/v1/collaborations/{id}

GET    /api/v1/evidence
GET    /api/v1/evidence/{id}

POST   /api/v1/reports
GET    /api/v1/reports/{id}

The interactive OpenAPI documentation is available at:

http://localhost:8000/docs

Frontend Pages
Dashboard
Displays:

Active workspace
Research profile
Discovery jobs
Researcher count
Paper count
Research gaps
Research intersections
Collaboration candidates
Research Profile
Displays:

Research Domains
Research Problems
Research Questions
Methods
Technical Skills
Datasets
Publications
Projects
Experience

Users can edit the extracted profile.

Discovery Dashboard
Displays:

Job Status
Researchers Discovered
Papers Collected
Papers Analyzed
Research Gaps
Intersections
Evidence Records
Collaboration Candidates

Progress example:

Research Discovery

████████████████░░░░ 82%

Researchers: 146 / 180
Papers: 1,430 / 1,800

Researcher Detail
Shows:

Researcher
Institution
Research areas
Publication history
Research trajectory
Methods
Topics
Evidence
Relevant papers
Potential intersections
Collaboration score
Research Intersection Detail
Shows:

Intersection Title

Why This Intersection Matters

Researcher A

Researcher B

Shared Problem

Complementary Expertise

Research Gap

Supporting Literature

Evidence

Novelty Confidence

Feasibility Confidence

Hypothesis Detail
Shows:

Research Question

Hypothesis

Motivation

Research Gap

Evidence

Method

Dataset

Baseline

Evaluation Metrics

Expected Contribution

Risks

Experiment Detail
Shows:

Objective

Research Question

Hypothesis

Dataset

Baseline

Method

Metrics

Ablation

Expected Results

Risks

Reproducibility Notes

Evidence Panel
Every important AI-generated claim should be inspectable.

Example:

Claim

Researcher X studies LLM evaluation.

Status

VERIFIED

Source

Official university profile

Retrieved

2026-08-21

Export
ResearchCollision can generate research reports.

Potential formats:

JSON
CSV
XLSX
Markdown
PDF
A report should include:

Research profile
Researchers
Papers
Research gaps
Research intersections
Hypotheses
Experiments
Collaboration candidates
Evidence
Sources
Evidence Quality
Sources should be prioritized approximately as:

Official university source
Official researcher profile
Official laboratory/group
Official publication
DOI/Crossref
OpenAlex
Semantic Scholar
arXiv
Other reputable scholarly sources
Lower-quality sources should not automatically be treated as authoritative.

Source Provenance
Each externally derived record should retain provenance.

Example:

{
  "source_url": "https://example.org/researcher",
  "source_type": "official_profile",
  "retrieved_at": "2026-08-21T12:00:00Z",
  "content_hash": "sha256:...",
  "status": "VERIFIED"
}

Rate Limiting
ResearchCollision must use reasonable request rates.

The system must not:

Crawl aggressively
Circumvent rate limits
Bypass authentication
Bypass CAPTCHA
Bypass Cloudflare
Access private information
When a provider returns a rate-limit error, the system should:

Log the error.
Apply backoff.
Retry when appropriate.
Continue with other providers when possible.
Privacy
ResearchCollision may process sensitive academic documents such as CVs.

The application should provide:

File validation
File size limits
Secure temporary storage
User-controlled deletion
Workspace deletion
Export functionality
Configurable external AI processing
Uploaded documents should never be executed as code.

Security
Never store API keys in source code.

Never commit:

.env
API keys
tokens
passwords
private certificates

Use:

.env.example

for configuration documentation.

Security vulnerabilities should be reported privately.

See:

SECURITY.md

AI Safety and Reliability
ResearchCollision is an AI-assisted research discovery tool.

AI output may contain errors.

Therefore:

AI Suggestion
      ↓
Evidence
      ↓
Verification
      ↓
Human Review

The platform should make uncertainty visible instead of hiding it.

Hallucination Prevention
The system should use:

Structured outputs
Pydantic validation
Citation verification
Evidence requirements
Provider provenance
Confidence scores
Explicit uncertainty states
Human review
AI output must never be accepted blindly.

Novelty Detection
Research novelty is difficult to determine automatically.

ResearchCollision therefore uses cautious language.

Allowed:

Potentially underexplored

No relevant evidence found

Potential research opportunity

Not allowed:

Nobody has ever done this.

This is guaranteed novel.

Collaboration Ethics
ResearchCollision should not infer:

Private interests
Personal intentions
Willingness to collaborate
Hiring decisions
Funding decisions
Unpublished research
The system only analyzes publicly available research evidence.

Evaluation Framework
ResearchCollision should be evaluated using both automated and human evaluation.

Metrics:

Precision@K
Recall@K
MRR

Citation Accuracy
Evidence Coverage
Unsupported Claim Rate

Researcher Relevance
Intersection Relevance
Research Gap Relevance

Novelty Rating
Feasibility Rating
Collaboration Relevance

Human Evaluation
Potential evaluation form:

Is the researcher relevant?

1 2 3 4 5

Is the research intersection meaningful?

1 2 3 4 5

Is the evidence sufficient?

1 2 3 4 5

Does the opportunity appear feasible?

1 2 3 4 5

These evaluations can be used to improve ranking models.

Reproducibility
Every discovery job should store:

Job ID
Prompt Version
Model
Model Parameters
Provider
Search Queries
Provider Responses
Retrieved Sources
Evidence
Timestamp
Ranking Configuration

This makes results more reproducible.

Observability
The backend should provide structured logs.

Example:

INFO  discovery.job.started
INFO  literature.search.completed
INFO  researcher.analysis.completed
INFO  evidence.verification.completed
WARN  provider.rate_limit
ERROR agent.execution.failed
INFO  discovery.job.completed

Each job should have a correlation ID.

Error Handling
Errors should be categorized.

PROVIDER_ERROR
RATE_LIMIT_ERROR
VALIDATION_ERROR
PARSING_ERROR
AI_ERROR
DATABASE_ERROR
NETWORK_ERROR
UNKNOWN_ERROR

A single failed agent should not unnecessarily terminate an entire discovery job.

Sample Workflow
A typical user workflow:

Create Workspace
      ↓
Upload CV
      ↓
AI extracts Research DNA
      ↓
User reviews profile
      ↓
Select research domain
      ↓
Start Discovery
      ↓
Find researchers
      ↓
Collect papers
      ↓
Analyze research trajectories
      ↓
Find research gaps
      ↓
Generate intersections
      ↓
Verify evidence
      ↓
Rank candidates
      ↓
Generate hypotheses
      ↓
Design experiments
      ↓
Human review
      ↓
Export report

Example Research Collision
Researcher A
Primary Areas:

NLP
LLM Evaluation
RAG
Hallucination Detection

Researcher B
Primary Areas:

Healthcare AI
Clinical NLP
Medical Data

Literature
LLM evaluation
Medical reasoning
RAG
Clinical QA

Potential Collision
Reliable Retrieval-Augmented
Clinical Reasoning Evaluation

Possible Research Question
Can domain-specific retrieval evaluation
improve reliability assessment of
LLM-based clinical reasoning systems?

The system should then search the literature before presenting this as an opportunity.

Development Mode
ResearchCollision includes mock providers.

MockLLMProvider
MockLiteratureProvider
MockEmbeddingProvider

This allows the application to run without external API keys.

Mock data must always be visibly labeled as:

DEMO DATA

Database Migration
Create migration:

cd backend
alembic revision --autogenerate -m "description"

Apply:

alembic upgrade head

Rollback:

alembic downgrade -1

Reset Development Database
python scripts/reset_db.py

Then:

alembic upgrade head
python scripts/seed.py

Production Considerations
For production deployment, consider:

PostgreSQL
pgvector
Redis
Background worker system
Object storage
Secrets manager
Reverse proxy
HTTPS
Centralized logging
Monitoring
Rate limiting
Automated backups
SQLite is intentionally the default for local development.

Scaling Strategy
Initial:

FastAPI
+
SQLite
+
Background Jobs

Future:

                    Load Balancer
                         |
             +-----------+-----------+
             |                       |
          FastAPI                 FastAPI
             |                       |
             +-----------+-----------+
                         |
                      Redis
                         |
                  Worker Pool
                         |
          +--------------+--------------+
          |              |              |
       AI Worker    Search Worker   Analysis Worker
                         |
                    PostgreSQL
                         |
                      pgvector

The provider and repository abstractions are intended to make this migration incremental.

Roadmap
Phase 1 — Foundation
 Project scaffolding
 FastAPI backend
 React frontend
 SQLite database
 Alembic migrations
 Provider interfaces
 Mock providers
 Basic authentication/workspaces
Phase 2 — Research Profile
 CV upload
 PDF extraction
 DOCX extraction
 Research DNA extraction
 Profile editing
 Profile versioning
Phase 3 — Literature Intelligence
 OpenAlex integration
 Semantic Scholar integration
 Crossref integration
 arXiv integration
 Metadata normalization
 Deduplication
 Caching
 Citation verification
Phase 4 — Agentic Research Discovery
 Literature Agent
 Paper Analysis Agent
 Trajectory Agent
 Research Gap Agent
 Intersection Agent
 Verification Agent
 Ranking Agent
Phase 5 — Research Generation
 Hypothesis Agent
 Experiment Agent
 Evidence-backed reports
 Research concept generation
Phase 6 — Evaluation
 Benchmark dataset
 Precision@K
 Recall@K
 MRR
 Human evaluation
 Citation accuracy
 Unsupported claim detection
Future
 Knowledge graph
 PostgreSQL
 pgvector
 Distributed workers
 Research trend forecasting
 Collaborative workspaces
 Research community feedback
 Advanced interdisciplinary discovery
Known Limitations
ResearchCollision depends on publicly available research data.

Potential limitations include:

Incomplete researcher profiles
Missing publications
Incorrect metadata
Provider rate limits
Citation ambiguity
AI reasoning errors
False-positive intersections
Difficulty determining scientific novelty
Limited information about future research directions
Difficulty measuring real-world collaboration success
Therefore, all important research decisions require human validation.

Contributing
Contributions are welcome.

Before opening a pull request:

make test
make lint
make typecheck

New AI functionality should:

Use structured outputs.
Define explicit Pydantic schemas.
Validate model responses.
Provide evidence where applicable.
Never fabricate scientific information.
Clearly distinguish facts from inference.
Include tests.
Preserve provider abstraction.
Avoid hard-coded secrets.
Document important architectural decisions.
Pull Request Guidelines
A pull request should contain:

Problem
Solution
Architecture Impact
Tests
Potential Risks

AI-generated code should be reviewed before merging.

License
Copyright © ResearchCollision Contributors.

Licensed under the Apache License, Version 2.0.

You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

Vision
Most research discovery systems answer:

"What papers are similar?"

ResearchCollision asks a different question:

"What meaningful research opportunity
might exist between these research trajectories?"

The long-term vision is to build an intelligent research discovery layer where:

Researchers
     +
Literature
     +
Research Trajectories
     +
Research Gaps
     +
Methods
     +
Datasets
     +
Agentic AI
     ↓
Research Collision
     ↓
Potential Research Opportunity
     ↓
Human Scientific Validation

ResearchCollision
Who should be working together — but currently isn't?

ResearchCollision is not designed to replace researchers.

It is designed to help researchers see connections they may not have searched for yet.

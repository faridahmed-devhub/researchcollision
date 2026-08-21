# ResearchCollision

<p align="center">
  <strong>Evidence-Aware Agentic AI for Discovering Non-Obvious Research Connections</strong>
</p>

<p align="center">
  Discover potential research intersections, research gaps, hypotheses,
  experiment ideas, and complementary researchers across scientific literature.
</p>

<p align="center">

![Status](https://img.shields.io/badge/status-active%20development-orange)
![Build](https://img.shields.io/badge/build-verified-brightgreen)
![Tests](https://img.shields.io/badge/tests-8%2F8%20passing-brightgreen)
![E2E](https://img.shields.io/badge/E2E-Playwright-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Agentic AI](https://img.shields.io/badge/AI-Agentic%20AI-purple)

</p>

---

## Overview

ResearchCollision is an **Evidence-Aware Agentic AI research discovery
platform** designed to identify potentially meaningful connections between:

- Researchers
- Research domains
- Scientific literature
- Research problems
- Methods
- Datasets
- Research trajectories
- Research gaps
- Emerging research directions

Traditional research discovery often looks like:

```text
Research Question
      ↓
Keyword Search
      ↓
Similar Papers
      ↓
Similar Researchers


ResearchCollision explores a different workflow:

Research Profile
      ↓
Research DNA
      ↓
Scientific Literature
      ↓
Research Trajectories
      ↓
Research Gaps
      ↓
Research Intersections
      ↓
Evidence Verification
      ↓
Research Hypothesis
      ↓
Experiment Design
      ↓
Potential Collaboration


The central question is:

What meaningful research connection might exist between research trajectories that are not obviously connected?

ResearchCollision does not claim that a researcher wants to collaborate.

Instead, it identifies evidence-supported potential research intersections
that a human researcher can investigate and validate.

Why ResearchCollision?
Modern research is increasingly interdisciplinary.

A researcher working on:

LLM Evaluation
RAG
NLP
Hallucination Detection


may have complementary expertise with another researcher working on:

Scientific Machine Learning
Climate Modeling
Environmental Data


while another researcher may contribute:

Evaluation Methodology
Benchmarking
Robustness


Traditional keyword search may not naturally connect these research
communities.

ResearchCollision attempts to find the intersection:

Researcher A
     +
Researcher B
     +
Scientific Literature
     +
Research Gaps
     +
Methods
     +
Datasets
     ↓
Potential Research Collision


For example:

Domain-aware evaluation of LLM
scientific reasoning for climate-related tasks


This is not presented as guaranteed novel research.

It is a candidate research direction that requires human validation.

Core Concept: Research Collision
A Research Collision occurs when two or more research trajectories contain
potentially complementary:

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


The system can then investigate whether the intersection appears:

Relevant
Evidence-supported
Potentially underexplored
Feasible
Experimentally testable
Design Principles
ResearchCollision is built around five principles.

1. Evidence First
AI-generated claims should be connected to available evidence whenever
possible.

Important claims should preserve:

Claim
Source
Source Type
Retrieved At
Evidence Status


2. No Fabricated Research
The system must never invent:

Researchers
Universities
Papers
DOI
URLs
Research findings
Datasets
Funding
Research positions
Collaboration intentions
If reliable evidence cannot be found, the system should say so.

3. Separate Facts From Inference
ResearchCollision distinguishes between:

Status	Meaning
VERIFIED	Directly supported by available evidence
INFERRED	AI inference based on available evidence
SPECULATIVE	Potential idea requiring validation
UNKNOWN	Evidence unavailable


Example:

Claim:
Researcher X works on LLM evaluation.

Status:
VERIFIED

Evidence:
Official university research profile


Whereas:

Claim:
Researcher X may be relevant to this research direction.

Status:
INFERRED


4. Human-in-the-Loop
ResearchCollision is not intended to replace scientific judgment.

AI Discovery
     ↓
Evidence Review
     ↓
Human Validation
     ↓
Research Decision


The AI proposes.

The researcher validates.

5. Scientific Novelty Is Not Guaranteed
The system should never claim:

Nobody has researched this.


Instead:

No relevant evidence was found in the searched literature.


or:

This appears potentially underexplored based on
the retrieved literature.


Scientific novelty ultimately requires human and scholarly validation.

Features
Research DNA Extraction
A researcher can provide:

CV
Research statement
Publication list
Projects
Research portfolio
The system can extract:

Research Domains
Research Problems
Research Questions
Methods
Technical Skills
Datasets
Publications
Projects
Research Experience
Research Interests
Emerging Interests


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


The extracted research profile can be reviewed and edited before discovery.

Literature Discovery
ResearchCollision is designed around a provider abstraction for scholarly
literature.

Supported/planned providers include:

OpenAlex
Semantic Scholar
Crossref
arXiv
Architecture:

                 LiteratureProvider
                        |
          +-------------+-------------+
          |             |             |
       OpenAlex   Semantic Scholar  Crossref
                                      |
                                    arXiv


The platform should not depend on a single literature provider.

Researcher Discovery
Potential researchers can be identified using multiple signals:

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
A researcher's latest publication does not necessarily represent their
complete research direction.

ResearchCollision analyzes the potential trajectory:

Historical Research
       ↓
Research Evolution
       ↓
Current Research
       ↓
Emerging Direction


Potential signals include:

Persistent topics
Emerging topics
Topic transitions
Methodological changes
Interdisciplinary movement
Domain shifts
The system must not claim to know private research intentions.

Research Gap Detection
The Research Gap Agent analyzes available literature for signals such as:

Explicit limitations
Future work
Missing evaluations
Dataset limitations
Methodological limitations
Contradictory findings
Domain-transfer opportunities
Reproducibility concerns
Evaluation gaps
Example:

Existing Literature
       ↓
Method X
       ↓
Dataset Y
       ↓
Strong Results
       ↓
Reported Limitations
       ↓
Potential Research Direction


A generated research direction is an AI-generated candidate, not a
guaranteed research gap.

Research Intersection Discovery
This is the central ResearchCollision capability.

Researcher A
      +
Researcher B
      +
Scientific Papers
      +
Research Gaps
      +
Methods
      +
Datasets
      ↓
Intersection Candidate


A candidate can contain:

Title
Description
Shared research problem
Complementary expertise
Research gap
Supporting evidence
Researcher relevance
Feasibility
Confidence
Evidence System
Every important externally sourced claim should have an evidence record.

Example:

Claim:
Researcher A works on LLM evaluation.

Source:
Official university profile

Source Type:
University Research Profile

Status:
VERIFIED

Retrieved:
2026-08-21


Evidence statuses:

Status	Description
VERIFIED	Directly supported by evidence
INFERRED	AI inference from evidence
SPECULATIVE	Potential idea requiring validation
UNKNOWN	Evidence unavailable


Citation Verification
Scholarly metadata can be checked using:

DOI
Paper title
Authors
Provider ID
Publication year
Source URL
A citation should not be marked as verified unless the underlying source
can be validated.

Hypothesis Generation
For promising research intersections, the system can generate structured
research hypotheses.

Example:

Research Question

Can domain-aware evaluation improve the reliability
assessment of LLMs on scientific reasoning tasks?


Potential hypothesis:

Domain-specific evaluation protocols may reveal
failure modes that are not captured by
general-purpose benchmarks.


A hypothesis may include:

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
AI-generated hypotheses are explicitly labeled.

Experiment Design
A research intersection can be transformed into an initial experiment plan:

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


The system distinguishes between:

Verified Resources


and:

AI-Proposed Resources


This prevents generated suggestions from being confused with verified
scientific resources.

Collaboration Ranking
Potentially relevant researchers can be ranked using configurable signals.

Example scoring model:

Research Relevance          25%
Method Complementarity      20%
Research Trajectory         20%
Research Gap Relevance      15%
Evidence Strength           10%
Feasibility                 10%


Example:

Collaboration Score: 91/100

Research Relevance:        Strong
Method Complementarity:    Strong
Trajectory Relevance:      Strong
Evidence Coverage:         High
Feasibility:               Good


The score is a decision-support signal.

It is not a prediction of actual collaboration.

Agentic AI Architecture
ResearchCollision is designed around specialized agents rather than one
large monolithic prompt.

                 Research DNA Agent
                         ↓
                Literature Agent
                         ↓
                Paper Analysis Agent
                         ↓
                 Trajectory Agent
                         ↓
                  Research Gap Agent
                         ↓
              Research Intersection Agent
                         ↓
                Evidence Verification
                         ↓
                  Hypothesis Agent
                         ↓
                  Experiment Agent
                         ↓
                Collaboration Ranking


Each agent should have:

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
Projects


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
Assign evidence status
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
Propose methodologies
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

This keeps local development simple while maintaining clear boundaries for
future scaling.

┌───────────────────────────────┐
│          React UI             │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│           FastAPI             │
│          REST API             │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      Application Services     │
└───────────────┬───────────────┘
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
     Agents  Providers  Evidence
        │       │        │
        └───────┼────────┘
                ▼
┌───────────────────────────────┐
│      Domain / Repository      │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          SQLite + FTS5        │
└───────────────────────────────┘


Technology Stack
Backend
Python 3.11+
FastAPI
Pydantic
SQLAlchemy
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
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── agents/
│   │   ├── core/
│   │   ├── db/
│   │   ├── providers/
│   │   │   ├── ai/
│   │   │   ├── literature/
│   │   │   └── embeddings/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── stores/
│   │   ├── types/
│   │   └── utils/
│   ├── tests/
│   └── package.json
│
├── docs/
├── sample_data/
├── scripts/
├── data/
│
├── .env.example
├── docker-compose.yml
├── Makefile
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md


Database
SQLite is the default development database.

The architecture is designed around clear domain entities such as:

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


SQLite FTS5 can be used for local full-text search.

The architecture leaves room for future PostgreSQL/pgvector migration.

Caching
Research discovery can be expensive.

The platform is designed to cache:

Provider responses
Paper metadata
Researcher metadata
Extracted content
AI analysis
Embeddings
Evidence
Cached records can include:

URL
Provider
Content Hash
Retrieved At
Expires At


A future refresh workflow can explicitly re-run research when needed.

Background Jobs
Long-running discovery workflows should run as jobs.

Supported states:

PENDING
RUNNING
PAUSED
COMPLETED
FAILED
CANCELLED


Supported actions:

START
PAUSE
RESUME
CANCEL
RETRY


Example:

Research Discovery

████████████████░░░░ 82%

Researchers analyzed: 146 / 180
Papers analyzed:      1,430
Evidence records:     3,412
Collisions found:     37


A failure affecting one researcher should not unnecessarily terminate the
whole discovery workflow.

Provider Architecture
AI Provider
class LLMProvider(Protocol):

    async def generate(
        self,
        prompt: str,
    ) -> str:
        ...

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        ...


Structured generation should be preferred for agent outputs.

Literature Provider
class LiteratureProvider(Protocol):

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[PaperRecord]:
        ...

    async def get_paper(
        self,
        paper_id: str,
    ) -> PaperRecord | None:
        ...


This allows providers to be replaced without rewriting the application.

Research Integrity
ResearchCollision must never fabricate:

Researchers
Universities
Papers
DOI
URLs
Findings
Datasets
Funding
Positions
Collaboration intentions
If evidence is unavailable:

UNKNOWN


is preferable to an unsupported claim.

Web Usage & Safety
The system must not:

Bypass CAPTCHA
Bypass login pages
Bypass Cloudflare
Scrape private profiles
Circumvent access controls
Ignore robots restrictions
Scrape aggressively
Only legitimately accessible public information should be used.

Reasonable rate limits should be applied.

Privacy
Research documents may contain sensitive academic information.

The application should support:

File validation
File size limits
Secure temporary storage
Workspace deletion
Document deletion
Export controls
Configurable external AI processing
Uploaded files must never be executed as code.

Verification Status
The current repository is in active development.

The following application foundation has been verified locally:

Frontend
npm run build
✓ PASSING


Unit Tests
Vitest
8 / 8 passing ✓


Development Server
Frontend:
http://localhost:5173

Backend:
http://localhost:8000


Verified:

Vite development server     ✓
Frontend → backend proxy    ✓
Login flow                  ✓
Dashboard statistics        ✓


End-to-End Testing
A Playwright E2E specification has been added.

Install Chromium once:

npx playwright install chromium


Run:

npm run e2e


E2E tests should be considered verified only after running the command
successfully in the current environment.

Demo Account
For local development/demo purposes:

Email:
demo@researchcollision.dev

Password:
demo1234


Open:

http://localhost:5173


Then sign in using the demo account.

Important: These credentials are for local/demo use only.
Never use demo credentials in production.

Quick Start
Requirements
Install:

Python 3.11+
Node.js 20+
npm
Git
Optional:

Docker
Docker Compose
Backend
cd backend

python -m venv .venv


Linux/macOS
source .venv/bin/activate


Windows
.venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt


Run the backend:

uvicorn app.main:app --reload --port 8000


Backend:

http://localhost:8000


API documentation:

http://localhost:8000/docs


Frontend
Open another terminal:

cd frontend

npm install

npm run dev


Open:

http://localhost:5173


The Vite development server proxies requests to the FastAPI backend.

Environment Variables
Create:

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


Never commit .env.

Docker
Build:

docker compose up --build


Run in background:

docker compose up -d


Stop:

docker compose down


Testing
Frontend unit tests:

npm run test


Frontend build:

npm run build


Install Playwright Chromium:

npx playwright install chromium


Run E2E:

npm run e2e


Backend tests:

cd backend
pytest


Evaluation
Recommended evaluation metrics include:

Precision@K
Recall@K
MRR

Citation Accuracy
Evidence Coverage
Unsupported Claim Rate

Researcher Relevance
Research Gap Relevance
Intersection Relevance

Novelty Assessment
Feasibility Assessment
Collaboration Relevance


Human evaluation should remain part of the evaluation process.

Human Evaluation
Researchers can rate discovered opportunities:

Researcher Relevance
1  2  3  4  5

Research Intersection Quality
1  2  3  4  5

Evidence Quality
1  2  3  4  5

Potential Research Value
1  2  3  4  5


These evaluations can later be used to improve ranking and discovery.

Reproducibility
A research discovery job should preserve:

Job ID
Prompt Version
AI Model
AI Provider
Search Queries
Retrieved Sources
Evidence
Ranking Configuration
Timestamp


This makes generated results easier to inspect and reproduce.

Prompt Versioning
Agent prompts should be version controlled.

Example:

prompts/
├── profile/
│   └── v1.txt
├── literature/
│   └── v1.txt
├── trajectory/
│   └── v1.txt
├── gap/
│   └── v1.txt
├── intersection/
│   └── v1.txt
└── hypothesis/
    └── v1.txt


Generated results should record the prompt version used.

Current Development Status
ResearchCollision is currently in active development.

Verified
 Frontend production build
 Vitest test suite
 8/8 current frontend tests passing
 Vite development server
 Frontend/backend proxy
 Login flow
 Dashboard statistics
 Playwright E2E specification
In Development
 CV / research document ingestion
 Research DNA extraction
 Scholarly literature integrations
 Researcher discovery pipeline
 Research trajectory analysis
 Research gap detection
 Research intersection engine
 Evidence verification pipeline
 Hypothesis generation
 Experiment design
 Collaboration ranking
 Advanced evaluation benchmarks
This distinction is intentional: planned architecture is not represented
as already-completed functionality.

Roadmap
Phase 1 — Foundation
 React frontend foundation
 FastAPI backend foundation
 Local development environment
 Authentication flow
 Dashboard
 SQLite architecture
 Frontend tests
 Playwright specification
Phase 2 — Research DNA
 CV upload
 PDF extraction
 DOCX extraction
 Research profile extraction
 Research profile editing
 Profile versioning
Phase 3 — Literature Intelligence
 OpenAlex integration
 Semantic Scholar integration
 Crossref integration
 arXiv integration
 Metadata normalization
 Deduplication
 Citation verification
 Research caching
Phase 4 — Agentic Discovery
 Literature Agent
 Paper Analysis Agent
 Trajectory Agent
 Research Gap Agent
 Research Intersection Agent
 Evidence Verification Agent
 Collaboration Ranking Agent
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
 Citation accuracy
 Unsupported claim detection
 Human evaluation
Future
 Research knowledge graph
 PostgreSQL
 pgvector
 Distributed workers
 Research trend forecasting
 Interdisciplinary opportunity mapping
 Community feedback loops
Known Limitations
ResearchCollision depends on publicly available information and external
providers.

Therefore:

Some researcher profiles may be incomplete.
Some papers may have incomplete metadata.
Research trajectories may be noisy.
Research intersections may produce false positives.
AI-generated hypotheses may be incorrect.
Research novelty cannot be guaranteed automatically.
Collaboration intent cannot be inferred reliably.
Provider APIs may have rate limits.
Human scientific judgment remains essential.
Production Direction
The initial architecture uses a modular monolith because it keeps local
development and deployment simple.

At larger scale, the system can evolve toward:

Load Balancer
      ↓
FastAPI Services
      ↓
Job Queue
      ↓
┌───────────────┬───────────────┐
│ Discovery     │ Literature    │
│ Workers       │ Workers       │
└───────────────┴───────────────┘
      ↓
AI Workers
      ↓
PostgreSQL + pgvector
      ↓
Evidence / Research Knowledge Graph


Potential production components:

PostgreSQL
pgvector
Redis
Background workers
Object storage
Reverse proxy
HTTPS
Centralized logging
Monitoring
Secrets management
Contributing
Contributions are welcome.

Before submitting a pull request:

make test
make lint
make typecheck


New AI functionality should:

Use structured outputs.
Define Pydantic schemas.
Validate model responses.
Preserve evidence provenance.
Clearly distinguish facts from inference.
Never fabricate scientific information.
Include tests.
Preserve provider abstraction.
Avoid hard-coded secrets.
Document important architectural decisions.
Security
If you discover a security vulnerability, please avoid publishing sensitive
details in a public issue.

See:

SECURITY.md


for responsible disclosure information.

License
Copyright © ResearchCollision Contributors.

Licensed under the Apache License, Version 2.0.

See:

LICENSE


Vision
Research discovery should not stop at:

"Find similar papers."

It should move toward:

Understand My Research
        ↓
Understand the Research Ecosystem
        ↓
Understand Research Trajectories
        ↓
Find Meaningful Gaps
        ↓
Discover Unexpected Intersections
        ↓
Generate Testable Hypotheses
        ↓
Design Experiments
        ↓
Find Potential Collaborators
        ↓
Human Scientific Validation


The goal is not to automate science.

The goal is to help researchers see scientific connections that are
difficult to discover manually.

The Question Behind ResearchCollision
Traditional research discovery asks:

"What is similar to what I already know?"

ResearchCollision asks:

"What could collide with what I already know?"

<p align="center">
<strong>ResearchCollision</strong>

<br>
<em>Discover the research connections you didn't know to search for.</em>

<br><br>

⭐ Star the repository if you find the idea interesting.

</p>
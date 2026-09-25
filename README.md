# ResearchCollision

**Evidence-Aware Agentic AI for Discovering Non-Obvious Research Connections — with a reproducible, evidence-grounded evaluation harness.**

ResearchCollision combines researcher profiles and scholarly literature to
propose candidate research intersections, gaps, hypotheses, and experiment
designs — and the repository ships a full offline-capable evaluation harness
that measures whether those outputs are *useful and grounded in real evidence*
against a v1 pilot reference evaluation, with a v2 dataset and repeated
experiments currently under construction.

This is a research project, not a completed study. Every claim in this README
is aligned with what the repository actually contains; planned phases are
explicitly marked as pending. See [Current Experimental Status](#current-experimental-status).

---

## What this project is (and is not)

ResearchCollision tries to answer: *"What could collide with what I already
know?"* — i.e., which cross-disciplinary research connections, gaps, and
hypotheses are worth a human investigating next.

- It **proposes candidates** (intersections, gaps, hypotheses, experiment
  plans) and grounds them in retrieved literature evidence.
- It **does not claim** scientific novelty, collaboration intent, or that a
  connection is guaranteed to be underexplored. Outcomes require human
  validation.
- Every externally sourced claim carries an evidence status:
  `VERIFIED` / `INFERRED` / `SPECULATIVE` / `UNKNOWN`.
- The system and its evaluation harness **must never fabricate** researchers,
  universities, papers, DOIs, URLs, findings, datasets, funding, positions, or
  collaboration intentions. `UNKNOWN` is preferable to an unsupported claim.

The application follows a modular monolith: a FastAPI backend with specialized
agents (research DNA, literature, paper analysis, trajectory, gap, intersection,
evidence verification, hypothesis, experiment, paper writing, ranking) behind
provider abstractions for literature (OpenAlex, arXiv, Crossref, Semantic
Scholar, PubMed), LLMs (mock, OpenAI-compatible, OpenRouter), and embeddings.

---

## Current status (verified against the repository)

- **v1 pilot evaluation exists.** A single-run, descriptive 12-case × 4-system
  evaluation was executed on a real, publicly traceable case-study dataset
  (see [v1 evaluation](#v1-evaluation-frozen-pilot)).
- **v1 authoritative artifacts are frozen.** `backend/datasets/v1/` is a
  byte-identical snapshot; per-file SHA-256 hashes are recorded in
  `backend/datasets/v1/MANIFEST.json`. v1 must not be silently modified.
- **Experiment infrastructure is implemented.** `backend/evaluation/` contains
  the offline-capable runner, systems, metrics, report and failure analysis,
  human-rating templates, blind-ID handling, prompt archive/registry, and the
  v2 dataset build with request optimization.
- **Reproducibility infrastructure exists.** Frozen sampling protocol, repeated
  experiment protocol, seed plumbing, immutable prompt archive, validation
  script, and an offline test suite (see
  [Reproducibility & provenance](#reproducibility-and-provenance)).
- **v2 dataset construction is the current experimental gate.**
  - `backend/datasets/v2/candidate_frame.json` — frozen deterministic candidate
    frame (96 candidate pairings from the 30-domain pool, seed `20260925`).
  - `backend/datasets/v2/corpus_query_cache.json` — populated OpenAlex query
    cache (30 distinct queries, one response each).
  - `backend/datasets/v2/candidate_population.json` — screening decisions
    (30/30 queries completed; **87 eligible**, 9 data-based exclusions, **0**
    provider-failure exclusions).
  - The **≥50-case v2 dataset has NOT yet been completed**. `dataset_v2.json`
    and `sampling_manifest.json` do not exist yet.
- **Repeated multi-seed experiments have NOT yet been completed.**
- **Inferential statistics have NOT yet been computed.**
- **Human expert evaluation has NOT yet been performed.**
- **The project is therefore NOT publication-ready as a completed empirical
  paper.** The current manuscript is a single-run, descriptive draft with
  explicitly stated scope limits.

---

## Current Experimental Status

| Category | Items | Status |
|---|---|---|
| **Implemented infrastructure** | FastAPI app + agents + providers; evaluation harness (`backend/evaluation/`); v2 datav2 build/sampling/validation (`evaluation/datav2/`); prompt archive (`experiments/prompts/v1/`); case-sampling protocol (frozen), experiment protocol, reproducibility guide; offline test suite; frontend UI | **DONE** |
| **Completed experiments** | v1 pilot: 12 cases × 4 systems (`keyword`, `embedding`, `llm_only`, `pipeline`), single run, descriptive; synthetic demo baseline runs; OpenAlex v2 screening gate (30/30) | **DONE** (bounded scope, see below) |
| **Pending experiments** | v2 corpus pulls + ≥50-case dataset + validation; repeated multi-seed experiments (seeds 0–4) with immutable per-seed outputs; inferential statistics (bootstrap CIs, Friedman, Wilcoxon+Holm, effect sizes); human expert evaluation (blind, ≥3 independent domain experts); manuscript rewrite + final audit | **NOT DONE** |

Bounded scope of the completed work: the v1 pilot used the **mock LLM /
mock embeddings providers** with real literature retrieval over a fixed
snapshot, measured once, on a dataset whose topics/evidence references are
machine-generated heuristics (not expert gold) and whose researcher personae
are illustrative. The v2 OpenAlex screening is a dataset-construction gate
(not a system evaluation). None of this establishes an empirical benchmark.

---

## Repository structure

Only paths that actually exist are listed.

```
backend/
  app/                       FastAPI application
    api/v1/                  REST routes (auth, profiles, papers, gaps, intersections,
                             hypotheses, collaborations, evidence, reports, ...)
    agents/                  Agent implementations + versioned prompts (prompts/*.txt)
    providers/               Literature (OpenAlex, arXiv, Crossref, Semantic Scholar,
                             PubMed, mock), LLM (mock, OpenAI-compatible, OpenRouter),
                             embeddings
    services/  db/  schemas/ core/  workers/
  evaluation/                Evaluation harness (offline-capable): runner, systems,
                             metrics, report, failures, human-rating templates, prompt
                             archive/registry; datav2/ (v2 dataset build, sampling,
                             validation, frozen 30-domain pool); data/ (v1 datasets)
  datasets/
    v1/                      Frozen v1 pilot snapshot + MANIFEST.json (SHA-256 pins)
    v2/                      v2 in progress: candidate_frame.json (frozen),
                             corpus_query_cache.json, candidate_population.json
    feasibility_report.md    v2 corpus-access feasibility audit (protocol §3K)
  experiments/prompts/v1/    Immutable prompt archive + MANIFEST.json (per-file SHA-256)
  evaluation_out_real_v1/    v1 pilot run output (immutable): results.json/csv,
                             report.md, failure_analysis.json, blind_key.json,
                             human_ratings_template.csv
  evaluation_out_real_llm_v1/  v1 pilot run output (immutable; basis for the manuscript)
  research_paper/            Manuscript deliverables (single-run descriptive draft),
                             audits, tables/, figures/, appendix/, .tex/.bib sources
  tests/                     Offline test suite (pytest)
  CASE_SAMPLING_PROTOCOL.md  Frozen v2 sampling protocol (v1.0.0)
  EXPERIMENT_PROTOCOL.md     Repeated-experiment protocol (execution gated on v2 dataset)
  REPRODUCIBILITY.md         Reproduction guide (environment, seeds, determinism, immutability)
frontend/                    React + TypeScript UI (Vite, Tailwind, Vitest, Playwright)
scripts/                     seed.py (demo/synthetic data), health_check.py
docs/, sample_data/, evaluation/, data/   Empty placeholders (note: the authoritative
                                          evaluation harness is backend/evaluation/)
Makefile  docker-compose.yml  .env.example  LICENSE  .gitignore
```

---

## v1 evaluation (frozen pilot)

**What it is.** A pilot evaluation of the discovery pipeline and comparison
baselines over **12 real case studies** (48 pairings: 12 cases × 4 systems —
`keyword`, `embedding`, `llm_only`, `pipeline`), executed as a **single run,
single seed, descriptive measurement**. Dataset `real_case_study_v1`
(content SHA-256 `09d84b77...`) was built from publicly traceable OpenAlex
records on 2026-09-21: source papers are real; topics and evidence references
are machine-generated heuristics (not expert gold); gap annotations do not
exist (gap-relevance reported n/a); the two "researchers" per case are
illustrative domain personas, not real named individuals.

**Authoritative artifacts (immutable):**

- `backend/evaluation/data/real_case_study_v1.json` — 12-case dataset (source)
- `backend/evaluation/data/real_case_specs_v1.json` — case specifications
- `backend/evaluation/data/demo_discovery.json` — **synthetic** evaluation
  fixture; clearly labeled, NEVER real research evidence
- `backend/datasets/v1/` — read-only snapshot of the above + `MANIFEST.json`
  recording SHA-256 per file (e.g. `real_case_study_v1`
  `90fd9f178a00ce36...`). **v1 must not be silently modified or merged with v2.**

**Pilot outputs (immutable):** `backend/evaluation_out_real_v1/` and
`backend/evaluation_out_real_llm_v1/` contain `results.json`/`results.csv`,
`report.md`, `failure_analysis.json`, `blind_key.json`, and a blank
`human_ratings_template.csv` (recording template only — no human ratings exist).

**Measurements are descriptive, not a benchmark:** system totals were keyword
41 / embedding 36 / llm_only 53 / pipeline 58; the pipeline produced evidence
for **8 of 12** cases, with the 4 failures recorded verbatim (`table_d`,
appendix B). There are **no** confidence intervals, statistical tests, error
bars, system ranking, or human ratings, and the manuscript says so explicitly
(see `backend/research_paper/README.md`, `AUDIT.md`).

**v1 does not represent a publishable final benchmark.**

---

## v2 evaluation (in progress — current gate)

Intended v2 workflow, with current stage marked:

```
frozen sampling protocol (CASE_SAMPLING_PROTOCOL.md, v1.0.0)     [DONE — frozen]
30-domain pool (evaluation/datav2/domain_pool_v1.json)           [DONE]
candidate frame (96 pairings, seed 20260925)                     [DONE — frozen]
corpus query cache (30 distinct queries)                         [DONE]
OpenAlex screening -> eligibility decisions                      [DONE — 30/30]
   (candidate_population.json: 87 eligible / 9 EX1 / 0 EX2)
corpus pulls + v2 dataset assembly (>=50-case target)            [PENDING — NEXT GATE]
sampling manifest + offline validation (validate_datasets.py)    [PENDING]
repeated experiments, seeds 0-4, immutable experiments/v2/seed<N>[PENDING]
inferential statistics (CIs, Friedman, Wilcoxon+Holm, effects)   [PENDING]
human expert evaluation (blind, >=3 domain experts, Fleiss kappa)[PENDING]
manuscript update + audits                                       [PENDING]
```

**Current stage: screening complete; the full v2 build (corpus pulls +
dataset assembly) is the next gate.** Screening ran with cache-first request
optimization (each distinct query fetched once; the cache is reused on resume)
and respected OpenAlex rate limits (Retry-After honored; hard cooldown aborts
with exit code 2 and never becomes an evidence exclusion). Corpus availability
and rate limits remain an external dependency — see
`backend/datasets/feasibility_report.md` for the earlier access audit and
`CASE_SAMPLING_PROTOCOL.md` for EX1/EX2 handling rules.

---

## Reproducibility and provenance

The repository ships reproducibility infrastructure and points to the
authoritative documents rather than duplicating them:

| Concern | Where it is documented |
|---|---|
| Frozen case-sampling protocol, corpus roles, EX1/EX2 rules | `backend/CASE_SAMPLING_PROTOCOL.md` |
| Repeated-experiment protocol (execution gated on v2 dataset + audit) | `backend/EXPERIMENT_PROTOCOL.md` |
| Environment, seed semantics, deterministic vs stochastic, failure recording, immutability | `backend/REPRODUCIBILITY.md` |
| Immutable prompt archive + per-file SHA-256 | `backend/experiments/prompts/v1/` (+ `MANIFEST.json`) |
| v1 snapshot hashes | `backend/datasets/v1/MANIFEST.json` |
| Offline v2 artifact validation | `backend/evaluation/datav2/validate_datasets.py` |
| Claim-by-claim manuscript verification | `backend/research_paper/AUDIT.md`, `FINAL_AUDIT.md`, `SOURCE_INVENTORY.md` |

Key invariants enforced by the infrastructure:

- The `--seed N` argument is plumbed end-to-end; repeated experiments are
  designed to write to immutable per-seed directories
  (`experiments/v2/seed<N>`, to be created by that phase) that record their
  `prompt_versions.json` hashes against the archive.
- Provider failures are recorded, never silently dropped, and **never** treated
  as evidence exclusions (EX2 is an error condition, not an exclusion).
- Generated artifacts retain provenance (dataset content SHA-256, timestamps,
  provider/retrieval records, configuration with secrets redacted).

Offline commands (safe, no live corpus access):

```bash
cd backend
python -m pytest -q                                       # full offline test suite
python -m evaluation.datav2.validate_datasets --root datasets/v2
  # offline v2 artifact checks; dataset-dependent checks activate after the
  # full build writes sampling_manifest.json / dataset_v2.json
python -m evaluation.run \
  --dataset evaluation/data/demo_discovery.json \
  --systems keyword,embedding,llm_only,pipeline \
  --out-dir eval_out
  # offline synthetic demo run (mock providers); numbers are NOT real performance
```

See `backend/evaluation/README.md` for the full harness quickstart.

---

## Testing

Latest verified status (re-run offline against the current tree):

- **Backend (pytest): `174 passed, 8 skipped`** — `python -m pytest -q` inside
  `backend/` (offline; live/`llm_live`/`literature_live` markers are skipped by
  default per `backend/pytest.ini`).
- **Frontend (Vitest): `8 passed` (2 files)** — `npm run test` in `frontend/`.
- Playwright E2E spec exists (`frontend/e2e/`) and runs via `npm run e2e`.

These are **offline development/test results**. They do **not** constitute
completion of the live v2 experiment, repeated experiments, statistics, or
human evaluation — those remain pending and must not be inferred from a green
test suite.

---

## Research integrity

- No fabricated experimental results exist or will be added. Missing or failed
  steps are reported as missing or failed.
- Failed provider requests are recorded and are **never** interpreted as
  evidence exclusions.
- v1 pilot artifacts (`backend/evaluation/data/*_v1*.json`,
  `backend/datasets/v1/`, `backend/evaluation_out_*_v1/`) are preserved and
  immutable; v2 is never merged into v1.
- Generated artifacts must retain provenance (source, timestamps, content
  hashes, prompt versions, seeds).
- **Publication-readiness claims depend on completing the outstanding
  experimental phases** (v2 dataset, repeated experiments, statistics, human
  evaluation, audit). The project is not currently publication-ready as a
  completed empirical study.

---

## Setup and usage

Requirements: Python **3.10+** (verified: 3.10.0), Node.js 20+, npm, git.
Optional: Docker / Docker Compose for the containerized app.

### Offline development / testing

```bash
# backend
cd backend
python -m venv .venv
# activate: .venv\Scripts\activate (Windows) | source .venv/bin/activate (Linux/macOS)
pip install -r requirements.txt -r requirements-dev.txt

# frontend
cd ../frontend
npm install

# run the app locally (offline OK for the UI; mock providers by default)
cd ../backend
python -m uvicorn app.main:app --reload --port 8000   # or: make backend
cd ../frontend
npm run dev                                            # or: make frontend
```

- API docs: http://localhost:8000/docs · UI: http://localhost:5173
- Optional demo data (synthetic): `make seed` — creates
  `demo@researchcollision.dev` / `demo1234` plus clearly fictional demo
  researchers/papers. Demo credentials are for local development only.
- Convenience targets are in `Makefile` (`make install`, `make dev`,
  `make test-backend`, `make lint`, `make typecheck`, `make seed`,
  `make docker-up`).
- Environment variables: copy `.env.example` to `.env`. `.env` is
  git-ignored; secrets are never committed.

### Corpus-dependent experimental execution (gated)

Live operations (OpenAlex screening/builds, real evaluation runs) are
**rate-limited and protocol-gated**:

```bash
cd backend
python -m evaluation.datav2.build --root datasets/v2 --screen-only  # screening gate (cached)
python -m evaluation.datav2.build --root datasets/v2 --build        # full v2 build (requires authorization)
```

- These honor `Retry-After`; a hard cooldown aborts with exit code 2 and never
  fabricates results. Full-build execution requires authorization per the
  phase gates and is paused until corpus access is healthy.
- Do **not** bypass rate limits (no proxies / IP rotation / undocumented
  endpoints / concurrency escalation).
- Real evaluation runs (v1-style) are documented in `backend/evaluation/README.md`
  and must follow `REPRODUCIBILITY.md` (set `EVALUATION_FORCE_OFFLINE=0` only
  when intentionally running live).

---

## Known limitations / dependencies

- **External corpus availability** (OpenAlex, arXiv, PubMed) is a dependency;
  IP-level cooldowns can block the v2 build entirely (`backend/datasets/feasibility_report.md`).
- v2 screening decisions cover the 96-pairing frame; the ≥50-case dataset and
  downstream experiments are outstanding.
- The v1 pilot is single-run and descriptive; it cannot support inferential or
  comparative claims.
- Human expert ratings and preregistration records, if any, will be claimed
  only when actually performed.

---

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.
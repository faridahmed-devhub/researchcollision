# CODE_QUALITY_FINAL_REPORT.md

**Repository:** ResearchCollision
**Date:** 2026-09-29
**Method:** static review of `backend/app/`, `backend/evaluation/`, frontend, scripts, packaging,
plus live execution of the offline test suites (deterministic, mock-provider mode).
**Scope rule applied:** no broad refactor is recommended or performed; findings are triaged by
impact on **correctness, reproducibility, security, or research validity**. Cosmetic rework is
deliberately out of scope for finalization.

---

## 0. Verdict summary

| Dimension | Status |
|---|---|
| Automated tests | **PASS** — backend `174 passed, 8 skipped` (102 s, offline); frontend Vitest `8 passed` (2 files) |
| Lint/typecheck gate | Not currently runnable via Makefile (`npm run lint/format/typecheck` do not exist); ruff available for backend |
| Research-integrity hardening | Strong (mock labeling, failure recording, prompt archive, no fabricated results) |
| Security posture (application) | Good for a research prototype; one packaging exposure (C1) |
| Reproducibility-of-code | Good seed plumbing + offline defaults; several latent issues below |
| Residual debt | Deferred to `PROJECT_CLEANUP_PLAN.md`; none blocks the manuscript finalization |

---

## 1. CRITICAL / HIGH findings

### C1 — Docker image can bake `.env`, `.venv`, and the SQLite DB (no `.dockerignore`)
`backend/Dockerfile` uses `COPY . .`; no `.dockerignore` exists at repo root or `backend/`.
The backend image therefore contains `backend/.env` (real-provider config: internal
`OPENAI_BASE_URL`, `LLM_MODEL`, key placeholder), `backend/.venv/`, `backend/data/researchcollision.db*`,
`__pycache__/`, and pytest/ruff caches.
**Impact:** secret/config exposure + multi-hundred-MB image bloat.
**Fix (cleanup plan):** add `.dockerignore`; never bake `.env` (use runtime env/`env_file`).

### C2 — Silent embedding fallback to mock masks provider failure (`app/providers/embeddings/factory.py:15-18`)
```python
try:
    return SentenceTransformerProvider()
except Exception:
    return MockEmbeddingProvider()
```
Any failure of the real provider silently degrades to the deterministic mock baseline with no trace.
**Impact:** application-level results could be labeled with real-embedding expectations while
actually being mock vectors; operators get no signal.
**Note:** the paper's *evaluation* embedding baseline intentionally uses `MockEmbeddingProvider`
(no pretrained model involved) — the paper's numbers are unaffected by this bug.
**Fix (deferred):** log-and-raise or log-and-mark provider as `mock_fallback` with provenance.

### H1 — Dead duplicate API module `app/api/v1/results.py` (214 L)
`results.py` is not included in `app/api/v1/__init__.py` (router aggregation list verified) yet
fully re-implements the `intersections`/`gaps`/`hypotheses`/`collaborations`/`evidence` routes
(e.g. `list_intersections` in `results.py:40` vs `intersections.py:22`), including a local copy
of `select_evidence_ids`. Two sources of truth for the same endpoints.
**Fix:** delete the module (or register it and delete the decomposed routers); ensure tests still pass.

### H2 — `PubmedProvider` is unreachable
`app/providers/literature/pubmed.py` exists (with tests in `test_pubmed_parse.py`) but is not
referenced by `literature/factory.py`, whose fallback order is
openalex → semantic_scholar → crossref → arxiv.
**Impact:** PubMed search is never actually used at runtime; README/provider claims mentioning
PubMed for the *app* are aspirational (the v2 build *does* pull PubMed records directly).
**Fix:** wire into the chain or annotate as planned.

### H3 — Retry re-runs can duplicate result rows (`app/workers/tasks/discovery_pipeline.py`)
Only `step_detect_gaps` deletes this job's prior rows before re-inserting
(`discovery_pipeline.py:350-356`). `step_discover_intersections`, `step_generate_hypotheses`,
`step_rank_collaborations`, and evidence steps do not clear prior output, so a retried job can
accumulate duplicate `ResearchIntersection` / `Hypothesis` / `CollaborationCandidate` rows.
**Impact:** correctness of stored discovery results on retries; downstream statistics could double-count.
**Fix (deferred):** transaction-block delete-then-insert per step keyed by `research_job_id`.

### H4 — `report_service._collect` loads all researchers globally (`app/services/report_service.py:73-76`)
`select(Researcher)` is unfiltered by workspace while every other entity in `_collect` is scoped to
`workspace_id`. In a multi-tenant deployment the researcher directory would leak across workspaces.

### H5 — Deprecated event-loop API inside async lifespan (`app/main.py:39-40`)
`__import__("asyncio").get_event_loop()` is called inside the async lifespan when starting the
embedded worker. This is the deprecated pattern and can bind to the wrong loop on 3.10+.
**Fix:** `asyncio.get_running_loop()`.

### H6 — Import-time global side effect in the harness (`backend/evaluation/baselines.py:41`)
`configure_offline_defaults()` runs at module import, mutating `os.environ` for the whole process.
It is idempotent and only reachable from tests/eval imports (`app/` never imports `evaluation.*`),
so blast radius is contained — still a non-obvious reproducibility foot-gun.

### H7 — `runner.py` reports stored (not recomputed) dataset hash
`runner.py:246` writes the dataset's `content_sha256` from the loaded metadata rather than
recomputing it. A tampered dataset would report its original hash. `validate_datasets.py` (v2)
recomputes; the v1-path manifest could too.

### H8 — Broad `except` in `prompt_registry.py:34`
A failure to read a prompt is silently mapped to `unknown` rather than surfacing — undermines the
immutability guarantee that seed runs record the exact prompt hash.

---

## 2. MEDIUM findings

| # | Finding | Location |
|---|---|---|
| M1 | v2 hash-label confusion: `DATASET_CARD.md` calls the recomputed *content* hash the file "sha256" while raw file SHA-256 differs; internally consistent with `build.py` but misleading | `datasets/v2/DATASET_CARD.md:646,702`, `evaluation/datav2/build.py` |
| M2 | Stratum table in DATASET_CARD rendered on one line (`''.join(rows)`) | `evaluation/datav2/build.py:682` |
| M3 | Module-level `_frame_map` mutated during card write — global mutable state | `evaluation/datav2/build.py:614-622` |
| M4 | Rate limiter and job-claim lock are per-process in-memory; multi-process deployments (e.g. multi-worker uvicorn) bypass them | `app/main.py:24-27`, `app/workers/worker.py:21` |
| M5 | Mixed ORM eras: legacy `self.db.query(...)` alongside 2.0 `select()` in the same codebase | `discovery_pipeline.py:157,251,351`, `paper_service.py:40,133`, `research_profiles.py:194` |
| M6 | `baselines.py:497` selects all `Paper` rows unfiltered; safe today only because the pipeline uses an isolated temp SQLite DB | `backend/evaluation/baselines.py:497` |
| M7 | Mojibake (encoding garbage) in source comments | `app/db/models/paper.py:10`, `job.py:13`, `gap.py:10` |
| M8 | Machine-specific absolute paths recorded inside committed metadata (`E:\AICode\...`) | `datasets/v1/MANIFEST.json:6,11,16`, `experiments/prompts/v1/MANIFEST.json:5`, `datasets/v2/sampling_manifest.json:3` |
| M9 | Hardcoded inline caps (`[:3]`/`[:5]`/`limit(300)`/`limit(50)`/`max_papers*2`) scattered | `discovery_pipeline.py`, `report_service.py:66`, `discovery.py:81` |
| M10 | `runner.py:194-214` duplicates blind-key/template logic that also lives in `evaluation/human.py:95,119` | `backend/evaluation/runner.py` |
| M11 | Config `secret_key` default is random-per-process (`config.py:25`) → JWTs invalidated on restart; also 31-byte test HMAC key triggers RFC 7518 warning | `app/core/config.py:25`, `backend/tests` |
| M12 | Historical `evaluation_out_real_llm_v1/report.md` (line ~212) was generated before the provider-aware `_limitations` fix and still says "mock LLM"; it is a frozen artifact and is intentionally NOT regenerated | `report.py:266-313` (fixed), `evaluation_out_real_llm_v1/report.md` (frozen) |

**M12 note (research validity):** the *manuscript* correctly discloses the provider; only the old
frozen report artifact differs, and project policy preserves it. No recipient of the paper is misled
because the paper does not cite that report as authoritative.

---

## 3. LOW / housekeeping findings

- L1 Unused symbols: `RateLimitAppError` (`exceptions.py:70`), `UNDEREXPLORED_LANGUAGE`
  (`constants.py:8`), `GapType` (`:46`), `EntityType` (`:85`), dead `repo_query` (`paper_service.py:87`),
  `_paper_window`/`SystemScore` (`baselines.py:112,126`), `all_expected_paper_ids` (`schemas.py:178,266`),
  unused schemas `PaperAnalysisOut`, `TrajectoryOut`, `PaperDraftCreate`, unused service
  `knowledge_graph_service.py` (zero callers).
- L2 `test_datav2_validation.py:47` contains an empty `pass` placeholder.
- L3 Stale bytecode `__pycache__/test_zz_real_papers_mock_llm_temp.*.pyc` (source deleted).
- L4 `frontend/vite.config.js` + `.d.ts` are tracked `tsc` outputs shadowing `vite.config.ts`
  (root cause: `tsconfig.node.json` composite without `noEmit`) — see project audit F3.
- L5 Makefile targets `lint/format/typecheck/e2e` call nonexistent npm scripts (project audit F4).
- L6 `VITE_API_BASE_URL` docker build arg is dead config (project audit F5).
- L7 Frontend has no Dockerfile / nginx while `docker-compose.yml` declares a build (project audit F6).
- L8 Empty placeholder dirs (`frontend/src/api,features,hooks,layouts,types,utils`,
  `frontend/tests/e2e`, top-level `evaluation/{datasets,metrics}`, `docs/`, `sample_data/`).
- L9 Orphaned runtime leftovers in `backend/` (`.pid`, `eval_*_run_*.log`,
  `_openrouter_free_models.txt`) — all correctly gitignored.
- L10 `research_paper/` contains ~20 scratch QA scripts + raster directories (`qa_pages/`,
  `_diff_iso/`, `_mupdf_pages/`, `caching_paper_deliverable_20260926/`, `figures/_orig_bars/`).
  Final keep/archive/remove disposition is in `PROJECT_CLEANUP_PLAN.md`.

---

## 4. Positive notes (what is solid)

- **Test discipline:** 182 collected, 174 pass (8 skipped = live/`llm_live`/`literature_live`, per
  `pytest.ini`); 64 tests directly guard evaluation integrity (metrics, failures, grounding /
  hallucination, blind ids, aggregation, builder, seed plumbing, prompt archive). Frontend: 8 pass.
- **Research-integrity rails:** mandatory `SYNTHETIC DEMO DATA` labeling in mock outputs; evidence
  statuses `VERIFIED/INFERRED/SPECULATIVE/UNKNOWN`; failures recorded not hidden; prompt archive
  with per-file SHA-256; seed plumbed end-to-end; `config.json` redacts secrets.
- **Security basics:** bcrypt, JWT with issuer, workspace ownership guards, 404-not-leak, bounded
  inputs, restricted CORS, no bare `except:`, no hardcoded credentials in source.
- **Architecture clarity:** provider abstraction (literature chain, LLM, embeddings), agents behind
  versioned prompts, isolated temp DB for the pipeline system, immutable per-seed experiment dirs.
- **Schema hygiene:** Alembic migration table names match models exactly (33 tables), FTS5 fallback
  is graceful.
- **No TODO/FIXME/HACK debris; code is broadly readable and consistently typed.**

---

## 5. Recommended remediation (ordered; all deferred, none required for the manuscript gate)

1. `backend/.dockerignore` + never bake `.env` (C1). **Security.**
2. Decide dead code: delete `results.py`, wire-or-annotate PubMed (H1, H2). **Maintenance.**
3. Make pipeline steps idempotent on retry (H3). **Correctness.**
4. Make embedding fallback loud + provenance-marked (C2). **Research integrity (app layer).**
5. Scope `_collect` researchers to workspace (H4); fix event loop (H5). **Correctness/security.**
6. Recompute dataset hash at report time (H7); tighten `prompt_registry` except (H8). **Repro.**
7. Frontend/package hygiene: `noEmit` fix + untrack `vite.config.js/.d.ts`, Makefile npm targets,
   drop-or-fix frontend container service, `.gitkeep` or remove placeholder dirs (L4–L8).
8. Optional de-lint: ruff/Mypy can be added as a Makefile `check` target; Drop the 31-byte test key.

None of the above affect the correctness of the manuscript numbers, which are sourced from the
frozen `results.json` and validated independently (see `PAPER_CORRECTION_REPORT.md`,
`render_manifest.json`).
# FINAL_PROJECT_AUDIT.md

**Repository:** ResearchCollision (evidence-aware agentic discovery framework + reproducible evaluation harness)
**Audit date:** 2026-09-29
**Auditor note:** read-only audit of the working tree at commit `9ebd5900b2c31c89e1fbb34b63e0851d575ff9b6` (branch `main`).
No files were modified to produce this audit; proposed actions are deferred to `PROJECT_CLEANUP_PLAN.md`.

---

## 1. Scope and purpose

This audit inventories what the repository actually contains, separates authoritative/immutable
artifacts from generated or scratch material, reviews security posture, and records discrepancies
between documented status (`README.md`, protocol documents) and ground truth on disk. It feeds the
code-quality report (`CODE_QUALITY_FINAL_REPORT.md`), the reproducibility freeze
(`REPRODUCIBILITY_FINAL.md`), and the cleanup plan (`PROJECT_CLEANUP_PLAN.md`).

Research-integrity invariants that were checked and held:

- v1 pilot dataset and outputs remain immutable (see §7 hashes).
- No human ratings exist and none are claimed (`human.provided=false` in `results.json`).
- Provider failures are recorded verbatim (4 pipeline failures), never converted to successes.
- No fabricated experiments, results, or credentials were introduced by this audit.

---

## 2. Repository architecture (what-is-where)

```
ResearchCollision/
├── backend/                 FastAPI mono-backend + evaluation harness + datasets + manuscript
├── frontend/                React 18 + TypeScript (Vite 5, Vitest, Playwright)
├── scripts/                 seed.py, health_check.py
├── evaluation/              EMPTY shell (datasets/, metrics/ subdirs are empty)
├── docs/                    EMPTY (not even .gitkeep)
├── sample_data/             EMPTY
├── data/                    data/.gitkeep only
├── Makefile                 dev/test/lint targets (some targets broken — see §9)
├── docker-compose.yml       backend + worker + frontend services
├── .env.example             template (git-tracked, no secrets)
├── .gitignore               solid coverage of secrets/logs/db/pdfs
└── LICENSE                  Apache-2.0
```

**Authoritative components that matter for the project finalization:**

| Area | Location | Status |
|---|---|---|
| Application (FastAPI, agents, providers, workers) | `backend/app/` | Implemented (see §3) |
| Evaluation harness (offline-capable) | `backend/evaluation/` | Implemented; basis for manuscript numbers |
| v1 frozen pilot dataset + outputs | `backend/datasets/v1/`, `backend/evaluation_out_real_llm_v1/` | Immutable ✓ |
| v2 dataset build | `backend/datasets/v2/` | **BUILT (60 cases); untracked in git** |
| v2 experiments (seeds 0–4) | `backend/experiments/v2/` | NOT STARTED (does not exist) |
| Immutable prompt archive | `backend/experiments/prompts/v1/` | Done, hashes pinned |
| Manuscript + render + QA | `backend/research_paper/` | Current draft (single-run, descriptive) |
| Backend test suite | `backend/tests/` | 31 test modules |
| Frontend app + tests | `frontend/src`, `frontend/__tests__`, `frontend/e2e` | Implemented |

---

## 3. Application component inventory (`backend/app/`, ~119 files, ~8k LOC)

- **Entry:** `app/main.py` — FastAPI app, lifespan (logging, FTS5 init, embedded worker), CORS,
  per-IP in-memory rate limiter, exception handlers, `GET /health`, API mounted at `/api/v1`.
- **API (`app/api/v1/`, 13 route modules):** auth, workspaces, research-profiles (+CV upload),
  researchers, papers, discovery (jobs lifecycle + paper-draft export), intersections, gaps,
  hypotheses, collaborations, evidence, reports, meta/provider-status. Ownership guards in
  `api/dependencies.py`.
- **Agents (`app/agents/`):** profile, literature, paper analysis, trajectory, gap, intersection,
  hypothesis, verification, paper writer, ranking (algorithmic). Versioned prompt files in
  `app/agents/prompts/*.txt`.
- **Providers (`app/providers/`):** literature chain (openalex → semantic_scholar → crossref →
  arxiv; mock appended only when allowed), LLM (mock / openai_compatible / openrouter), embeddings
  (mock / sentence_transformer). `MockEmbeddingProvider` is a deterministic MD5 token-hash,
  256-dim L2-normalized (cosine) baseline — no pretrained model is used.
- **Workers (`app/workers/`):** worker loop + `JobRunner` + `tasks/discovery_pipeline.py`
  (ordered discovery steps; resilient per-item failure logging).
- **Services (`app/services/`, 14):** vector, literature, paper, evidence, cv, settings,
  paper_draft, report, intersection, hypothesis, trajectory, collaboration, knowledge_graph
  (unused), settings.
- **DB (`app/db/`):** ~18 model modules + repositories; SQLite (WAL + FK on); Alembic single
  squashed initial migration `eaae242b764c`. Migration table names match models exactly (33 tables).

**Security posture (application):** bcrypt password hashing; JWT (HS256, issuer bound, exp/sub
required); ownership checks on workspace-scoped resources; 404-not-leak patterns; CORS restricted
to localhost origins with `allow_credentials` (no wildcard). No credentials hardcoded in `app/`.
`example` secrets found in tracked docs are placeholders only (see §10 for the one caveat).

---

## 4. Evaluation harness (`backend/evaluation/`)

- `run.py` / `runner.py` — CLI → per-case/per-system execution → aggregation → artifacts.
- `baselines.py` — four systems: `keyword` (token-overlap lexical baseline), `embedding` (mock
  cosine baseline), `llm_only`, `pipeline` (isolated temp SQLite).
- `metrics.py`, `failures.py`, `human.py` (blind keys + rating templates + IRR), `report.py`
  (**provider-aware `_limitations()`**), `variants.py` (live / live_cache / analysis_cache /
  frozen_v2), `batch.py`, `experiment.py` (immutable per-seed dirs), `environment.py`
  (offline defaults), `prompt_archive.py`, `prompt_registry.py`, `schemas.py`.
- Run command: `python -m evaluation.run --dataset <path> --systems keyword,embedding,llm_only,pipeline --seed N`.
- `datav2/` — frozen 30-domain pool, sampling protocol, build (screening + corpus pulls), and
  `validate_datasets.py` (offline v2 artifact validation including the 60-case dataset).

## 5. Datasets

**v1 (frozen pilot):** `backend/datasets/v1/` pins 3 files (see §7 hashes); byte-identical copies
in `backend/evaluation/data/`. 12-case real case-study dataset built from publicly traceable
OpenAlex records; topics/evidence references are machine-generated heuristics (not expert gold);
researcher personae are illustrative.

**v2 (built):** `backend/datasets/v2/` contains:
- `candidate_frame.json` (frozen, 96 pairings, seed 20260925) — tracked.
- `corpus_query_cache.json` (30 distinct queries) — tracked, modified in working tree.
- `candidate_population.json` — 96 screened → 87 eligible / 9 excluded (all EX1). — untracked.
- `dataset_v2.json` — **60 cases × 10 source papers (600 entries, 151 unique works)**; providers
  openalex 430 / arxiv 120 / pubmed 50; all rows schema-valid. — untracked.
- `sampling_manifest.json`, `dedup_audit.json` (2,589 → 2,525 kept, 64 deduped), `DATASET_CARD.md`
  (documents server-side content SHA-256 `826263ae…`). — untracked.

> **FINDING F1 (documentation staleness):** `README.md` states "`dataset_v2.json` and
> `sampling_manifest.json` do not exist yet" and lists v2 corpus pulls as PENDING. That is no
> longer true: the ≥50-case v2 dataset IS built (60 cases) with a sampling manifest and dedup
> audit. The v2 *experiments* (seeds 0–4), inferential statistics, and human evaluation remain
> pending as documented. README needs a status refresh (see §11).

> **FINDING F2 (immutability state):** the five v2 artifacts (`candidate_population.json`,
> `dataset_v2.json`, `sampling_manifest.json`, `dedup_audit.json`, `DATASET_CARD.md`) and
> `evaluation/variants.py` are **untracked** in git. Declaring a freeze before committing is
> contradictory; the cleanup plan recommends committing (via git, if authorized) or at minimum
> recording their hashes.

## 6. Prompt archive and experiment infrastructure

- `backend/experiments/prompts/v1/` — 10 `.txt` prompt files + `MANIFEST.json` (per-file SHA-256)
  + `README.md`. All ten hashes match the live `app/agents/prompts/*.txt` sources. Two prompts
  (`collaboration_ranking.txt`, `verification.txt`) are marked `unused`.
- `backend/experiments/v2/` — **does not exist**. No repeated multi-seed runs have been executed.
  Per `REPRODUCIBILITY.md` each seed writes an immutable `experiments/v2/seed<N>/`.

## 7. Immutability verification (hashes)

v1 snapshot (from `MANIFEST.json`, verified byte-identical in both copies on 2026-09-29):

| File | Size | SHA-256 |
|---|---|---|
| `real_case_study_v1.json` | 448,418 | `90fd9f178a00ce36757e5cfebfabfac82ab675583c4eb95a2b85cec503345e59` |
| `real_case_specs_v1.json` | 6,914 | `fd3c16deae01e94c1529264082039569e2430aedd3f90172257094796dd60bac` |
| `demo_discovery.json` | 12,436 | `2a0a7125bdcfac9edbdeb279dbb286e5cf040148de5c890480f07ba45ab42b6b` |

v1 pilot outputs (`evaluation_out_real_llm_v1/`, basis for the manuscript) — source of truth for
the paper: `results.json` (188 records; 55 intersection / 50 hypothesis / 83 gap; keyword 41 /
embedding 36 / llm_only 53 / pipeline 58; coverage 12/12/12/8; `human.provided=false`), plus
`failure_analysis.json`, `report.md`, `blind_key.json`, blank `human_ratings_template.csv`.
Immutable by project rule; **not regenerated** by the correction pass.

## 8. Manuscript deliverables (`backend/research_paper/`)

**Authoritative source (master):** `paper.md` (278 lines, 20,507 bytes) — single-run, descriptive
12-case/4-system manuscript; corrected in the correction pass (see `PAPER_CORRECTION_REPORT.md`).
**Current rendered artifacts:**
- `research_paper.pdf` — 16 pages, A4 (595×842), 640,323 bytes, fonts embedded.
- `research_paper.html` — 55,002 bytes.
- `render_manifest.json` — 55/55 QA checks PASS; 7 rendered references; 4 verbatim failure bytes.
- `qa_run.py` (55 checks), `qa_bars.py`, `bar_proportionality_qa.json` (PASS) — the QA gate.
- `render_research_paper.py` — Chromium (Edge headless) renderer, `@page` footer mechanism.

**Supporting sources:** `tables/` (A–D CSV+MD), `figures/` (3 SVG), `appendix/` A–D, canonical
bib `Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.bib` (15 provenance entries),
legacy `references.bib` (11, untouched). Canonical-named deliverable copies
(`Farid_Ahmed_…{.md,.tex,.bib,.pdf}`) are byte-identical copies, last synced before the correction
pass — **re-sync required during Phase 20** (see §11/F-canonical).

**Audit trail:** `AUDIT.md`, `FINAL_AUDIT.md`, `SOURCE_INVENTORY.md`, `MANUSCRIPT_GAP_AUDIT.md`,
`PAPER_CONTENT_AUDIT.md` (with §15 correction status), `PAPER_CORRECTION_REPORT.md`,
`FINAL_RENDER_QA.md`.

**Scratch/throwaway (audit candidate, see cleanup plan):** `qa_ascii.py`, `qa_deep.py`,
`qa_drawings.py`, `qa_figs.py`, `qa_fonts.py`, `qa_geometry.py`, `qa_glyph_ink.py`, `qa_reports.py`,
`qa_spot.py`, `qa_symbols.py`, `qa_toc.py`, `qa_toc_layout.py`, `_scratch_factcheck.py`,
`_qraster_qa.py`, `_vlayout_audit.py`, `_pdf_extract.txt`, `_diff_iso/`, `_mupdf_pages/`
(15 raster previews each), `caching_paper_deliverable_20260926/`, `figures/_orig_bars/`,
`html_qa_report.md`, `pdf_qa_report.md`, `visual_qa_report.md`, `pdf_content_integrity_report.md`,
`qa_pages/` (15 page rasters — currently stale at 15 vs 16 PDF pages; regenerated in Phase 20).

## 9. Frontend, scripts, packaging (housekeeping findings)

**Frontend:** React 18 + TS + Vite 5; 17 routed pages; `lib/api.ts` is a bare axios instance with
`baseURL: "/api/v1"` and auth/401 interceptors + `apiError`. Vitest: 2 spec files; Playwright: 1
spec (`e2e/auth.spec.ts`).

- **F3 — committed generated config shadows source:** `frontend/vite.config.js` and
  `frontend/vite.config.d.ts` are git-tracked `tsc` outputs. `tsconfig.node.json` sets
  `composite: true` without `noEmit`, so `npm run build` re-emits them. Vite prefers `.js`, so the
  compiled copy silently shadows `vite.config.ts`. Fix: add `noEmit`, untrack + delete.
- **F4 — broken Makefile targets:** `make lint/format/typecheck/e2e` call npm scripts
  (`lint`, `format`, `typecheck`, `test:e2e`) that do not exist in `package.json` (actual:
  `dev`, `build`, `preview`, `test`, `test:watch`, `e2e`).
- **F5 — dead build arg:** `VITE_API_BASE_URL` is passed by docker-compose but never read
  (api.ts hardcodes `/api/v1`).
- **F6 — frontend cannot be containerized:** `docker-compose.yml` declares a `frontend` build
  with no `frontend/Dockerfile` (and no nginx config), so `docker compose up --build` cannot
  succeed.
- **F7 — empty placeholder dirs:** `frontend/src/{api,features,hooks,layouts,types,utils}`,
  `frontend/tests/e2e/`, top-level `evaluation/{datasets,metrics}`, `docs/`, `sample_data/` are
  empty shells (without `.gitkeep`, so invisible to git). Create-or-delete decision deferred to
  cleanup plan.

**Scripts:** `scripts/seed.py` (155 L; idempotent demo user + researchers + papers + optional job),
`scripts/health_check.py` (54 L; env + provider + schema-diff + FTS probe, exit 0/1).

**Docker:** `backend/Dockerfile` (`python:3.11-slim`), frontend service broken (F6 above).

- **F8 — no `.dockerignore`:** `COPY . .` in the backend Dockerfile bakes `backend/.env`,
  `backend/.venv/`, `backend/data/researchcollision.db*`, `__pycache__/`, caches into the image —
  a secret-exposure and bloat risk. Highest-impact packaging finding.

## 10. Secrets and sensitive-config review

- `backend/.env` exists and is **gitignored** (verified via `git check-ignore`); never committed.
  Contents (reviewed, redacted here): `LLM_PROVIDER=openai_compatible`,
  `OPENAI_BASE_URL=http://203.96.189.126:11434/v1`, `LLM_MODEL=qwen2.5:7b`,
  `OPENAI_API_KEY=ollama` (Ollama-compat non-secret placeholder key), `OPENALEX_EMAIL=…`. This is
  the real-provider configuration redacted in the manuscript.
- **F9 — internal endpoint leaks into tracked docs:** the same URL appears verbatim in
  `backend/REPRODUCIBILITY.md:20` and `backend/research_paper/UPGRADE_PLAN.md:29`. The manuscript
  correctly discloses only "openai_compatible (identity redacted)". These two tracked docs expose
  a private LAN endpoint + organizational email. Recommendation: replace with redacted placeholder
  in those docs (they remain authoritative for provenance but need not carry the live address), or
  explicitly mark as internal. Not a credential leak (`ollama` key is not a secret), but a privacy
  hardening item.
- `git grep` scan of tracked files found no real API key/token on disk (only `.env.example`
  placeholders and the two endpoint references above).
- Runtime leftovers (gitignored): `backend/eval_llm_run.pid`, `.eval_real_llm.pid`,
  `eval_llm_run_{out,err}.log`, `eval_real_llm_{stdout,stderr}.log`, `_openrouter_free_models.txt`.

## 11. Current-project-status reconciliation (documented vs actual)

| Statement | Documented (README) | Actual on disk | Verdict |
|---|---|---|---|
| v1 pilot frozen | Yes | Yes (hashes match) | Consistent |
| v2 candidate frame frozen | Yes | `candidate_frame.json` exists | Consistent |
| v2 corpus pulls + ≥50-case build | **PENDING** | **Done: 60 cases** (`dataset_v2.json`) | **STALE** |
| sampling manifest/validation | PENDING | `sampling_manifest.json`, `dedup_audit.json` exist; `validate_datasets.py` ready | **STALE** |
| v2 experiments seeds 0–4 | NOT DONE | `experiments/v2/` absent | Consistent |
| inferential statistics | NOT DONE | not present | Consistent |
| human expert evaluation | NOT DONE | `human.provided=false` | Consistent |
| manuscript = single-run descriptive draft | Yes | yes | Consistent |

**Project-level finalization recommendations (top of list, no file renames/deletions here):**
1. Commit / pin the v2 dataset artifacts (F2) and `variants.py`, or explicitly record their hashes
   in a freeze manifest (delegated to cleanup plan; requires git authorization).
2. Refresh `README.md` status table to reflect the completed v2 build while keeping pending gates
   accurately pending (F1).
3. Regenerate/refresh the canonical-named deliverables from the current corrected `paper.md`
   during Phase 20 (F-canonical).
4. Redact the internal endpoint from the two tracked docs, or annotate as internal (F9).
5. Add `.dockerignore`, restore frontend containerization or drop the compose frontend service
   (F6/F8), fix Makefile npm targets (F4), fix the `vite.config.*` shadowing (F3).
6. Decide keep/archive/remove for scratch QA artifacts listed in §8 (final dispositions in
   `PROJECT_CLEANUP_PLAN.md`, Phase 22).

## 12. Finalization-gate context

The repository is NOT publication-ready as a completed empirical study (no repeated seeds, no
inferential statistics, no human ratings). The manuscript in `backend/research_paper/` is correctly
scoped as a single-run, descriptive, artifact-grounded draft. This audit confirms that framing is
consistent with repository contents and that no fabrication or immutability violation exists.
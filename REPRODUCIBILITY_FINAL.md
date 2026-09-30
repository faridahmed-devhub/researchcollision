# REPRODUCIBILITY_FINAL.md (freeze record)

**Repository:** ResearchCollision · commit `9ebd5900b2c31c89e1fbb34b63e0851d575ff9b6` (branch `main`)
**Freeze-review date:** 2026-09-29 (all VERIFIED values re-checked on this date on the authoring machine)
**Note:** authoritative long-form documents are `backend/REPRODUCIBILITY.md`, `backend/EXPERIMENT_PROTOCOL.md`,
`backend/CASE_SAMPLING_PROTOCOL.md`, and `backend/evaluation/README.md`. This file is the **final freeze record**
binding the manuscript's numbers to a concrete environment, inputs, and commands.

---

## 1. Environment (three-state record)

Legend: **CONFIGURED** = what the project documents/requires · **EXECUTED** = what the artifacts record ·
**VERIFIED** = re-checked on 2026-09-29.

| Ingredient | CONFIGURED | EXECUTED | VERIFIED |
|---|---|---|---|
| Python | 3.10+ (docs) | — | **3.10.0** (`C:\Users\HP\...\Python310`) |
| Node / npm | Node 20+ (README) | — | **v22.16.0** / npm **11.4.2** |
| SQLite | WAL + FK on | used by app + pipeline | present (`backend/data/researchcollision.db` ignored) |
| Render engine (paper) | headless Chromium/Edge | Edge `--print-to-pdf` | **Microsoft Edge 154.0.4258.37** |
| Key Python deps (resolved) | ranges in `requirements.txt` | — | fastapi **0.139.0**, uvicorn **0.49.0**, pydantic **2.13.4**, pydantic-settings **2.14.2**, SQLAlchemy **2.0.51**, alembic **1.19.1**, httpx **0.28.1**, numpy **1.26.4**, pandas **2.3.3**, scipy **1.15.3**, tenacity **9.1.4**, PyMuPDF **1.28.2**, pytest **9.1.1**, pytest-asyncio **1.4.0**, ruff **0.16.4**, mypy **2.3.1**, PyJWT **2.13.0**, bcrypt **5.0.0**, structlog **26.1.0**, beautifulsoup4 **4.14.3**, openpyxl **3.1.5** |
| LLM provider (real run) | `openai_compatible` (identity redacted) | `openai_compatible` | recorded in `results.json.config` |
| Embedding provider (eval run) | mock (not `sentence_transformer`) | `mock` | recorded in `results.json.config`; deterministic MD5-token-hash 256-dim L2-normalized vectors, no pretrained model |
| Literature chain | openalex → semantic_scholar → crossref → arxiv | recorded | recorded in `results.json.config` |
| Offline mode | default forced unless `EVALUATION_FORCE_OFFLINE=0` | `false` (live run) | recorded in `results.json.config` |
| Seed | `--seed N` plumbed | single run, **default seed 0** (not recorded in results.json; `--seed` omitted ⇒ 0) | consistent with docs |
| Generated-UTC of eval | — | `2026-09-23T11:43:34+00:00` | recorded in `results.json.generated_utc` |
| Generated-UTC of manuscript render | — | `2026-09-29T05:25:15+00:00` | `render_manifest.json` |

---

## 2. v1 pilot evaluation (the manuscript's empirical basis) — exact reproduction recipe

Input dataset: `backend/evaluation/data/real_case_study_v1.json` (immutable v1, content
`09d84b77...` embedded in results.json; snapshot pinned in `datasets/v1/MANIFEST.json`).

Recorded execution config (`results.json` → `config`): systems
`[keyword, embedding, llm_only, pipeline]`, `llm_provider=openai_compatible`, `embedding_provider=mock`,
literature chain `[openalex, semantic_scholar, crossref, arxiv]`, `offline_mode=false`.

Canonical command (URL/key are on the authoring machine only; identity redacted for the record):

```powershell
cd backend
$env:EVALUATION_FORCE_OFFLINE = "0"
python -m evaluation.run `
  --dataset evaluation/data/real_case_study_v1.json `
  --systems keyword,embedding,llm_only,pipeline `
  --seed 0 `
  --out-dir evaluation_out_real_llm_v1
```

The normal **offline, deterministic reproduction** (no real providers) of the same harness on the
demo fixture:

```powershell
cd backend
python -m evaluation.run --dataset evaluation/data/demo_discovery.json `
  --systems keyword,embedding,llm_only,pipeline --seed 0 --out-dir <tmp>
```

**Recorded outcomes that a reproduction must match** (`results.json`):
188 candidate records = 55 intersection / 50 hypothesis / 83 gap; per-system totals
keyword 41 / embedding 36 / llm_only 53 / pipeline 58; case coverage 12/12/12/8 (pipeline 8/12);
4 pipeline runtime failures with exact bytes
`causal_inference_x_clinical_ml: ReadTimeout: `, `gnn_x_protein_structure: ReadTimeout: `,
`rl_x_sim_to_real: ReadError: `, `clinical_nlp_x_ehr: ConnectError: All connection attempts failed`;
`human.provided=false`, ratings_count=0 (nothing fabricated).

**Honest determinism limits** (also documented in `REPRODUCIBILITY.md` §7): remote LLM sampling
depends on the endpoint honoring `seed`; seeding controls blind IDs and sampling trajectories but
**cannot** control endpoint nondeterminism or network/retry timing; transient failures are recorded,
never converted into successes.

---

## 3. Dataset provenance (single source of truth)

### v1 (frozen pilot) — VERIFIED byte-identical 2026-09-29

| File | Size bytes | SHA-256 (pin in `datasets/v1/MANIFEST.json`) |
|---|---|---|
| `real_case_study_v1.json` | 448,418 | `90fd9f178a00ce36757e5cfebfabfac82ab675583c4eb95a2b85cec503345e59` |
| `real_case_specs_v1.json` | 6,914 | `fd3c16deae01e94c1529264082039569e2430aedd3f90172257094796dd60bac` |
| `demo_discovery.json` | 12,436 | `2a0a7125bdcfac9edbdeb279dbb286e5cf040148de5c890480f07ba45ab42b6b` |

### v2 (built 2026-09-25, not yet used for experiments)

| Artifact | Hash / identity | State |
|---|---|---|
| `dataset_v2.json` | content SHA-256 `826263ae99a348b8cafc802e35a94afdd320c38d640cee553a22414cc3b126a4` | 60 cases × 10 source papers (600 entries, 151 unique works); schema-valid; openalex 430 / arxiv 120 / pubmed 50 |
| `candidate_frame.json` | seeded 20260925, 96 pairings | frozen, tracked |
| `sampling_manifest.json` | protocol pin `c51a2edca0db5903…`, pool `417a85650866b76e…` | present, **untracked** |
| `candidate_population.json` | 87 eligible / 9 exclusions (all EX1) | present, **untracked** |
| `dedup_audit.json` | 2,589 → 2,525 (64 dropped) | present, **untracked** |

> **Freeze caveat:** the v2 build artifacts and `evaluation/variants.py` are untracked in git.
> Their on-disk hashes are recorded above; a durable freeze requires committing (authorization to
> commit is not assumed by this task) or a standalone hash manifest. See `PROJECT_CLEANUP_PLAN.md`.

---

## 4. Manuscript build pipeline (fully reproducible)

| Step | Command / input | Verified output |
|---|---|---|
| Source of truth | `backend/research_paper/paper.md` (corrected draft; facts pinned to results.json) | 278 lines, 20,507 B |
| Render | `python backend/research_paper/render_research_paper.py` (Edge headless `--print-to-pdf`; `@page @bottom-center` footer; embedded fonts) | `research_paper.html` 55,002 B; `research_paper.pdf` 16 pages A4 (595×842), 640,323 B |
| Manifest | written by renderer | `render_manifest.json` (surface/method/coverage counts, 4 exact-bytes failures, 7 references, check log) |
| HTML+PDF QA | `python backend/research_paper/qa_run.py` | **55/55 PASS** (counts, citations, byte-exact failures at `<code>` level, TOC page numbers, no leaks, fonts embedded, figures placed) |
| Figure proportional bar QA | `python backend/research_paper/qa_bars.py` | **PASS** (`bar_proportionality_qa.json`) |
| Page rasters (human eyeball) | PyMuPDF → `qa_pages/page--NN.png` | refreshed in Phase 20 |
| Reference list | 7 cited keys only, from canonical 15-entry provenance `.bib` (Kaiser names, DOIs) | verified in `render_manifest.json` |

**Invariants the pipeline enforces (fail-hard):** render failure → nonzero exit; QA drift → FAIL;
manifest counts must equal `results.json` counts; bibliography rendered = cited subset only.

**Offline commands re-verified 2026-09-29:** `python -m pytest -q` → **174 passed, 8 skipped**
(offline, mock providers; live/`llm_live`/`literature_live` skipped per `pytest.ini`);
Vitest `npm run test -- --run` → **8 passed** (2 files). These match the "Latest verified status"
section of the repository `README.md`.

---

## 5. Freeze verdict

1. The manuscript's numbers trace to a single immutable artifact (`results.json`) whose recorded
   config, dataset hash, and generated timestamps are captured in §2–§3.
2. The render/manifest/QA chain is deterministic given the same `paper.md` + renderer + Edge
   (pins in §4). Rerunning `render_research_paper.py` + `qa_run.py` is the canonical verification.
3. Live multiplicative inference beyond the pilot (v2 seeds 0–4, inferential statistics, human
   ratings, preregistration) is **pending, not fabricated**, and not part of this freeze.
4. **STATE: FREEZABLE**, with two housekeeping caveats carried to the cleanup plan — untracked v2
   artifacts (commit-or-hash-pin) and the stale README status text.
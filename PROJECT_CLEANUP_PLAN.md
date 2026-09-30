# PROJECT_CLEANUP_PLAN.md

**Repository:** ResearchCollision
**Plan date:** 2026-09-29
**Prepared from:** `FINAL_PROJECT_AUDIT.md` (findings F1–F9), `CODE_QUALITY_FINAL_REPORT.md`
(findings C1–C2, H1–H8, M1–M12, L1–L10), `REPRODUCIBILITY_FINAL.md`, and the Phase 20 render state.

**Execution policy (important):** this plan states dispositions only. **No file is deleted and no
git write happens without explicit user authorization.** Items needing authorization are flagged
`[AUTH REQUIRED]`. Comments are not converted into actions automatically.

All item references below are either documented in the cited audit/report files or verified in
Phases 1–4, 20.

---

## 1. Priority overview

| Priority | Area | Items |
|---|---|---|
| P0 – Security | secrets, docker, endpoint redaction | S1, S2, S4 |
| P0 – Documentation freshness | README status table | D1 |
| P0 – Immutability state | untracked v2 artifacts | G1 |
| P1 – Build/config correctness | vite shadowing, Makefile, compose, dead arg | B1–B4 |
| P2 – Code quality backlog | code-quality findings | C1–C2, H1–H8, M*, L* |
| P2 – Housekeeping | empty dirs, scratch QA artifacts | B5, R3 |

---

## 2. Security and secrets

| ID | Finding | Action | Disposition |
|---|---|---|---|
| S1 | **F9** — private LAN endpoint `http://203.96.189.126:11434/v1` and org email appear verbatim in tracked `backend/REPRODUCIBILITY.md:20` and `backend/research_paper/UPGRADE_PLAN.md:29` | Replace with `<internal-redacted>` placeholder (or an explicit "internal only" annotation) in both files; keep the files tracked for provenance. Redact the org email the same way. | EDIT, KEEP |
| S2 | **F8 / C1** — no `.dockerignore`; backend Dockerfile `COPY . .` bakes `.env`, `.venv/`, `*.db*`, `__pycache__/`, caches into the image | Add `.dockerignore` (repo root or `backend/.dockerignore`) excluding `.env`, `.venv/`, `**/__pycache__/`, `*.db*`, eval logs/pids, `research_paper/qa_pages/*.png`. | CREATE |
| S3 | `backend/.env` gitignored (verified) | No action; keep out of any commit. Add a pre-commit note (comment in `.env.example` header: real `.env` must never be committed). | KEEP |
| S4 | Runtime leftovers (gitignored): `backend/eval_llm_run.pid`, `.eval_real_llm.pid`, `eval_llm_run_{out,err}.log`, `eval_real_llm_{stdout,stderr}.log`, `_openrouter_free_models.txt` | Delete. They are process/lint leftovers with no provenance value. `[AUTH REQUIRED]` | REMOVE |

## 3. Documentation freshness

| ID | Finding | Action | Disposition |
|---|---|---|---|
| D1 | **F1** — README says `dataset_v2.json`/`sampling_manifest.json` do not exist; v2 corpus pulls listed PENDING. Ground truth: 60-case v2 dataset IS built (600 entries, 151 unique works) with manifest + dedup audit; v2 *experiments*, inferential stats, and human evaluation remain pending. | Refresh README status table: v2 build/validation DONE; seeds 0–4 experiments, statistics, human eval PENDING. Also correct the manuscript-status line to "single-run descriptive draft, verified." | EDIT |
| D2 | Repo-root `evaluation/`, `docs/`, `sample_data/`, `data/` are empty shells (some without `.gitkeep`) | Either drop them or add `.gitkeep`. Recommendation: delete `docs/` and `sample_data/`; keep `evaluation/{datasets,metrics}` + `data/` with `.gitkeep` for planned v2/research use. `[AUTH REQUIRED]` for removals | KEEP(.gitkeep)/REMOVE |

## 4. Git and immutability

| ID | Finding | Action | Disposition |
|---|---|---|---|
| G1 | **F2** — untracked but part of the frozen dataset lineage: `backend/datasets/v2/{candidate_population.json, dataset_v2.json, sampling_manifest.json, dedup_audit.json, DATASET_CARD.md}` and `backend/evaluation/variants.py` | **(a) preferred** commit them after a secret scan (expected clean), or **(b)** record their SHA-256 hashes inside `REPRODUCIBILITY_FINAL.md` and keep them untracked. Choose one; do not declare a v2 freeze before this resolves. `[AUTH REQUIRED]` for (a) | COMMIT or PIN |
| G2 | v1 immutability (hashes match, artifacts untouched) | No action; re-verify hashes if any later edit touches `datasets/v1/` or `evaluation_out_real_llm_v1/` | KEEP |

## 5. Frontend / build / packaging

| ID | Finding | Action | Disposition |
|---|---|---|---|
| B1 | **F3** — `frontend/vite.config.js` + `.d.ts` are git-tracked `tsc` outputs that shadow `vite.config.ts` | Set `noEmit: true` in `frontend/tsconfig.node.json`; `git rm` the tracked compiled files after confirming `npm run build` regenerates nothing needed. `[AUTH REQUIRED]` | EDIT + UNTRACK |
| B2 | **F4** — Makefile `lint/format/typecheck/e2e` call npm scripts that do not exist (`lint`, `format`, `typecheck`, `test:e2e`) | Map targets to real scripts (`dev`, `build`, `preview`, `test`, `e2e`) or rename targets; verify with a dry-run (`make -n`). | EDIT |
| B3 | **F5** — `VITE_API_BASE_URL` passed by docker-compose but never read (`frontend/src/lib/api.ts` hardcodes `/api/v1`) | Either consume the variable or drop the argument from compose. | EDIT |
| B4 | **F6** — compose declares a `frontend` service with no `frontend/Dockerfile`/nginx config | Add a minimal Dockerfile (build + nginx static) or remove the frontend service from compose. | CREATE or EDIT |
| B5 | **F7** — empty `frontend/src/{api,features,hooks,layouts,types,utils}`, `frontend/tests/e2e/` | Delete empties or add `.gitkeep`. Recommendation: `git rm` the empty src shells only if unused (they are; confirm imports first). `[AUTH REQUIRED]` | REMOVE |

## 6. Code quality backlog (from CODE_QUALITY_FINAL_REPORT.md)

| ID | Summary | Action |
|---|---|---|
| C2 | Silent `MockEmbeddingProvider` fallback (`app/providers/embeddings/factory.py:15-18`) | Add an explicit log/warning when falling back to mock; document why. |
| H1 | Unregistered `app/api/v1/results.py` (dead module) | Wire it into the router or delete it. |
| H2 | `PubmedProvider` unreachable from the literature chain | Add it to the chain (datav2 uses PubMed) or remove with a note. |
| H3 | Retry path can insert duplicate rows (`tasks/discovery_pipeline.py`) | Deduplicate before insert in the retry branch. |
| H4 | `report_service.py:73-76` global-researchers select | Restrict to the workspace/current user via parameters. |
| H5 | `get_event_loop()` deprecation (`app/main.py:39-40`) | Use `asyncio.run`-scoped or `loop_factory` era patterns per Python 3.11/3.12. |
| H6 | Import-time side effect `configure_offline_defaults()` (`evaluation/baselines.py:41`) | Move the call into `main()`/`run.py` guard so importing for tests has no side effect. |
| H7 | Stored-vs-recomputed dataset hash mismatch | Document the difference or reconcile computation at write time. |
| H8 | Broad `except` at `app/agents/prompt_registry.py:34` | Narrow the exception and re-raise original context. |
| M1–M12, L1–L10 | See the report file | Work through the report's ordered remediation list; re-run `ruff`/`mypy` after each batch. |

## 7. Manuscript / reproducibility follow-ups

| ID | Item | Action | Disposition |
|---|---|---|---|
| R1 | Canonical `.tex` (both `paper.tex` and `Farid_Ahmed_*.tex`) reflect the pre-humanization manuscript; LaTeX toolchain absent on this machine; HTML renderer is authoritative | Mark the `.tex` pair as legacy in `research_paper/README.md`; do not rebuild. Archive-only; do not delete (disclosure history). | ARCHIVE (keep, annotate) |
| R2 | `qa_pages/` documented as stale at 15 vs 16 pages in audit §8 | Already resolved in Phase 20: 17 rasters match the new 17-page PDF. Verify count after any future render. | KEEP |
| R3 | Scratch QA artifacts (§8 of audit): `qa_{ascii,deep,drawings,figs,fonts,geometry,glyph_ink,reports,spot,symbols,toc,toc_layout}.py`, `_scratch_factcheck.py`, `_qraster_qa.py`, `_vlayout_audit.py`, `_pdf_extract.txt`, `_diff_iso/`, `_mupdf_pages/`, `caching_paper_deliverable_20260926/`, `figures/_orig_bars/`, `html_qa_report.md`/`pdf_qa_report.md`/`visual_qa_report.md`/`pdf_content_integrity_report.md` | Move to a single `_scratch/` archive dir or delete. Keep the canonical gates `qa_run.py` + `qa_bars.py` and the self-generated `html_qa_report.md`/`pdf_qa_report.md`. `[AUTH REQUIRED]` | ARCHIVE or REMOVE |
| R4 | Audit §8 artifacts figures (16 pp / 640,323 B PDF) superseded by Phase 20 state (17 pp / 614,298 B) | Keep audit as a historical snapshot; current state is `FINAL_RESEARCH_PAPER_AUDIT.md` + `render_manifest.json` (55/55 PASS). Optionally add a one-line addendum to the audit. | KEEP |
| R5 | Render repro gate | Documented in `REPRODUCIBILITY_FINAL.md` §re-render: `python render_research_paper.py && python qa_run.py && python qa_bars.py`. No change. | KEEP |

## 8. Verification gates after cleanup edits

1. Backend: `python -m pytest -q` (baseline 174 passed, 8 skipped).
2. Frontend: `npm run test -- --run` (baseline 8 passed).
3. Lint/type: `ruff check backend/` and `mypy backend/app/` per `CODE_QUALITY_FINAL_REPORT.md`.
4. Manuscript: after any edit touching `paper.md`, re-run `render_research_paper.py` + `qa_run.py`
   (55 checks) + `qa_bars.py`; re-verify extracted PDF word count > 3,500 and no markdown/endpoint
   leaks (scan used in Phase 20).
5. Secrets: `git grep -i '203\.96\.189\.126\|11434\|api[_-]?key'` on tracked files → expect zero
   after S1.

---

## 9. Suggested execution order

1. S1, D1 (docs edits; no authorization needed beyond normal editing) — then re-run tests (gate 1–2).
2. S2, B1, B2, B3, B4 (config/build) — then build frontend + backend image dry-run.
3. G1 (commit or pin v2) — `[AUTH REQUIRED]`.
4. S4, B5, R3 removals/archival — `[AUTH REQUIRED]`.
5. C2, H1–H8, M*, L* backlog — scheduled remediation batches with gates after each.

## 10. Residual risks after plan execution

- No repeated-run variance, inferential statistics, or human ratings exist; the manuscript scope
  (single-run, descriptive) stays as authorized and is not claimed otherwise.
- v2 experiments (seeds 0–4) remain not started; any future claims must not cite them.
- The LaTeX publication path remains unavailable (toolchain absent); the HTML renderer is the
  authoritative build and the sole documented reproduction path.
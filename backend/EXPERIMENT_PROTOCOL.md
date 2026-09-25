# Experiment protocol (evidence-discovery evaluation)

Planned (partially implemented as Phase-2 infrastructure) protocol for the
repeated, repository-level evaluation that will replace the single-run pilot as
the empirical basis of the upgraded manuscript. This is a **protocol skeleton:
execution happens only after the Phase-3 dataset and Phase-4 audit gates.** The
pilot run `evaluation_out_real_llm_v1/` is an immutable baseline and is never
overwritten or silently merged.

## 1. Objective

Estimate, with honest uncertainty, the evidence-grounding behavior of four
systems (keyword, embedding, llm_only, pipeline) across ≥N case studies, in
terms of automatic metrics plus (pending raters) blind human ratings, with a
recorded failure taxonomy and retry-policy effect.

## 2. Dataset

- Build a v2 case dataset (`evaluation/data/...v2.json`) via the Phase-3
  sampling protocol: case register (target 50), explicit inclusion/exclusion,
  corpus providers — OpenAlex **required**, arXiv **required where applicable**,
  PubMed **required where applicable**, Semantic Scholar **optional / never
  blocking**. Record availability and access dates per corpus.
- Keep `real_case_study_v1.json` untouched as pilot evidence with explicit
  provenance (UPGRADE_PLAN.md, §evidence inventory).
- Every case must satisfy the existing `EvaluationDataset` schema validation
  (gold references ⊆ source corpus, provenance labels, sha256 pin).

## 3. Systems & execution per seed

- Systems: `keyword`, `embedding`, `llm_only`, `pipeline` (definition in
  `evaluation/baselines.py`; offline defaults deterministic).
- Execution: one immutable directory per seed under `experiments/v2/seed<N>/`
  via `python -m evaluation.batch --seeds 0 1 2 3 4 --resume`.
- Config snapshot (seed, model, prompt versions, corpus metadata, retry
  policy, provider identities) is persisted inside each seed directory — never
  inferred later.
- No overwrites: re-running uses a new seed index. `--resume` only skips
  completed seeds.

## 4. Seed semantics

See REPRODUCIBILITY.md §2. Seeds control blind-id randomization and (where the
endpoint honors it) sampling; they do not create artificial determinism for a
non-deterministic remote model. Report seed-scatter honestly.

## 5. Retry & failure handling

- Policy fixed at run time, recorded in `config.json` (attempts=3; retryable
  {429,500,502,503,504}; exponential backoff; fail fast on client errors).
- Every timeout/retry/final failure is logged and stored in `failures.json`.
- Failures are **never converted into successes**; analysis distinguishes
  analysis-level failures (taxonomy in `evaluation/failures.py`) from
  system/runtime failures (e.g. the pilot's 4 `system_error` pipeline errors)
  and separates seeded stochastic variation from persistent failure.

## 6. Statistical analysis (Phase 6; scipy only, no heavy new deps)

Planned procedures (final methods gated on data shape and assumption checks):
- Summaries per system: mean, SD, bootstrap 95% CI (**no** invented precision).
- Comparisons across systems per metric: Friedman test + post-hoc Wilcoxon
  signed-rank with multiple-comparison correction; report effect sizes.
- Failure rates with exact binomial confidence intervals.
- Retry-policy sensitivity: compare failure counts under the recorded policy.
- All assumptions verified before inference; non-parametric defaults.

## 7. Human evaluation (Phase 7–8)

- Blind templates exported per seed (`human_ratings_template.csv`), merged via
  `blind_key.json`; 4 dimensions (relevance, novelty, plausibility, evidence
  quality), 1–5 rubrics.
- **Requires real independent raters; STOP gate before executing.** No
  fabricated or LLM-substitute ratings.

## 8. Reporting responsibilities

Each phase ends with a report (completed / remains / evidence / blocked /
files changed). Final paper claims are written only from verified artifacts.

## 9. Preregistration

See `research_paper/PREREGISTRATION_DRAFT.md` — labeled **“Preregistration
planned”**; it will be registered externally before confirmatory analysis. It
is not a fake DOI.
# UPGRADE_PLAN.md — From Single-Run Descriptive Report to Reproducible Research Paper

**Status:** Phase 1 (audit) COMPLETE. This document is the pre-edit plan required by the
research-upgrade workflow. **No manuscript has been rewritten yet; no authoritative artifact
has been modified.** All statements below were verified read-only against the repository
in this session (2026-09-25).

Project goal restated: transform the current single-run descriptive technical report into a
reproducible, statistically defensible, peer-reviewable research paper — without fabricating
experiments, data, statistics, citations, or DOIs, and without silently rewriting the science
ahead of verification.

---

## 0. Audit basis (verified in this session, read-only)

| Item | Verified value |
|---|---|
| Python | 3.10.0 (system) and `.venv` (3.10.0) |
| Backend tests | **122 passed, 8 skipped** (offline, `python -m pytest -q` in `backend/`) |
| Authoritative results | `backend/evaluation_out_real_llm_v1/results.json`, `generated_utc=2026-09-23T11:43:34+00:00` |
| Dataset | `evaluation/data/real_case_study_v1.json` — 12 cases, provenance `curated`, `source_providers=[openalex]`, built `2026-09-21T16:08:04+00:00`, `content_sha256=09d84b77...` |
| Case count | 12 (federated_learning_x_privacy, causal_inference_x_clinical_ml, gnn_x_protein_structure, rl_x_sim_to_real, clinical_nlp_x_ehr, climate_downscaling_x_deep_learning, quantum_chemistry_x_dft, recommender_x_fairness, single_cell_x_transfer_learning, materials_discovery_x_active_learning, knowledge_graph_x_question_answering, speech_recognition_x_hearing_aids) |
| Systems | keyword, embedding, llm_only, pipeline (all in `evaluation/baselines.py`) |
| Evidence records (tallied from `blind_key.json`/`human_ratings_template.csv`, 188 rows) | surfaces gap=83, hypothesis=50, intersection=55; systems keyword=41, embedding=36, llm_only=53, pipeline=58 → **188** |
| Pipeline failures | 4 of 12 (`failures` array): causal_inference_x_clinical_ml/GNN/RL were ReadTimeout/ReadError/ConnectError varying; 4 files verbatim |
| Failure analysis (analysis-level) | `failure_summary`: total=61; by_stage reasoning=19/retrieval=38/generation=4; by_type ungrounded_hypothesis=18, gap_without_evidence=15, intersection_without_evidence=23, system_error=4, no_expected_topic_covered=1; by_system llm_only=53, pipeline=7, embedding=1 |
| Human ratings | `provided=false`, `ratings_count=0` — **none collected** |
| Real-run LLM config | `LLM_PROVIDER=openai_compatible`, `OPENAI_BASE_URL=http://203.96.189.126:11434/v1`, `LLM_MODEL=qwen2.5:7b` (remote Ollama; **reachable**, HTTP 200 on `/api/tags`), `LLM_TIMEOUT_SECONDS=900`, `STRUCTURED_MAX_TOKENS=4096` |
| Literature chain | `[openalex, semantic_scholar, crossref, arxiv]` (openalex primary; network probe HTTP 200) |
| Embedding provider | `mock` in the authoritative run (`MockEmbeddingProvider`) |
| Stats libs | scipy 1.15.3, numpy 1.26.4 present in system Python; **not listed in `requirements.txt`** |
| TeX | absent (honest disclosure already in AUDIT.md); manuscript PDFs are headless-Edge HTML renderings |
| Venv | `backend/.venv` present |
| Manuscript | single-run descriptive `.md`, canonical files under `research_paper/`, verified vs `results.json` |

---

## 1. Current evidence inventory

**Data artifacts (imutable, present):**
- `evaluation/data/real_case_specs_v1.json` — 12 hand-authored case designs (domain pairs + queries).
- `evaluation/data/real_case_study_v1.json` — built dataset (real OpenAlex papers, per-case personas).
- `evaluation/data/demo_discovery.json` — synthetic fixture (not real evidence).
- `evaluation_out_real_v1/` — earlier offline/mock run (keyword/embedding/llm_only/pipeline, mock providers).
- `evaluation_out_real_llm_v1/` — **authoritative** run: `results.json`, `results.csv`, `report.md`,
  `blind_key.json`, `human_ratings_template.csv` (188 rows), `failure_analysis.json`.
  **Note:** `SOURCE_INVENTORY.md` claims a `pipeline_failures.json` exists here — it does **not**;
  the 4 failures live in the `failures` array of `results.json`. Stale documentation to correct.

**Code (executable, offline):**
- `evaluation/run.py` (CLI), `runner.py` (orchestrator), `baselines.py` (4 systems),
  `metrics.py` (automatic + human rubric), `failures.py`, `human.py`, `report.py`,
  `schemas.py`, `build_real_dataset.py`, `environment.py`.
- `app/providers/llm/{openai_compatible,openrouter,mock}.py`, literature providers (openalex,
  semantic_scholar, crossref, arxiv, mock), embeddings (mock, sentence_transformer).
- `app/agents/prompts/*.txt` — 8+ versioned prompt files actually used.
- `app/workers/tasks/discovery_pipeline.py` — the real end-to-end pipeline.

**Current reproducibility barriers (must be fixed):**
1. Raw system outputs (gaps/intersections/hypotheses/refs) are **not persisted per run**;
   `results.json` stores only metrics + blind_key text. A re-run cannot reconstruct the exact
   output that produced a score.
2. `--seed` only randomizes blind eval_ids. **LLM generation is not seeded** (temperature fixed
   at 0.2 in `llm_only`; pipeline agents use their own defaults). Repeated runs are not
   reproducible.
3. No per-record metadata: seed, model/version, prompt version, corpus snapshot date, runtime,
   cost are missing from `results.json`.
4. Stockholm not multi-corpus: dataset is OpenAlex-only although `semantic_scholar`/`arxiv`
   clients exist. The plan requires at least one additional corpus (or a documented reason).
5. Case coverage is only 12 cases; plan target is ≥50 with a documented sampling procedure
   and the original 12 kept identifiable as the pilot subset.

---

## 2. Missing experiments

| # | Missing | Required | Blockers |
|---|---|---|---|
| E1 | Repeated runs (seeds) | ≥5 independent seeds (0–4), prefer 10 if API failure variability matters; each stored separately `experiments/v2/seedN/results_seedN.json` | Needs seed plumbing in LLM provider + per-run persistence + batch runner. LLM non-determinism is expected (temperature sampling); `seed` accepted by Ollama `/api/chat`. |
| E2 | Expanded case dataset (≥50) | Documented sampling procedure; 50–100 initially; original 12 remain pilot subset | Needs a sampling protocol + new specs; OpenAlex is reachable so rebuild is feasible. Corpus version must be recorded (snapshot date differs from pilot). |
| E3 | Multi-corpus evaluation | Add ≥1 corpus (candidates: Semantic Scholar, PubMed, arXiv); cross-corpus consistency | Semantic Scholar requires an optional API key; PubMed/E-utilities is keyless; arXiv has no key. Scopus is licensed — document unavailability rather than fabricate. |
| E4 | Human evaluation | ≥3 independent raters × (relevance, novelty, plausibility, evidence quality [correctness/actionability rubric coverage to be specified]) | **Human subjects required** → STOP (see §8). Infrastructure (blind template + blinded merge + inter-rater reliability) already exists. |
| E5 | Statistical comparison | Friedman + post-hoc Wilcoxon signed-rank + effect sizes (rank-biserial r, Cliff's δ) + Holm-Bonferroni/BH correction; on matched case sets only | Needs scipy added to requirements; needs per-seed per-case counts (E1). |
| E6 | Fault-tolerance ablation (optional contribution) | retry policy for pipeline failures, measured effect on coverage/failure rate | Design decision; requires reruns with/without retry (E1 code path). |
| E7 | Runtime / cost instrumentation | per-record runtime; API usage where available | Runner must wrap system.run timing; LLM usage dict already returned but not persisted. |
| E8 | Qualitative examples | representative success + failure examples with full provenance (case, system, seed, surface, source, outcome) | Requires persisted raw outputs (E1). |

---

## 3. Missing data

- Raw normalized outputs per (case, system, seed).
- Seed + timestamp + model/version + prompt-version + corpus/index-version per run (and ideally per record).
- Runtime per run and per system; API usage/cost where available.
- Failure detail: stage, error type, exact message, retry behavior, final outcome (currently only a
  coarse `failures` array + analysis-level taxonomy; exact message text is truncated at collection).
- Human ratings and rater metadata (requires raters).
- Cross-corpus retrieval snapshots and corpus retrieval dates.
- Versioned prompt archive (`prompts/` mirroring `app/agents/prompts/*.txt`).

---

## 4. Required code changes

| Component | Change |
|---|---|
| `app/providers/llm/openai_compatible.py` | Accept `seed` param (Ollama/OpenAI-compatible), propagate into payload; expose in `LLMResponse`. |
| `app/providers/llm/base.py` | Optional `seed` in protocol method signatures (non-breaking defaults). |
| `evaluation/runner.py` | Persist normalized SystemOutput per case/seed (JSONL or nested JSON); record seed, generated_utc, provider config, prompt versions, runtime, usage; separate per-`experiments/v2/<seed>/` output dirs. |
| `evaluation/run.py` | Add `--seed` propagation to LLMs (not only blind ids), `--runs`, `--experiments-root`; never overwrite an existing run dir. |
| new `evaluation/batch_runner.py` | Orchestrate seeds 0..n sequentially (avoid parallel LLM thundering); write one dir per seed; registration of attempts/retries; immutability check. |
| new `evaluation/stats.py` | mean/sd/95% CI (Gaussian + bootstrap), Friedman, Wilcoxon signed-rank, Holm-Bonferroni/BH, Cliff's δ, rank-biserial r; input = per-case matched counts; requires scipy. |
| `evaluation/failures.py` | Capture exact error string + retry behavior + stage + final outcome per record (keep existing schema, extend). |
| `evaluation/human.py` + `report.py` | Keep blind merge; add explicit 4-dimension rubric mapping incl. correctness/actionability if raters' rubric is extended; emit raw ratings CSV untouched. |
| `evaluation/build_real_dataset.py` | Generalize provider to support OpenAlex/S2/arXiv/PubMed; record per-corpus retrieval dates; add sampling protocol metadata (case register). |
| `evaluation/schemas.py` | Add optional `sampling` block per case (sampling method, inclusion/exclusion, rationale) without breaking v1. |
| `requirements.txt` | Add `scipy` (stats). |
| `prompts/` | Mirror the exact `app/agents/prompts/*.txt` files verbatim (versioned archive outside the app tree). |
| manuscript pipeline | Rebuild `.md` → `.html` → PDF via existing headless-Edge tooling; re-verify with poppler. |

---

## 5. Required statistical analyses

Applied only where mathematically appropriate and assumption-suited (never just "because requested"):

1. Descriptive: per metric, per system, per case: mean, SD, 95% CI (and bootstrap CI where the
   distribution is non-normal/small-n).
2. Matched-case comparisons on the **same case set** (complete-case analysis over the cases where
   all compared systems produced evidence). Denominators explicit (e.g., `n=8` shared cases across
   all 4 systems; `n=12` for keyword/embedding/llm_only).
3. Friedman test (4 systems × K matched cases) on per-case counts/per-case metric values; if
   significant, pairwise Wilcoxon signed-rank tests with Holm-Bonferroni (or BH) correction.
4. Effect sizes: matched-pairs rank-biserial r / Cliff's δ (no invented p-values).
5. Failure-inclusive (intention-to-treat-style) secondary analysis: failure rate + failure-type
   distribution; state the denominator (e.g., pipeline 4/12 failed in pilot).
6. Inter-rater reliability: mean pairwise quadratic-weighted Cohen's κ + exact agreement, only with
   ≥2 real raters.

Statistical plan is preregistered in `PREREGISTRATION_DRAFT.md` before confirmatory data collection
(Phase 3–5) — actual registration (OSF/other) requires external service → STOP.

---

## 6. Required human evaluation

- Infrastructure exists (blind template, eval_ids, merge, κ). Needs:
  - ≥3 independent expert raters, independent of system implementation.
  - Pre-specified 1–5 rubric (existing: relevance, novelty, plausibility, evidence quality; align
    with requested correctness/actionability).
  - Raw ratings stored separately (`human_eval_raw.csv`); no post-hoc editing except documented
    correction procedure.
  - Disagreement inspected and reported; low agreement documented, not discarded.
- **Raters are human subjects → STOP and ask before recruiting/running Phase 8.**

---

## 7. Reproducibility requirements

New/updated docs (plan to create/extend in Phase 2 and refresh in Phase 11–12):
- `README.md` (update to describe the v2 experiment layout + how to reproduce),
- `REPRODUCIBILITY.md` (env, Python 3.10, package versions incl. scipy, model versions, Ollama
  endpoint + snapshot, GPU/CPU, memory, corpus versions, API snapshot dates, runtimes, costs,
  exact commands),
- `EXPERIMENT_PROTOCOL.md` (prompt set frozen verbatim in `prompts/`, config, seeds, per-run
  layout, failure/retry policy, stope rules),
- `PREREGISTRATION_DRAFT.md` (hypotheses, primary/secondary outcomes, sampling plan, exclusion
  rules, statistical plan, stopping rules, human-eval protocol; labeled "Preregistration planned"
  — never faked DOIs).

Layout: `experiments/v2/seed0/ … seedN/` with raw + normalized results, logs, metadata; derived
tables regenerable; **raw evidence immutable**.

---

## 8. Risks and blockers (STOP conditions)

| # | Risk | Action |
|---|---|---|
| S1 | Human raters required (Phase 8) | **STOP — ask.** No fabrication of ratings ever. |
| S2 | External paid/registered pre-registration (OSF/AsPredicted) | **STOP — ask**; label "Preregistration planned" otherwise. |
| S3 | Semantic Scholar API key (optional) | Keyless fallbacks first (OpenAlex + arXiv + PubMed). **STOP** if licensing/paid required. |
| S4 | Remote Ollama hosts model `qwen2.5:7b`; availability/flakiness caused the 4 pilot failures | Run sequentially with retry policy; measure failure rate; treat failures as outcomes. If endpoint becomes paid/keys → STOP. |
| S5 | Corpus/license for a corpus (e.g., Scopus) | Document unavailable; never fabricate cross-corpus numbers. |
| S6 | OpenAlex snapshot drift (v2 dataset rebuilt at a later date) | Record corpus version + retrieval date; pilot (v1) dataset retained unchanged as `pilot` subset. |
| S7 | `search_limit`/citation-count heuristics in `build_real_dataset` produce < min papers | Builder already fails loudly; keep behavior; record case register exclusions. |
| S8 | Statistical analysis statistically inappropriate | Replace with appropriate alternative + explanation (see §5). |
| S9 | Time/cost of 50 cases × ≥5 seeds × 4 systems including pipeline LLM load | Estimate in Phase 5 before full run; may stage dataset (e.g., Phase-3 50 cases, larger later). |
| S10 | Pipeline uses `LITERATURE_ALLOW_MOCK_FALLBACK=false`; mock fallback must stay off for real runs | Enforce config check in batch runner. |

---

## 9. Proposed paper structure (post-run; based ONLY on verified results)

1. Abstract
2. Background / Objective
3. Introduction
4. Related Work (LBD: Swanson/Smalheiser/Bruza/Gordon; dense retrieval: DPR/ColBERT/Contriever;
   RAG: Lewis/Izacard/Borgeaud; IR eval: Voorhees/Buckley/Sakai; reproducibility: Pineau/Dodge;
   recent 2024–2026 work) — every citation verified
5. Research Questions
6. Methodology
   - Dataset and Case Sampling (v1 pilot subset + v2 register)
   - Systems (keyword, embedding, llm_only, pipeline)
   - Experimental Protocol (seeds, prompts, corpora)
   - Human Evaluation
   - Statistical Analysis
7. Results (central estimate + uncertainty + n + denominator; complete-case and failure-inclusive
   analyses kept separate; record count vs unique evidence vs surface distribution vs coverage vs
   failure rate vs human scores never conflated)
8. Failure Analysis (taxonomy + verbatim exact errors + retry policy effects)
9. Discussion
10. Threats to Validity
11. Reproducibility and Open Science
12. Conclusion
13. References
14. Appendices (method/config; failures verbatim; evidence matrix with provenance; reproducibility)

Contribution frame: **Evidence Discovery Benchmark and Failure Analysis Framework** — formal
evidence-surface taxonomy, operational definitions, reproducible protocol, multi-case dataset,
failure taxonomy, human-eval protocol, statistical protocol. Optional: fault-tolerance mechanism.

---

## 10. Phase-by-phase plan (workflow order, no overwrites)

- **Phase 1 (this doc).** Audit + plan. DONE.
- **Phase 2.** Experiment infrastructure: seed plumbing, runner persistence, batch runner,
  runtime/usage capture, failure recording, `requirements.txt` (+scipy), `prompts/` archive,
  REPRODUCIBILITY.md / EXPERIMENT_PROTOCOL.md skeletons. **IMPLEMENTED (2A–2G; tests 2H) — see §13.**
- **Phase 3.** Case-sampling pipeline: sampling protocol, case register (≥N, target 50), corpus
  provider options, build v2 dataset (keep v1 untouched, mark pilot). Record retrieval dates.
- **Phase 4.** Repeated-run execution infra (seed 0..N, immutability, retry policy).
- **Phase 5.** Run experiments → `experiments/v2/seedN/`; immutable raw artifacts + logs.
- **Phase 6.** Statistical analysis (`evaluation/stats.py`); verify assumptions.
- **Phase 7.** Human-eval infra (rubric, raw-ratings storage, correction procedure).
- **Phase 8.** Human evaluation — **requires raters (STOP before starting).**
- **Phase 9.** Failure analysis incl. retry-policy effect.
- **Phase 10.** Independent verification (cross-checks vs raw artifacts). 
- **Phase 11.** Rewrite manuscript from verified results only.
- **Phase 12.** Final audit (`FINAL_AUDIT.md`) + regenerate `.md`/`.html`/PDF (headless Edge,
  poppler-verified) — no stale artifacts.

Every phase ends with a report: completed / remains / evidence / blocked / files changed.

---

## 11. Immediate next step (pending approval)

Proceed to **Phase 2** (no destructive changes): add LLM seed plumbing, runner per-seed
persistence + metadata, batch runner, scipy, prompts archive, reproducibility docs. Runs are NOT
executed until Phase 5 after the Phase-3 dataset and Phase-4 audit gates.

---

## 12. Phase 2A audit — stochasticity & seed semantics (DONE)

Seed plumbing implemented across providers, agents, pipeline, baselines, runner, CLI, and tests
(`tests/test_seed_plumbing.py`, 10 tests). Audit of every stochastic component in the evaluation path:

**Seed-controlled (reproducible given endpoint cooperation):**
- Blind eval-id assignment: `evaluation/human.py::make_blind_key` uses `random.Random(seed)`.
- LLM sampling: `--seed` is plumbed `run.py → run_evaluation → _run_one → get_system(name, seed) →
  BaseSystem.run/DiscoveryPipeline(seed) → BaseAgent(seed) → structured_generate(seed) →
  OpenAICompatibleProvider._chat`, where `seed` is added to the `/chat/completions` payload ONLY when
  not `None`. Ollama honors `seed`; other OpenAI-compatible endpoints may ignore it.

**Deterministic / seed is a NO-OP (no randomness to control):**
- Retrieval baselines (keyword token overlap, mock-embedding cosine) are pure functions of inputs.
- MockLLMProvider, MockEmbeddingProvider, mock literature chain: hashing/sorting-based, no RNG.
- Metrics, aggregation, failure analysis, CSV/JSON export: deterministic.
- No `python random`, `numpy.random`, `random.choice/sample/shuffle`, or `secrets` in the eval path
  (verified by grep; the only `random` is the seeded blind-key RNG above).

**NOT seed-controllable (documented, never misrepresented as reproducibility):**
- Remote model nondeterminism: if the endpoint ignores `seed` or samples non-deterministically
  (e.g., batched decode), identical `seed` does not guarantee identical model output.
- Network/retry timing and transient failures (timeout, 429/5xx) — handled by the configurable
  tenacity retry policy and logged as failures, never converted into successes.
- Verification tests enforce: same seed + same config → identical cases/aggregates/blind_key;
  different seeds → distinguishable blind_key while deterministic mock metrics stay identical.

## 13. Phase 2 implementation record (2A–2H)

All Phase 2 infrastructure is implemented and tested (offline; no expensive runs executed).

- **2A Seed plumbing — DONE.** `seed: int | None` on `LLMProvider`/`structured_generate`;
  `OpenAICompatibleProvider` sends `seed` in payload only when not `None`; `BaseAgent`, pipeline,
  `BaseSystem`/`_SYSTEM_CLASSES`, `get_system(name, seed)`, runner, `run.py --seed`, config metadata
  (`results.json.config.seed`). §12 audit.
- **2B Per-seed immutable persistence — DONE.** `evaluation/experiment.py`:
  `experiments/v2/seedN/` with run_manifest, redacted `config.json`, `prompt_versions.json`,
  `corpus_meta.json`, `status.json` (per-case `duration_ms` + totals), `outputs_per_case.json`,
  `report.md`, `blind_key.json`, `human_ratings_template.csv`, `failures.json`,
  `failure_analysis.json`; `ExperimentError` on non-empty seed dir (never overwrite).
- **2C Batch runner — DONE.** `evaluation/batch.py`: sequential seeds, `--resume` skip via
  `is_completed`; statuses completed/skipped_completed/already_exists_no_resume/
  partial_dir_blocked/error; batch manifest under `root/_batch_manifests/`.
  `run_evaluation` gained `case_ids` subset selection (ValueError on unknown ids).
- **2D scipy — DONE.** `scipy>=1.11` added to `requirements.txt`; installed in `.venv`
  (1.15.3). Full suite green after install.
- **2E Prompt archive — DONE.** `evaluation/prompt_archive.py` (idempotent noop / error on
  different content) + `evaluation/prompt_registry.py` (shared agent→version map);
  `experiments/prompts/v1/` snapshot (10 files + MANIFEST.json sha256 + README.md).
  `experiment.py` prompt-version collection now uses the registry.
- **2F Reproducibility docs — DONE.** `REPRODUCIBILITY.md` (deterministic vs
  not-seed-controllable), `EXPERIMENT_PROTOCOL.md`, `PREREGISTRATION_DRAFT.md` (labeled
  "planned"), `evaluation/README.md` Phase-2 section.
- **2G Documentation corrections — DONE.** `SOURCE_INVENTORY.md` §1/§7/§9 + `REAL_METHODOLOGY.md`
  §6: authoritative 12-case id list; removed phantom `pipeline_failures.json` (failures live in
  `results.json.failures`); separated analysis-level failures (61) from system/runtime failures (4).
- **2H Tests — DONE.** `tests/test_prompt_archive.py` (3). Full offline suite:
  **142 passed, 8 skipped**. CLI smoke (`run.py --seed`) records seed; batch resume verified.
  Ruff: repo has no config and a non-clean baseline; new code matches existing defensive style
  (one trivia in a test fixed).

**Phase 2 deliverable**: no manuscript claims changed; authoritative artifacts untouched.
Next up: Phase 3 (case-sampling protocol + v2 dataset build) per §10.
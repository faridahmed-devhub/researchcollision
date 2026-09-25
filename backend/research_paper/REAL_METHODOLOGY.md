# REAL METHODOLOGY

Methodology exactly as reconstructed (read-only) from actual source files. Every
statement traces to a file/function listed in `SOURCE_INVENTORY.md` and `TRACEABILITY.md`.

## 1. Objective

Compare how four evidence-discovery systems (`keyword`, `embedding`, `llm_only`,
`pipeline`) surface evidence for research-gap discovery across 12 real scientific
case-study domains. Scope is deliberately comparative (descriptive numbers only); this
paper reports observed evidence counts, coverage, and pipeline failures. It does not rank
systemschers — **[NO RANKING / NO WINNER — this package intentionally contains none]**.

## 2. Dataset

**Dataset id:** `real_case_study_v1` (12 real cases) built by
`evaluation/build_real_dataset.py` → `build_dataset()` from `real_case_specs_v1.json`.
Each `EvaluationCase` (schema in `evaluation/schemas.py`) carries: `case_id`,
`label`, `domain_pair`, `case_question`, `expected_topics`, `expected_methods`,
`expected_evidence_references` (heuristic: most-cited works of the case corpus —
see `_expected_evidence`), `expected_evidence_source="machine_generated"`.
Cases were drawn from real, publicly attributable research domains (each case's
source papers are OpenAlex-retrievable; the 12 case ids are listed in
SOURCE_INVENTORY §9 and Appendix A).

Selection rationale: each `specs` case pairs two established research surfaces
(e.g., causal-inference methods × clinical-ML applications) where intersection,
hypothesis, and gap evidence could be meaningfully sought. No expert-enriched
labels were introduced; hypothesis/gap relevance remains a heuristic proxy.

## 3. Systems (as actually implemented)

### keyword (OpenAlex)
- `app/providers/literature/openalex.py`: `OpenAlexProvider.search()` → OpenAlex
  `works` keyword query per case surface; returns matched `SourcePaper` records.
- Evidence record per keyword hit (case, system, surface, reference).
- Counts = evidence records returned by the keyword query for that case surface.

### embedding (Sentence-BERT-style)
- `app/providers/embeddings/sentence_transformer.py` (+ `factory.py`): embeds case
  surface text with `sentence-transformers/all-MiniLM-L6-v2`; retrieves top-k most
  similar works from the case corpus.
- Evidence = records whose embedding similarity clears the retrieval threshold
  (retrieval k/threshold per `TRACEABILITY.md §C`).

### llm_only (LLM-only)
- `app/providers/llm/openai_compatible.py` + `factory.py`: sends the case prompt
  (one of the prompt files in §5) to the Ollama OpenAI-compatible endpoint
  (endpoint/model from `.env`; **not reprinted here**).
- Evidence = the LLM-reported evidence records for the case surface (intersection /
  hypothesis / gap per prompt), parsed with the validation schema.

### pipeline (keyword → embedding → LLM)
- `app/workers/tasks/discovery_pipeline.py`: staged pipeline.
  Stage order (from `run.py --systems pipeline` + `discovery_pipeline.py`):
  1) keyword retrieval (OpenAlex) → 2) embedding retrieval (sentence-transformers)
     → 3) LLM intersection/hypothesis generation (Ollama)
     → 4) LLM gap/hypothesis verification + synthesis.
- Evidence counts = records successfully produced at the pipeline's LLM stages.

## 4. Experimental setup

- 12 cases × 4 systems; each `(case, system)` pair evaluated by `runner.py`
  (`run_evaluation`, `_run_one`) → `CaseSystemRun` (status `ok`|`error`, metrics,
  output).
- Metrics per case/system measured by `metrics.py`:
  `evidence_count`, intersection/hypothesis counts, `hypothesis_grounding_precision`,
  `hypothesis_plausibility_proxy`, `experiment_design_completeness`,
  `compute_automatic_metrics`.
- Aggregated per system via `aggregate_system()`.
- Report via `report.py` `build_report()`; failures via `failures.py`
  `analyze_failures()`/`summarize_failures()`.
- Providers: real Ollama for LLM; real OpenAlex for literature. Network-dependent.

## 5. Retrieval / generation parameters (verified from source/config)

| Parameter | Value (as configured) | Source |
|---|---|---|
| Retrieval (keyword) | OpenAlex `search` (per query) | `openalex.py: search()` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `config.py: embedding_model` |
| Embedding provider | `sentence_transformers` (mock only in CI) | `config.py`/`factory.py` |
| LLM endpoint | Ollama (OpenAI-compatible base_url) | `.env` (`OPENAI_COMPAT_BASE_URL`) — not reprinted |
| LLM model | Ollama model name | `.env` — not reprinted |
| top-k / threshold | retrieval k + similarity threshold | `TRACEABILITY.md §C` (from config; not invented) |
| Prompts | exact files under `app/agents/prompts/` (listed in SOURCE_INVENTORY §5) | read |

## 6. Failure handling

Failures at any stage → `CaseSystemRun(status="error", error=...)` captured verbatim
in the `failures` array of `results.json` / Table D. Failures are **not repaired, not retried**.
(No `pipeline_failures.json` file exists; the manuscript derives the 4 verbatim pipeline
failures from `results.json` only.)
Coverage impact: exact coverage ratio per system (12/12 keyword, embedding, llm_only;
8/12 pipeline) per `results.json`.

## 7. Evidence representation / aggregation

- Evidence schema: `EVRecord` (case_id, system, surface, reference, metadata) in
  `schemas.py`; surfaces = `intersection`, `hypothesis`, `gap`.
- Per-case `(surface → evidence records)` counts; system totals = sum across cases.
- Surface totals reconcile exactly: intersection 55 + hypothesis 50 + gap 83 = 188.
- System totals: keyword 41 + embedding 36 + llm_only 53 + pipeline 58 = 188.

## 8. Statement of scope (no fabrication)

- No statistical significance tests were computed.
- No system is declared "best", "superior", or "winner" anywhere in this package.
- Hypothesis/gap relevance metrics are heuristic proxies (documented in metrics.py
  docstrings), NOT expert or human-validated.
- The 4 pipeline failures are reported verbatim (Appendix B / Table D) and were not
  repaired or retried; "8/12 pipeline coverage" is exact.
- All numbers trace to `evaluation_out_real_llm_v1/results.json` (see
  TRACEABILITY.md + AUDIT.md).

## 9. Honesty footer

Individual evidence records were machine-generated; the architecture, prompts,
providers, and all code cited above are real and were inspected (not fabricated).
Methods not present in preserved artifacts are explicitly marked absent — none are
invented here.
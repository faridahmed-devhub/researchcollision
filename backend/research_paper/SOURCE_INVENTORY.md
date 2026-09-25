# SOURCE INVENTORY

Real, read-only forensic map of the preserved experiment. Every entry below was
confirmed present on disk; file sizes/line ranges are as read. Nothing was rerun,
repaired, or modified. Paths are relative to `backend/`.

## 1. Dataset (real-case study)

| Path | Purpose |
|---|---|
| `evaluation/data/real_case_specs_v1.json` | 12 real case-study case ids + pairing spec (authoritative read anchor) |
| `evaluation/data/real_case_study_v1.json` | built v1 dataset (12 real cases, OpenAlex records only) as consumed by the run |
| `evaluation/build_real_dataset.py` | `build_dataset()` assemble 12 real cases from provider hits |

Dataset label used by the run: `real_case_study_v1`.
The `case_id` list is authoritative in BOTH `real_case_study_v1.json` AND
`results.json` AND `tables/table_a_casexsystem.csv` (see §9); older inventory
drafts that listed other ids (e.g. `gnn_x_bioinformatics`,
`causal_inference_x_population_health`) were stale and are superseded.

## 2. Evaluation CLI / pipeline

| Path | Purpose | Relevant functions |
|---|---|---|
| `evaluation/run.py` | CLI entry: `python -m evaluation.run --dataset ... --systems ... --out-dir ...` | `main`, `run` |
| `evaluation/runner.py` | async orchestration of the 4 systems over each real case | `run_evaluation`, `_run_one`, `aggregate_system` |
| `evaluation/build_real_dataset.py` | builds `EvaluationCase` objects | `build_case`, `build_dataset`, `load_specs`, `_expected_evidence` |
| `evaluation/metrics.py` | automatic metrics per case/system | `evidence_count`, `intersection_evidence_count`, `hypothesis_grounding_precision`, `hypothesis_plausibility_proxy`, `experiment_design_completeness`, `compute_automatic_metrics`, `aggregate_system` |
| `evaluation/report.py` | Markdown report generator | `build_report` (+ limitations list) |
| `evaluation/failures.py` | pipeline failure capture/analysis | `analyze_failures`, `summarize_failures`, `_analyze_output` |
| `evaluation/__init__.py`, `evaluation/environment.py`, `evaluation/schemas.py` | dataset/environment/schema types | `EvaluationDataset`, `EvaluationCase`, `EVRecord` (schemas.py) |

## 3. The four systems (actual implementation)

| System key | Core provider file(s) | How it produced evidence |
|---|---|---|
| `keyword` | `app/providers/literature/openalex.py` + `factory.py` (`get_literature_provider("openalex")`) | OpenAlex `search` word query per case surface; evidence = matching work records |
| `embedding` | `app/providers/embeddings/sentence_transformer.py` (+ `factory.py`) | Sentence-BERT-style embedding retrieval; evidence = most-similar work records |
| `llm_only` | `app/providers/llm/openai_compatible.py` + `factory.py` (Ollama endpoint) | LLM-only generation of evidence/hypotheses from case prompt |
| `pipeline` | `app/workers/tasks/discovery_pipeline.py` (+ `app/agents/*`) | keyword → embedding → LLM pipeline |

Actual system names in the run config: `keyword`, `embedding`, `llm_only`, `pipeline`
(`DEFAULT_SYSTEMS` in `evaluation/baselines.py` / runner config).

## 4. Providers

Literature: `app/providers/literature/{openalex,arxiv,crossref,semantic_scholar,mock}.py`.
OpenAlex used for the real run (`BASE_URL=https://api.openalex.org`), configured with a
polite-mailto param (`openalex_email` config; **no credential exposed here**).

LLM: `app/providers/llm/{openai_compatible,openrouter,mock}.py` + `factory.py`.
Real run used an OpenAI-compatible Ollama instance (`base_url` points at Ollama; the local
model and endpoint are in config/`.env`, **not printed here** — never expose secrets).

Embeddings: `app/providers/embeddings/{sentence_transformer,mock}.py` + `factory.py`;
config default embedding model: `sentence-transformers/all-MiniLM-L6-v2`
(provider `sentence_transformers`); `mock` possible for CI-only runs.

## 5. Prompts (exact files, as read)

`app/agents/prompts/` — actual prompt text files (byte sizes as read):
- `intersection_discovery.txt` (1260 B) — pipeline intersection/hypothesis evidence step
- `gap_detection.txt` (764 B) — pipeline gap-evidence step
- `hypothesis_generation.txt` (583 B) — pipeline hypothesis step
- `evidence_extraction.txt` (0 B, placeholder) — NOT used by the real run (verification steps used `verification.txt`)
- `verification.txt` (783 B) — pipeline verification step
- `collaboration_ranking.txt` (672 B) — post-hoc, not part of evidence generation
- `experiment_design.txt` (506 B) — hypothesis → gap methodological evidence (pipeline)
- `paper_analysis.txt` (576 B); `paper_writing.txt` (2088 B); `profile_extraction.txt` (720 B);
  `trajectory_analysis.txt` (749 B) — auxiliary agents, not evidence-count sources.

## 6. Evidence schema / records

- `evaluation/schemas.py`: `EVRecord`, `EvidenceSurface`, `SystemOutput`,
  `CaseSystemRun`, `EvaluationCase`, `EvaluationDataset`.
- Evidence surfaces in results: `intersection` (hypothesis x discovery intersection),
  `hypothesis`, `gap`.
- Selector surface group in the LLM-only/pipeline outputs: intersection `55`, hypothesis `50`,
  gap `83` (per-case grouping; see REAL_METHODOLOGY §7).

## 7. Real run outputs (authoritative; read-only)

| Path | Role |
|---|---|
| `evaluation_out_real_llm_v1/results.json` | **authoritative 188-EV results** (55+50+83=188; systems 41/36/53/58; coverage 12/12/12/8; 4 system/runtime failures in the `failures` array) |
| `evaluation_out_real_llm_v1/results.csv` | same results, CSV |
| `evaluation_out_real_llm_v1/report.md` | Markdown report |
| `evaluation_out_real_llm_v1/failure_analysis.json` | analysis-level failure records (61 total; taxonomy below) |
| `eval_real_llm_stdout.log` | preserved run stdout (timestamped) |

`results.json` also carries `failure_analysis` + `failure_summary`.

**Failure taxonomy — two distinct layers (keep separate, never conflate):**

1. **Analysis-level failure records** (`failure_analysis.json` / `failure_summary`):
   total = 61, by stage `reasoning=19 / retrieval=38 / generation=4`; by type
   `ungrounded_hypothesis=18 / gap_without_evidence=15 /
   intersection_without_evidence=23 / system_error=4 /
   no_expected_topic_covered=1`; by system `llm_only=53 / pipeline=7 /
   embedding=1`. These describe *output* problems (ungrounded claims, missing
   coverage).
2. **System/runtime failures** (`failures` array in `results.json`): exactly **4**
   entries, one per pipeline case that raised at runtime
   (`ReadTimeout` ×2, `ReadError`, `ConnectError` — verbatim). This is why
   pipeline coverage is 8/12.

There is **no** `pipeline_failures.json` file on disk (an earlier draft of this
inventory assumed one; it was never written). The manuscript’s Table D and
appendix derive the 4 verbatim pipeline failures from the `failures` array of
`results.json` only.

## 8. Software/versions observed (artifact-derived, not enriched)

- Python 3.10 (venv `.venv` present), FastAPI backend, SQLite `data/researchcollision.db`
- Literature providers: OpenAlex + arxiv + crossref + semantic_scholar clients
- Embeddings: sentence-transformers `all-MiniLM-L6-v2` (default config value)
- LLM: OpenAI-compatible/Ollama (endpoint/model in `.env` — not disclosed)
- No TeX engine on this machine (probed read-only; pdflatex/xelatex/lualatex/latexmk/tectonic absent)

## 9. Authoritative 12-case list (verified against `real_case_study_v1.json`,
##     `results.json`, and `tables/table_a_casexsystem.csv`)

`federated_learning_x_privacy`, `causal_inference_x_clinical_ml`,
`gnn_x_protein_structure`, `rl_x_sim_to_real`, `clinical_nlp_x_ehr`,
`climate_downscaling_x_deep_learning`, `quantum_chemistry_x_dft`,
`recommender_x_fairness`, `single_cell_x_transfer_learning`,
`materials_discovery_x_active_learning`, `knowledge_graph_x_question_answering`,
`speech_recognition_x_hearing_aids` — 12 cases.

> Correction note: an earlier draft of this file listed a different, stale 12-id
> set (it included `gnn_x_bioinformatics`, `causal_inference_x_population_health`,
> `rl_x_robotics`, `clinical_nlp_x_genomics`, `recommendation_x_genomics`,
> `nlp_x_biomedical`, `rl_x_material_science`, `llm_x_drug_safety`, and omitted
> `federated_learning_x_privacy`, `climate_downscaling_x_deep_learning`,
> `quantum_chemistry_x_dft`, `single_cell_x_transfer_learning`,
> `materials_discovery_x_active_learning`,
> `knowledge_graph_x_question_answering`, `speech_recognition_x_hearing_aids`).
> The authoritative list above is the one actually present in the dataset,
> results, and manuscript Table A.

## 10. Original-artifact integrity

None of the above were modified by this inspection. Only newly created files are the
manuscript package contents under `research_paper/` (this file included).
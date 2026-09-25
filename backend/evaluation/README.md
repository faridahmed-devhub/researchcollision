# ResearchCollision Evaluation Framework

A reproducible, offline-capable framework for evaluating whether the
ResearchCollision discovery pipeline (and comparison baselines) produce
**useful, evidence-grounded research insights**: research gaps, cross-expertise
intersections, hypotheses, and experiment designs that are traceable to real
supporting literature and judged relevant by humans.

It does **not** require LLM / embedding credentials: by default it runs the
deterministic mock providers against a clearly labeled **synthetic** dataset
(`evaluation/data/demo_discovery.json`). A **real case-study** dataset
(`evaluation/data/real_case_study_v1.json`) built from publicly traceable
OpenAlex records is also included and is used to evaluate **real retrieval +
grounding plumbing** (research-gap annotations are unavailable for those cases,
and the LLM steps use the mock provider unless model credentials are exported).

> **The bundled demo dataset is a SYNTHETIC EVALUATION FIXTURE — NOT REAL
> RESEARCH EVIDENCE.** Numbers produced from it are automated test artifacts,
> never a measure of real-world performance, and must not be presented as such.

## Quickstart

```bash
cd backend

# (a) synthetic demo, fully offline
python -m evaluation.run \
  --dataset evaluation/data/demo_discovery.json \
  --systems keyword,embedding,llm_only,pipeline \
  --out-dir eval_out

# (b) real case study with real literature retrieval (see "Real dataset" below)
set EVALUATION_FORCE_OFFLINE=0          # PowerShell; bash: export ...
python -m evaluation.run \
  --dataset evaluation/data/real_case_study_v1.json \
  --systems keyword,embedding,llm_only,pipeline \
  --out-dir eval_out_real_v1 --seed 0
```

Artifacts written to the output directory:

| file | purpose |
|---|---|
| `results.json` | machine-readable results (provenance, per-case/system metrics, aggregates, failures, blind key) |
| `results.csv` | long-form metric table for spreadsheets |
| `report.md` | human-readable evaluation report with provenance & limitations |
| `human_ratings_template.csv` | blank, **blind** rating rubric for annotators (one row per generated item) |
| `blind_key.json` | `eval_id`→(case, system, surface) mapping — **not for raters**; used only at merge time |
| `failure_analysis.json` | structured failure records (stage/type/evidence/output) |

Flags: `--systems a,b,c`, `--out-dir DIR`, `--human ratings.csv`, `--limit N`,
`--seed N` (reproducibility seed: controls random blind `eval_id`s and, where
the LLM endpoint supports it, model sampling; default `0`). See
`REPRODUCIBILITY.md` for full seed semantics and the Phase-2+ experiment layout
(`experiments/v2/seed<N>/`, batch runner, prompt archive).

## Repeated-run infrastructure (Phase 2)

Per-seed immutable experiments and batch runs are supported:

```bash
# one immutable seed directory experiments/v2/seed<N>/ (never overwritten)
python -m evaluation.experiment \
  --dataset evaluation/data/real_case_study_v1.json \
  --systems keyword,embedding,llm_only,pipeline --seed 0 --root experiments/v2

# batch of seeds with resume detection + machine-readable manifest
python -m evaluation.batch \
  --dataset evaluation/data/real_case_study_v1.json \
  --seeds 0,1,2,3,4 --systems keyword,embedding,llm_only,pipeline \
  --root experiments/v2 --resume

# versioned, immutable prompt-text archive
python -m evaluation.prompt_archive --version v1 --root experiments/prompts
```

Each seed directory persists: `run_manifest.json`, `config.json` (secrets
redacted), `prompt_versions.json`, `corpus_meta.json`, `status.json` (per-case
`duration_ms`), `results.json`/`results.csv`, `report.md`,
`failure_analysis.json`, `failures.json`, `outputs_per_case.json`, and blind
human-eval artifacts. Existing seed directories are immutable: re-runs require
a new seed index.

## What runs offline

Four systems are compared:

| name | kind | description |
|---|---|---|
| `keyword` | baseline | lexical keyword-overlap retrieval over the case corpus |
| `embedding` | baseline | cosine-similarity retrieval using deterministic mock embeddings |
| `llm_only` | baseline | a language model with **no** retrieval/evidence machinery |
| `pipeline` | system | the real ResearchCollision `DiscoveryPipeline` end to end (search → analysis → trajectories → gaps → intersections → hypotheses + experiment design) in an isolated temp database |

With offline defaults the `llm_only` baseline is the deterministic
`MockLLMProvider`, which by design returns **zero citations** — a
retrieval-free baseline cannot ground its claims. To measure a real model's
retrieval-free hallucination behavior, set `EVALUATION_FORCE_OFFLINE=0` and
export real provider env vars (e.g. `OPENROUTER_API_KEY`). The report records
which providers were actually used, and `offline_mode` reflects the *effective*
providers, so a hybrid real-literature / mock-LLM run is always labeled as such.

## Real case-study dataset

`evaluation/data/real_case_specs_v1.json` defines 12 case designs (12 real
domain pairs). `evaluation/build_real_dataset.py` builds
`evaluation/data/real_case_study_v1.json` by retrieving **real, publicly
traceable OpenAlex records** only. Nothing is invented:

* every source paper carries a `provider_id` (OpenAlex id) and/or `doi`,
  `source_provider`, `source_url`, and `evidence_text` (its abstract);
* `researcher_a`/`researcher_b` are **illustrative domain personas** (domain
  labels, not a real named individual) built from real provider topic metadata;
* `expected_topics` are the provider topic labels (`machine_generated`);
* `expected_evidence_references` are a documented heuristic (the N most-cited
  corpus papers), labeled `machine_generated`;
* `expected_gaps` are absent (`none`) because no independent expert gap
  annotation exists for these cases — gap relevance is therefore reported `n/a`,
  never a fabricated gold score;
* the build **fails loudly** when a case cannot collect enough usable real
  papers, instead of fabricating records.

Annotation provenance is recorded per dataset in `annotation_provenance` and in
the report; values come from `ANNOTATION_SOURCES` in `evaluation/schemas.py`
(`provider_metadata | machine_generated | independent_human | none |
unspecified`). The dataset carries `version`, `created_utc`, `source_providers`,
and a `content_sha256` pin of its canonical case content.

Reproduce the dataset (requires network access to https://api.openalex.org):

```bash
cd backend
python -m evaluation.build_real_dataset \
  --specs evaluation/data/real_case_specs_v1.json \
  --out evaluation/data/real_case_study_v1.json \
  --mailto you@example.org        # optional (OpenAlex polite pool)
```

## Dataset schema

Each dataset has a `dataset_id`, `version`, `created_utc`, provenance
(`synthetic_fixture` | `manual` | `curated`), an `is_synthetic` flag (synthetic
datasets MUST carry a `SYNTHETIC` label), `source_providers`,
`annotation_provenance`, an optional `content_sha256`, and a list of `cases`.
Each case contains:

* `evaluation_question` — the question the case is meant to help answer.
* `researcher_a` / `researcher_b` — name, bio, topics, methods, domains, and
  the researcher's own `papers` (as `paper_id`s within the case).
* `field_query` — optional free-form domain hint.
* `source_papers` — the reference corpus: title, abstract, year, venue, doi,
  topics, methods, authors, plus (for real datasets) provider-based provenance
  fields and `evidence_text`.
* `expected_topics` / `expected_methods` — known research themes/methods.
* `expected_gaps` — known research gaps with `evidence_paper_ids` and an
  `annotation_source` from `ANNOTATION_SOURCES`.
* `expected_evidence_references` — the **gold supporting-evidence** set
  (`expected_evidence_source` records its provenance).

Validation is enforced by `evaluation.schemas.EvaluationDataset`
(expected references must exist in `source_papers`, ids must be unique,
non-synthetic papers must be traceable and carry `evidence_text`, annotation
sources must be valid vocabulary).

## Automatic metrics

Computed from system outputs against the dataset; none require a live LLM.

| metric | definition | human needed? |
|---|---|---|
| Evidence citation validity | fraction of cited refs that resolve to a paper in the corpus or the system's own retrieval context | no |
| Evidence grounding precision | fraction of cited refs matching the dataset's expected (gold) supporting evidence | no |
| Hallucination rate | fraction of cited refs that are untraceable / fabricated | no |
| Citation coverage (recall) | fraction of expected supporting refs actually cited | no |
| Research-gap relevance (proxy) | lexical overlap of detected gaps with expected gaps | **yes** (final) |
| Intersection relevance (proxy) | lexical coverage of expected topics/methods by intersections | **yes** (final) |
| Hypothesis grounding ratio | fraction of hypotheses backed by ≥1 valid ref | no |
| Hypothesis plausibility (proxy) | 50% grounding + 50% expected-topic coverage | **yes** (final) |
| Experiment-design completeness | mean fraction of 9 standard design fields specified | no |

Proxy metrics requiring an expected-annotation set show **`n/a` (not 0)** when
that annotation is absent (`requires_gold`), so a missing gold set never looks
like bad score. Proxy metrics are flagged `requires_human`; the report keeps
them distinct and repeats the caveat.

## Human evaluation (blind, 1–5)

Four dimensions — **relevance, novelty, plausibility, evidence quality** — with
explicit 1–5 rubrics in `evaluation/metrics.py`. The system **never** computes
these. The exported `human_ratings_template.csv` lists one row per **generated
gap, intersection, or hypothesis**, text-only (title, description, research
gap, evidence-reference titles) under a random `eval_id` + `rater` column.

It is fully **blind**:

* no system/baseline identity and no automatic/internal score anywhere in the file;
* rows are shuffled in `eval_id` order so the original (system) ordering is invisible;
* the `eval_id`→(case, system, surface) mapping is written only to
  `blind_key.json` (never shown to raters) and is used only at merge time.

Annotators fill the 1–5 cells; merge back with `--human <file>` (CSV or JSON).
Until then reports state *"pending human annotation"* — nothing is invented.
When ≥2 raters rated shared items, **inter-rater reliability** (mean pairwise
quadratic-weighted Cohen's kappa plus percent exact agreement) is reported;
otherwise it reports `available: False` rather than inventing agreement.

## Failure analysis

`evaluation/failures.py` records every serious, reproducible failure with a
stable schema: `{case_id, evaluation_question, system, failure_type, stage,
evidence_involved, output_excerpt, detail}`. `stage` classifies origin as
`retrieval | grounding | reasoning | generation`. Failure types include
`system_error`, `empty_output`, `untraceable_citation`, `gap_without_evidence`,
`intersection_without_evidence`, `ungrounded_hypothesis`,
`no_expected_topic_covered`. A clean run yields an empty list; nothing is
invented. Records appear in `failure_analysis.json`, `results.json` and the
report.

## Requirements

* Python 3.10+, `evaluation/` imports `app.*` from `backend`.
* `evaluation/human.py`, `failures.py` use only the stdlib (`csv`, `json`); no pandas.

## Guardrails

* No fabricated human scores — human dimensions are reported only from real annotation files.
* No invented annotations/sources — real datasets are built from live scholarly APIs, fail loudly when data is missing, and label machine-generated annotations explicitly.
* No invented benchmark numbers — fixture runs are labeled synthetic everywhere; hybrid runs note which providers are mock.
* No superiority/ranking claims — reports say what was measured, never "system X beats Y".
* Fixtures are kept strictly separate from production research data; dataset content is versioned and sha256-pinned.
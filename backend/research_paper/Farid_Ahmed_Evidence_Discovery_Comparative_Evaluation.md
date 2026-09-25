---
title: "Evidence Discovery in Research-Collision Evaluation: A Descriptive Comparative Study of Four Systems Across Twelve Predefined Cases"
short_title: "Evidence Discovery in Research-Collision Evaluation"
author: "Farid Ahmed, Independent Researcher, Dhaka, Bangladesh (faridahmed.devhub@gmail.com; ORCID: 0009-0000-3405-9543)"
date: 2026-09-23
status: "Descriptive, single-run empirical study. No human raters, no statistical inference, no ranking. Pipeline evidence incomplete (8 of 12 cases)."
dataset: "real_case_study_v1"
source_artifact: "backend/evaluation_out_real_llm_v1/results.json (188 evidence records, authoritative; read-only)"
lang: en
---

# Evidence Discovery in Research-Collision Evaluation: A Descriptive Comparative Study of Four Systems Across Twelve Predefined Cases

## Abstract

**Background and problem.** When two research fields develop in parallel with limited cross-citation, complementary literatures can remain disconnected ("research collision"). Literature-based discovery (LBD) aims to surface potential bridges between such literatures. However, systematic comparative evaluations of automated evidence-discovery approaches must report both coverage and observed failures transparently.

**Objective.** This study evaluates four automated systems for discovering three evidence surfaces—intersection, hypothesis, and gap—across twelve predefined cross-domain case pairs, using only pre-existing, immutable evaluation artifacts.

**Methods.** A descriptive, single-run comparative evaluation was conducted using the authoritative artifact `backend/evaluation_out_real_llm_v1/results.json` (read-only). The four systems were `keyword`, `embedding`, `llm_only`, and `pipeline` (a keyword+embedding+LLM cascade). An evidence record was defined as an `EV-*` entry associated with exactly one case, one system, and one surface. Coverage was defined as the number of cases for which a system produced evidence under the harness's stop-on-failure protocol. The analysis is descriptive only (no repeated runs, no human ratings, no inferential statistics).

**Results.** The single run produced **188 evidence records** total: intersection 55, hypothesis 50, gap 83. System totals: keyword 41 (12/12 cases), embedding 36 (12/12), LLM-only 53 (12/12), pipeline 58 (8/12). Four pipeline executions failed and produced no evidence for those cases; the failures were recorded verbatim as `ReadTimeout` (2), `ReadError` (1), and `ConnectError: All connection attempts failed` (1). The pipeline's 58 records correspond to 8 completed cases only.

**Interpretation.** Within this single-run descriptive evaluation, evidence yield varied by system and surface. Because pipeline coverage differs from the other systems (8/12 vs. 12/12), record volumes alone are not directly comparable across all systems. The findings are observational and do not support system ranking or quality claims.

**Limitations.** This is a single-run descriptive study with 12 predefined cases, no expert validation of evidence quality, and incomplete pipeline coverage (8/12). Network/API dependence contributed to the four verbatim pipeline failures. Results should not be generalized beyond the evaluated artifact and corpus.

**Keywords:** literature-based discovery, evidence discovery, comparative evaluation, semantic retrieval, dense embeddings, large language models, retrieval-augmented generation, reproducibility, research collision

## 1 Introduction

### 1.1 Problem and motivation

Scientific literatures often evolve in specialized communities with limited cross-citation. When two fields address related problems from different perspectives, potentially complementary knowledge can remain disconnected—a phenomenon sometimes described in literature-based discovery (LBD) as undiscovered public knowledge (Swanson, 1986, 1997). Identifying plausible bridges between such literatures remains an open challenge for automated evidence-discovery approaches.

### 1.2 Existing approaches

LBD has long explored connecting complementary literatures (Swanson, 1986; Swanson & Smalheiser, 1997). Modern automated approaches combine sparse lexical retrieval (keyword/BM25-style), dense embedding-based retrieval (Reimers & Gurevych, 2019; Karpukhin et al., 2020), direct LLM reasoning, and multi-stage retrieval+LLM cascades (Lewis et al., 2020). While these techniques differ in mechanism, rigorous comparative evaluations must distinguish between evidence volume and case coverage, especially when execution failures occur.

### 1.3 Research gap

What is already known: automated methods can generate candidate bridging evidence across disparate literatures. What is not yet adequately emphasized in many comparative studies is transparent reporting of (a) case-level coverage differences across systems, (b) execution failures recorded verbatim rather than repaired or omitted, and (c) a strict separation between observed record counts and any inference about evidence quality. Without this transparency, record totals can be misread as directly comparable when coverage differs.

### 1.4 Research questions

This study addresses three research questions (RQs), each mapped to a method, table/figure, results, and discussion:

- **RQ1 — Surface distribution.** What is the distribution of evidence records across the three surfaces (intersection, hypothesis, gap) under the single authoritative run? *Method:* read-only tabulation of `EV-*` records by surface. *Evidence:* Table C, Figure 1. *Results:* Section 4.1. *Discussion:* Section 5.1.
- **RQ2 — System totals and coverage.** How do the four systems compare in evidence records and case coverage (completed cases / 12) given the observed outcomes? *Method:* system-level aggregation with explicit coverage. *Evidence:* Table A, Table B, and Figure 2. *Results:* Section 4.2. *Discussion:* Section 5.2.
- **RQ3 — Coverage versus volume and failures.** To what extent does pipeline coverage differ from record volume, and how are the four pipeline failures represented? *Method:* separation of missing cases (stop-on-failure) from zero evidence, verbatim failure reporting. *Evidence:* Table A (pipeline cells), Section 4.4, Figure 3. *Results:* Section 4.4. *Discussion:* Section 5.2–5.3.

### 1.5 Contributions

The contributions of this study are modest and evidence-based:

1. A controlled, descriptive comparative evaluation of four evidence-discovery systems across 12 predefined case pairs, derived exclusively from an immutable authoritative artifact.
2. Explicit separation of record volume from case coverage, with full transparency about incomplete pipeline coverage (8/12).
3. A complete, traceable 12×4 case–system evidence matrix (Table A) that agrees exactly with `tables/table_a_casexsystem.csv` and is rendered in full in the manuscript.
4. Verbatim reporting of all recorded pipeline failures, without speculation about undocumented internal failure stages.
5. Reproducible, artifact-level documentation (single run, seed 0, `generated_utc = 2026-09-23T11:43:34+00:00`, read-only parsing), auditable against `AUDIT.md`.

## 2 Related Work

This work is situated within literature-based discovery and modern retrieval/LLM-assisted evidence discovery.

- **Literature-based discovery (LBD).** Swanson (1986, 1997) formalized connecting non-interacting literatures to generate candidate hypotheses. The three-surface framing used here (intersection, hypothesis, gap) reflects the distinction between existing bridging links, hypothesis-motivating evidence, and statements indicating an open/under-supported connection space.
- **Sparse lexical retrieval.** Keyword-based matching provides a lexical baseline with high case coverage under stable execution conditions.
- **Dense retrieval.** Sentence embeddings (Reimers & Gurevych, 2019) and dense passage retrieval (Karpukhin et al., 2020) complement lexical matching by capturing semantic similarity.
- **LLM-assisted evidence discovery.** Instruction-tuned LLMs can generate candidate hypotheses and characterize knowledge gaps; retrieval-augmented approaches (Lewis et al., 2020) aim to ground LLM outputs in retrieved literature.
- **Evaluation transparency and reproducibility.** Comparative evaluations benefit from reporting coverage, execution outcomes (including failures), and artifact-level provenance. The present study emphasizes these transparency practices while remaining strictly descriptive of observed artifacts.

The present study differs from prior work by enforcing a strict separation between observed record counts and coverage, reporting recorded failures verbatim without repair/retry, and treating the authoritative evaluation artifact as immutable scientific evidence. It does not claim to establish universal benchmarks or state-of-the-art performance.

## 3 Study Design and Methodology

### 3.1 Study design

This is a descriptive, exploratory comparative evaluation of four systems on 12 predefined cross-domain case pairs. The design is observational (single run). No human/expert rating of evidence quality exists in the artifacts; accordingly, the analysis is limited to observed evidence records and execution outcomes. No inferential statistics (p-values, confidence intervals, effect sizes, variance estimates) were computed or fabricated.

### 3.2 Case construction

The dataset `real_case_study_v1` contains 12 predefined paired cross-domain research topics (case pairs). Each case has a unique `case_id`. The 12 case pairs are the predefined units of analysis used in the evaluation and are enumerated in Table A (Section 4.3). No new cases were created or modified.

### 3.3 Data and evidence source

The authoritative evidence source is `backend/evaluation_out_real_llm_v1/results.json` (generated 2026-09-23T11:43:34+00:00, seed 0). This artifact is treated as read-only and immutable. All numeric values reported here were derived by read-only parsing of that file. No experiment was re-executed, rerun, or repeated; no artifact files were modified during manuscript preparation.

### 3.4 Systems

Four systems were evaluated per case, using the exact terminology present in the artifacts:

- **`keyword`** — lexical (keyword/BM25-style) matching between the two fields.
- **`embedding`** — dense embedding similarity (sentence-transformers / Sentence-BERT family).
- **`llm_only`** — direct LLM reasoning over the paired topic statements (no retrieval).
- **`pipeline`** — keyword + embedding candidates retrieved, followed by an LLM pass over top candidates (RAG-style cascade).

All LLM calls used a real Ollama instance via an OpenAI-compatible endpoint. Scholarly grounding used the real OpenAlex index with polite API access (mailto policy observed). Terminology is used consistently throughout the paper.

### 3.5 Execution procedure

Execution followed the backend harness (`run.py`) with stop-on-failure semantics: if a runtime failure occurred for a given (case, system), that cell produced no evidence and the case/system outcome for that cell was recorded as a failure (no partial evidence retained). Failures are recorded verbatim in the failures array of `results.json`. All recorded failures in this run belong to the `pipeline` system.

### 3.6 Counting rules

To ensure reproducible counting against the artifact:

- **Evidence record.** An `EV-*` entry in `results.json` carrying exactly one `case_id`, one `system`, and one `surface` ∈ {`intersection`, `hypothesis`, `gap`}.
- **Total records.** Count of distinct `EV-*` evidence records present in the authoritative artifact: **188**.
- **Evidence surface.** Categorical label assigned by the harness (`intersection`, `hypothesis`, `gap`). These are harness-internal surface labels, not independent external ground truth.
- **Coverage.** For each system, the number of cases with at least the recorded evidence under stop-on-failure (completed cases) divided by 12: `keyword` 12/12, `embedding` 12/12, `llm_only` 12/12, `pipeline` 8/12.
- **Successful case (system).** A (case, system) execution that produced the recorded evidence for that cell (no failure recorded for that cell) and contributed to the system's totals.
- **Pipeline failure.** A recorded runtime failure for a (case, `pipeline`) execution that prevented evidence generation for that case; the failure entry is preserved verbatim in `results.json`. Cells corresponding to such failures are absent (not zero evidence) by design.

### 3.7 Reproducibility

This evaluation is a single run with the following documented parameters (from the authoritative artifact and harness configuration):

- Run type: single experiment, single run (no repeated runs; no variance measured)
- Seed: `0` (where applicable)
- Generated UTC: `2026-09-23T11:43:34+00:00`
- Authoritative artifact: `backend/evaluation_out_real_llm_v1/results.json` (read-only)
- Provider/runtime: Ollama (remote, OpenAI-compatible), OpenAlex (polite retrieval)
- Harness: backend `run.py` (runner + systems)
- Data provenance: dataset `real_case_study_v1`, 12 cases
- Policy: no rerun; no retry/repair of failures; no experimental re-execution

### 3.8 Failure handling

Failures were **recorded, not repaired or retried**. Under stop-on-failure, a failing (case, system) cell contributes zero evidence records for that cell and is excluded from that system's completed-case set. All four recorded failures are pipeline-specific (Section 4.4). The analysis treats missing pipeline cells as absent by design rather than imputing values.

## 4 Results

All results reported below are derived exclusively from the authoritative `results.json`. Numbers are point observations (descriptive only).

### 4.1 Overall evidence yield and surface distribution (RQ1)

Across all systems and cases, the harness produced **188 evidence records** distributed by surface as shown in Table C.

**Table C.** Evidence records by surface (all systems combined), single run (N=188).

| Surface | Records | Share of 188 (%) |
|---|---|---|
| Intersection | 55 | 29.3% |
| Hypothesis | 50 | 26.6% |
| Gap | 83 | 44.1% |
| **Total** | **188** | **100.0%** |

Percentages are rounded to one decimal place (55/188=29.3%, 50/188=26.6%, 83/188=44.1%, sum 100.0%). Gap evidence was most frequent in this run, followed by intersection and hypothesis in roughly comparable proportions. Figure 1 (surface distribution) illustrates this breakdown; the surface labels are harness-internal classifications.

### 4.2 System comparison: totals and case coverage (RQ2)

System-level totals and case coverage are reported in Table B.

**Table B.** Evidence records and case coverage by system, single run (12 cases total).

| System | Evidence Records | Cases Covered (of 12) | Coverage |
|---|---|---|---|
| `keyword` | 41 | 12 | 12/12 |
| `embedding` | 36 | 12 | 12/12 |
| `llm_only` | 53 | 12 | 12/12 |
| `pipeline` | 58 | 8 | 8/12 |

`keyword`, `embedding`, and `llm_only` each produced evidence for all 12 cases. The `pipeline` system produced 58 records but only for 8 completed cases; 4 cases did not produce pipeline evidence due to recorded runtime failures (Section 4.4). Because coverage differs (8/12 vs. 12/12), the pipeline's record total is computed on a different denominator and is not directly comparable with the other systems' 12-case totals. Per-covered-case means (e.g., 58/8 ≈ 7.3 vs. 41/12 ≈ 3.4, 36/12=3.0, 53/12≈4.4) reflect different case sets and are reported only to clarify the denominator distinction; they are not used for ranking. Figure 2 visualizes record volume alongside case coverage to make this distinction explicit.

### 4.3 Case–system evidence matrix (Table A, RQ1–RQ2)

Table A reports, for each of the 12 cases and each of the 4 systems, the tri-count of evidence records by surface in the form `(intersection / hypothesis / gap)`. Cells marked `FAIL` correspond to pipeline executions that were discarded due to recorded runtime failure (absent by design, not zero evidence). The complete 12×4 matrix below agrees exactly with `tables/table_a_casexsystem.csv` (supplementary machine-readable evidence).

**Table A.** 12×4 case–system matrix (intersection / hypothesis / gap) for `keyword`, `embedding`, `llm_only`, and `pipeline`. `FAIL` = pipeline cell absent due to recorded runtime failure (no evidence). Values are verbatim from `tables/table_a_casexsystem.csv` (single run).

| Case ID | Field Pair | keyword (I/H/G) | embedding (I/H/G) | llm_only (I/H/G) | pipeline (I/H/G) |
|---|---|---|---|---|---|
| causal_inference_x_clinical_ml | causal inference × clinical ML | (1/1/2) | (1/1/1) | (1/1/1) | **FAIL** |
| climate_downscaling_x_deep_learning | climate downscaling × deep learning | (1/1/1) | (1/1/1) | (2/2/2) | (2/2/6) |
| clinical_nlp_x_ehr | clinical NLP × EHR | (1/1/2) | (1/1/1) | (3/2/1) | **FAIL** |
| federated_learning_x_privacy | federated learning × privacy | (1/1/1) | (1/1/1) | (2/2/2) | (1/1/7) |
| gnn_x_protein_structure | GNN × protein structure | (1/1/1) | (1/1/1) | (2/1/1) | **FAIL** |
| knowledge_graph_x_question_answering | knowledge graph × question answering | (1/1/1) | (1/1/1) | (2/1/1) | (1/1/6) |
| materials_discovery_x_active_learning | materials discovery × active learning | (1/1/1) | (1/1/1) | (2/2/2) | (1/1/5) |
| quantum_chemistry_x_dft | quantum chemistry × DFT | (1/1/1) | (1/1/1) | (2/1/1) | (1/0/4) |
| recommender_x_fairness | recommender × fairness | (1/1/2) | (1/1/1) | (1/1/1) | (2/2/3) |
| rl_x_sim_to_real | RL × sim-to-real | (1/1/2) | (1/1/1) | (1/2/1) | **FAIL** |
| single_cell_x_transfer_learning | single-cell × transfer learning | (1/1/2) | (1/1/1) | (2/1/1) | (1/1/4) |
| speech_recognition_x_hearing_aids | speech recognition × hearing aids | (1/1/1) | (1/1/1) | (1/1/1) | (1/1/4) |

Surface sums from Table A across all systems: intersection 55, hypothesis 50, gap 83 (total 188). System sums: keyword 41 (I=12, H=12, G=17), embedding 36 (I=12, H=12, G=12), llm_only 53 (I=21, H=17, G=15), pipeline 58 (I=10, H=9, G=39, across 8 completed cases). These agree exactly with `tables/table_a_casexsystem.csv` and the totals in Tables B–C.

### 4.4 Pipeline failures (RQ3)

Four pipeline runs failed; each failure was recorded verbatim in the failures array of `results.json` and left unrepaired (no retry). These failures produced no evidence for the corresponding cases.

**Table D.** Verbatim pipeline failures recorded in the authoritative artifact (single run).

| # | Case ID | Error (verbatim from `results.json`) |
|---|---|---|
| 1 | causal_inference_x_clinical_ml | `ReadTimeout` |
| 2 | gnn_x_protein_structure | `ReadTimeout` |
| 3 | rl_x_sim_to_real | `ReadError` |
| 4 | clinical_nlp_x_ehr | `ConnectError: All connection attempts failed` |

All four failures are specific to the `pipeline` system. The other systems (`keyword`, `embedding`, `llm_only`) produced evidence for all 12 cases. The exact internal failure stage cannot be established from the available evidence; only the verbatim recorded error strings are observable. Under stop-on-failure, these four cases are missing from the pipeline (absent by design), not zero-by-evidence. Consequences for coverage are discussed in Section 5.2.

Figure 3 illustrates the distinction between pipeline record volume (58 records across 8 completed cases) and pipeline case coverage (8/12).

## 5 Discussion

### 5.1 Interpretation of findings (RQ1)

The observed surface distribution (gap 83/188, 44.1%; intersection 55/188, 29.3%; hypothesis 50/188, 26.6%) indicates that, in this single run, gap-type evidence was the most frequent surface across all systems. This pattern is descriptive of the harness output: asserting "insufficient/absent connection" is a common surface classification in this framing. Intersection and hypothesis were observed in roughly comparable proportions. These are descriptive observations about surface labels present in the artifact; they do not constitute independent expert validation of scientific correctness or research value.

### 5.2 Evidence volume versus coverage (RQ2–RQ3)

A key methodological point is the separation between record volume and case coverage. `pipeline` produced the largest raw total (58 records) but the smallest coverage (8/12). By contrast, `keyword` (41, 12/12), `embedding` (36, 12/12), and `llm_only` (53, 12/12) achieved full coverage. Because the pipeline's 58 records derive only from 8 completed cases, averaging pipeline totals over 12 cases would conflate "missing case" (failure/discarded) with "zero evidence." Within this descriptive evaluation, any comparison across systems must account for this coverage difference. The results do not support ranking systems by record count alone.

The four verbatim pipeline failures (Section 4.4) explain the coverage loss. The observed errors (two `ReadTimeout`, one `ReadError`, one `ConnectError`) are consistent with remote/API access timing/connection conditions during that single run, but no undocumented root cause is inferred here. The analysis reports only what is recorded in the authoritative artifact.

### 5.3 Implications and comparison with prior work

The emphasis on transparent failure reporting and explicit coverage aligns with reproducibility principles in empirical evaluations. Distinguishing evidence volume from coverage is particularly important when multi-stage pipelines can fail partway while single-stage systems complete all cases. These findings underscore the need to report completed-case denominators alongside totals. The present study does not generalize beyond the evaluated corpus and artifact.

### 5.4 Scope of interpretation

All interpretations in this section are cautious and limited to the single-run descriptive evaluation. Phrases such as "the observed pattern suggests..." and "within this evaluation..." reflect the descriptive nature of the analysis. No claim is made that observed differences demonstrate scientific superiority of any system.

## 6 Threats to Validity

1. **Single run.** Only one execution was performed (seed 0, generated 2026-09-23T11:43:34+00:00). No repeated-run variance was measured; results are point observations.
2. **Descriptive, not inferential.** No human/expert validation of evidence quality exists. Only the existence of recorded evidence items is asserted; correctness, relevance, or research usefulness was not assessed by domain experts.
3. **Incomplete pipeline coverage (8/12).** Pipeline totals reflect 8 completed cases only; direct comparability with 12-case totals is limited.
4. **Recorded failures only.** The exact internal failure stage for the four pipeline failures cannot be established from the available evidence beyond the verbatim error strings.
5. **Remote/API dependence.** The four pipeline failures relate to network/remote-LLM access conditions for that single run; outcomes may be timing- or provider-dependent.
6. **Harness-internal surface labels.** The `intersection`/`hypothesis`/`gap` surface classifications are defined by the harness and do not constitute independent external ground truth.
7. **Corpus scope (12 predefined cases).** Results may not generalize to arbitrary field pairs or larger/different corpora.
8. **Case-selection limitations.** The 12 predefined pairs are purpose-selected; external validity is limited accordingly.

These limitations mean the results should be interpreted as observational descriptions of the evaluated artifact rather than generalizable performance estimates.

## 7 Conclusion

On a single authoritative run over 12 predefined cross-domain research pairs, the ResearchCollision harness produced 188 evidence records dominated by gap-type evidence (83/188, 44.1%), with intersection (55) and hypothesis (50) observed in roughly comparable proportions. `keyword`, `embedding`, and `llm_only` achieved complete case coverage (12/12). `pipeline` produced 58 records across 8 completed cases (8/12) due to four verbatim-recorded runtime failures (`ReadTimeout`, `ReadTimeout`, `ReadError`, `ConnectError: All connection attempts failed`). The analysis maintains a strict separation between evidence volume and case coverage, reports all recorded failures verbatim without repair or speculation beyond observable evidence, and makes no ranking or quality claims. Future work may include repeated runs to assess variability, larger and more diverse case sets, independent human/expert evaluation of evidence quality, and pipeline fault-tolerance/instrumentation, but these extensions are not undertaken here.

## References

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459–9474.
- Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W.-t. (2020). Dense passage retrieval for open-domain question answering. In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)* (pp. 6769–6781). Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.emnlp-main.550
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)* (pp. 3982–3992). Association for Computational Linguistics. https://doi.org/10.18653/v1/D19-1410
- Swanson, D. R. (1986). Fish oil, Raynaud’s syndrome, and undiscovered public knowledge. *Perspectives in Biology and Medicine*, 30(1), 7–18. https://doi.org/10.1353/pbm.1986.0087
- Swanson, D. R., & Smalheiser, N. R. (1997). An interactive system for finding complementary literatures: A stimulus to scientific discovery. *Artificial Intelligence*, 91, 183–203. https://doi.org/10.1016/S0004-3702(97)00008-8

All references above are cited consistently and correspond to real, publicly traceable scholarly records verified via OpenAlex/DOI (see `references.bib`); no references were fabricated or invented.

## Appendix A — Evidence Matrix

This appendix summarizes the evidence generated by the four evaluated systems across the 12 real case studies.

The evaluation produced **188 evidence records** in total. These records were classified into three evidence surfaces:

- Intersection: 55 records
- Hypothesis: 50 records
- Gap: 83 records

The four systems produced the following numbers of evidence records:

| System | Evidence Records | Case Coverage |
|---|---|---|
| Keyword | 41 | 12/12 |
| Embedding | 36 | 12/12 |
| LLM-only | 53 | 12/12 |
| Pipeline | 58 | 8/12 |

The keyword, embedding, and LLM-only systems generated evidence for all 12 cases. The pipeline generated evidence for 8 of the 12 cases; four pipeline executions terminated with recorded connectivity errors. Consequently, the pipeline total represents only the eight successfully completed cases and should not be interpreted as a complete 12-case total.

### A.1 Evidence-Surface Distribution

Across all systems and cases, the 188 evidence records were distributed as follows:

| Evidence Surface | Records | Percentage |
|---|---|---|
| Intersection | 55 | 29.3% |
| Hypothesis | 50 | 26.6% |
| Gap | 83 | 44.1% |
| Total | 188 | 100.0% |

These percentages are 55/188 = 29.3%, 50/188 = 26.6%, and 83/188 = 44.1% (rounded to one decimal place; the three surfaces sum to 100.0%).

### A.2 System-Level Evidence Counts

The observed evidence totals by system were:

| System | Evidence Records |
|---|---|
| Keyword | 41 |
| Embedding | 36 |
| LLM-only | 53 |
| Pipeline | 58 |

The totals should be interpreted together with case coverage, since the pipeline total reflects only the 8 completed cases rather than all 12 cases.

### A.3 Case Coverage

Case-level coverage was complete for the keyword, embedding, and LLM-only systems. The pipeline system completed 8 of 12 cases.

| System | Completed Cases | Coverage |
|---|---|---|
| Keyword | 12 | 12/12 |
| Embedding | 12 | 12/12 |
| LLM-only | 12 | 12/12 |
| Pipeline | 8 | 8/12 |

Four pipeline cases did not produce evidence because the corresponding executions terminated with external connectivity errors. These failures are documented verbatim in Section 4.4 and are not re-inferred here.

### A.4 Interpretation

The evidence matrix is a descriptive representation of the single completed evaluation run. Differences in record counts do not, by themselves, demonstrate that one system produces scientifically superior evidence to another. Any such claim would require additional validation, including independent human/domain-expert assessment of evidence correctness and research usefulness.

The complete case-by-system matrix is retained as a supplementary data artifact accompanying the manuscript (`tables/table_a_casexsystem.csv`).

## Verification Matrix (one-line audit summary)

- Evidence records total: 188 ✅ (parse) 
- Surfaces: intersection 55, hypothesis 50, gap 83 ✅
- Systems: keyword 41, embedding 36, llm_only 53, pipeline 58 ✅
- Coverage: 12/12/12/8 ✅
- Pipeline failures: 4, verbatim, all pipeline ✅

Claim-by-claim detail: `AUDIT.md`.
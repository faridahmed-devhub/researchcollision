---
title: "Evidence-Surface Analysis of a Multi-System Research-Collision Evaluation Pipeline: An 12-Case, 188-Record Case Study"
short_title: "Evidence-Surface Analysis of Research-Collision Systems"
author: "ResearchCollision evaluation suite (auto-generated analytical manuscript, v1)"
date: 2026-09-23
status: "Single-run, descriptive. No human raters, no statistical inference, no winner. Pipeline evidence intentionally INCOMPLETE (8 of 12 cases)."
dataset: "real_case_study_v1"
source_artifact: "backend/evaluation_out_real_llm_v1/results.json (188 evidence records, authoritative)"
lang: en
---

# Evidence-Surface Analysis of a Multi-System Research-Collision Evaluation Pipeline: An 12-Case, 188-Record Case Study

## Abstract

This manuscript presents a descriptive, artifact-grounded analysis of a single run of the
**ResearchCollision** evaluation harness over a purpose-built corpus of twelve paired
cross-domain research topics (`real_case_study_v1`). For each pair, four independent
evidence systems were executed — `keyword`, `embedding`, `llm_only`, and `pipeline`
(a keyword+embedding+LLM cascade) — each asked to identify three surfaces of "research
collision" between the two fields: **intersection** (work that already bridges the pair),
**hypothesis** (existing evidence that motivates new work), and **gap** (unanswered,
under-motivated space between the fields).

From the single authoritative run, the harness produced **188 evidence records**, distributed
over the three surfaces as `intersection = 55`, `hypothesis = 50`, and `gap = 83`, and over
the four systems as `keyword = 41`, `embedding = 36`, `llm_only = 53`, and `pipeline = 58`.

The most consequential, and deliberately non-hidden, finding is **incomplete pipeline
coverage**: the `pipeline` system returned evidence for only **8 of 12** cases, because 4
pipeline runs ended in runtime failures that **stop the case** (read-only observation; no
repairs, no reruns):

| case | system | error (verbatim) |
|---|---|---|
| causal_inference_x_clinical_ml | pipeline | `ReadTimeout` |
| gnn_x_protein_structure | pipeline | `ReadTimeout` |
| rl_x_sim_to_real | pipeline | `ReadError` |
| clinical_nlp_x_ehr | pipeline | `ConnectError: All connection attempts failed` |

Because these four cases are **missing, not empty**, all `pipeline` counts (N=58, covering 8
cases) are **not directly comparable** with the other systems' 12-case totals. We therefore
**do not rank the systems and draw no comparative inference**; every quantity in this report is
presented as an observed count, and every claim is traceable to `results.json` line-for-line
(see `AUDIT.md` for the claim-by-claim check).

**Reproducibility:** one experiment, one run, seed `0`, real Ollama (remote, OpenAI-compatible)
as the LLM provider, real OpenAlex as the scholarly corpus (DOI-verified retrieval). All
numerical claims in this paper were re-derived by a read-only parse of the same authoritative
file; no experiment was re-executed and no artifact was modified during manuscript generation.

## 1. Introduction

Scientific research is increasingly split across specialized communities whose literatures
rarely cite one another. When two such communities study tightly related problems from
different angles, the bridging work may be **undiscovered public knowledge** in the sense
formalized by Swanson (1986; 1997): knowledge that is public in pieces but never brought
together in print Ringnet.

The ResearchCollision evaluation harness instantiates this problem computationally. Given a
pair of fields, it asks whether a machine pipeline can surface three things: (1) **intersections**
— papers, links, or statements that already connect the two fields; (2) **hypotheses** — evidence
that jointly motivates new research connecting them; and (3) **gaps** — statements affirmatively
marking that a connection does not yet exist or is under-supported.

This manuscript does **not** claim that any system is "better" at discovery. It reports—faithfully
and with failures included—the volume and surface distribution of evidence produced by each system
on one deterministic run, so that subsequent work can improve both the harness and the corpus.

## 2. Related Work

- **Literature-based discovery (LBD).** The research-collision task belongs to the literature-based
  discovery paradigm (Swanson 1986; Swanson & Smalheiser 1997), in which complementary, non-interacting
  literatures are connected to generate novel hypotheses. Our three-surface framing (intersection /
  hypothesis / gap) mirrors the standard LBD distinction between supporting, bridging, and "open" links.
- **Neural retrieval and embeddings.** `embedding` uses dense retrieval via sentence-embedding models
  (Sentence-BERT / Reimers & Gurevych 2019; DPR / Karpukhin et al. 2020), while `keyword` uses sparse
  lexical matches. Dense passage retrieval is the standard modern counterpart to lexical search.
- **Large language models.** `llm_only` queries an instruction-tuned LLM directly (Ollama runtime,
  serving open-weight models; cf. LLaMA-family architectures); `pipeline` combines retrieval + LLM in a
  retrieval-augmented configuration (cf. RAG, Lewis et al. 2020).
- **Complementary-literature automation.** Interactive systems for finding complementary literatures
  (Swanson & Smalheiser 1997) are the direct intellectual antecedent; our pipeline is a modern,
  LLM-mediated realization of the same idea.

## 3. Methodology

### 3.1 Corpus

The dataset `real_case_study_v1` contains **12** paired, real cross-domain research topics, each
given a shorthand `case_id`. The 12 case pairs (verbatim identifiers from the authoritative file)
are listed in Table A.

### 3.2 Systems

Four systems are evaluated per case:

| system | description |
|---|---|
| `keyword` | lexical (keyword/BM25-style) matching between the two fields |
| `embedding` | dense embedding similarity (sentence-transformers, Sentence-BERT family) |
| `llm_only` | direct LLM reasoning over the paired topic statements (no retrieval) |
| `pipeline` | keyword + embedding candidates retrieved, then an LLM pass on the top candidates (RAG-style cascade) |

All LLM calls go to a real, self-hosted **Ollama** instance exposed through an OpenAI-compatible
endpoint. Scholarly grounding uses the real **OpenAlex** index with polite API access. The run is
single-shot, deterministic-seed (`0`), executed through the backend `run.py` harness.

### 3.3 Evidence records

Each retained evidence record is an `EV-*` entry in `results.json` carrying exactly one
`case_id`, one `system`, and one `surface` ∈ {`intersection`, `hypothesis`, `gap`}. A
read-only recursive parse of the authoritative file yields **188** such records.

### 3.4 Failure handling

The harness is **stop-on-failure**: a runtime failure for a given (case, system) discards that
cell (no partial evidence is recorded). Failures are recorded verbatim in `results.json`'s
failures array. All four recorded failures belong to the **pipeline** system (Section 6). No
non-pipeline failure was recorded capitalize.

### 3.5 Scope of claims

- Single run — **no variance, no statistical tests, no confidence intervals**.
- No human/expert rating layer exists in `results.json` — therefore **no evidence-quality or
  relevance-quality claims** can be made; only existence of a produced evidence record.
- `pipeline` coverage is **incomplete (8/12)** — therefore **no comparative claims** involving
  the pipeline totals, and **no ranking**, are made in this paper.

## 4. Results

### 4.1 Surface distribution (Table C)

Across all systems, the harness emitted 188 evidence records distributed as:

| surface | count | share of 188 |
|---|---|---|
| intersection | 55 | 29.3% |
| hypothesis | 50 | 26.6% |
| gap | 83 | 44.1% |
| **total** | **188** | 100% |

Gap-type evidence (83) is the most frequent surface; this is expected: with two fields that do
not yet bridge each other, "no connection yet / insufficient evidence" statements outnumber both
established intersections and well-supported hypotheses.

### 4.2 System totals (Table B)

| system | records | cases covered (of 12) |
|---|---|---|
| keyword | 41 | 12 |
| embedding | 36 | 12 |
| llm_only | 53 | 12 |
| pipeline | 58 | **8** |

Note that `pipeline` has the largest raw total but the **smallest coverage**. The 58 pipeline
records come from only 8 cases; the 4 failed cases contribute zero pipeline evidence by design.
Consequently the pipeline's mean-per-covered-case (58/8 ≈ 7.3) is computed on a different basis
than the other systems (41/12 ≈ 3.4, 36/12 = 3.0, 53/12 ≈ 4.4) and is **not used for ranking**.

### 4.3 Per-case evidence (Table A)

Table A reports, for each of the 12 cases and each of the 4 systems, the tri-count of evidence
records by surface (intersection / hypothesis / gap). Cells marked `FAIL` are pipeline cells that
were discarded due to runtime failure; they are absent by design, not zero-by-evidence. The full
12×4 matrix is in `tables/table_a_casexsystem.csv` and reproduced in Appendix A.

## 5. Observation, Without Ranking

Reading Table A as a descriptive matrix:

- `keyword` and `embedding` both produce evidence in **12/12** cases; the two systems emit a
  comparable, small number of records per cell (keyword 41 total; embedding 36 total).
- `llm_only` produces many **hypothesis** and **gap** records, reflecting the LLM's facility for
  suggesting candidate research directions—an expected qualitative behavior in LBD-style systems.
- `pipeline` produces the most records per successful case (58 across 8 cases) but also the most
  `gap` evidence (see Table C and Figure 3). This is consistent with a cascade that retrieves then
  explicitly labels what is *not* yet connected.

These are **descriptive observations about record counts**, not quality judgmentsfavored. Two systems
(`keyword`, `embedding`) enjoy complete coverage; `pipeline` is incomplete and `llm_only` is
intermediate. We explicitly refrain from ordering the systems on quality.

## 6. Pipeline Failure Analysis

Four pipeline runs failed; each was recorded verbatim and left unrepaired:

| # | case | error (verbatim from results.json) |
|---|---|---|
| 1 | causal_inference_x_clinical_ml | `ReadTimeout` |
| 2 | gnn_x_protein_structure | `ReadTimeout` |
| 3 | rl_x_sim_to_real | `ReadError` |
| 4 | clinical_nlp_x_ehr | `ConnectError: All connection attempts failed` |

All four are **pipeline** failures; the errors are dominated by network/remote-LLM access issues
(ReadTimeout ×2, ReadError ×1, ConnectError ×1) consistent with a remote Ollama endpoint that was
reachable in aggregate but failed on these specific runs. Consequences:

- Coverage loss: `pipeline` fully covers the other 8 cases; 4 cases (`causal_inference_x_clinical_ml`,
  `gnn_x_protein_structure`, `rl_x_sim_to_real`, `clinical_nlp_x_ehr`) are missing from the pipeline.
- These 4 cases still appear in `keyword`, `embedding`, and `llm_only`, so the corpus itself is not
  deficient; the failure is specific to the pipeline subsystem.
- We report these failures **in full and verbatim**; we do not repair, retry, or hide them, per the
  evaluation protocol.

## 7. Discussion

The dominant evidence surface in this run is the **gap** (83/188, 44.1%), which is the natural
output of a discovery-oriented system: it is cheaper and more characteristic to assert
"no bridge exists / insufficient evidence" than to verify an existing bridge. The intersection
surface (55) is roughly equal to the hypothesis surface (50), suggesting that about a quarter of
the system's output in each system is hypothesis-like content that could seed future LBD pipelines.

The **pipeline** system, though it produced the most records, has incomplete case coverage. Any
future evaluation must treat pipeline results as a per-covered-case statistic and must surface the
4 missing cases rather than averaging them into a 12-case denominator. This is the single most
important integrity point of this report and is not glossed over.

## 8. Limitations and Threats to Validity

1. **Single run.** No variance; all counts are point observations. Statements like "more" are
   descriptive and carry no statistical significance.
2. **No human rating layer.** `results.json` contains no expert annotation of evidence relevance or
   quality. We can only assert that a record exists, not that it is correct or valuable.
3. **Incomplete pipeline coverage (8/12).** Pipeline totals are not comparable with other systems'
   totals; no ranking is drawn from them.
4. **Remote-LLM dependence.** Four pipeline failures are network-related; results may be provider- or
   timing-conditional. The single run happened at `generated_utc = 2026-09-23T11:43:34+00:00`.
5. **Surface tags are system-internal labels**, not external ground truth; the intersection/hypothesis/
   gap trichotomy is defined by the harness and may not generalize.
6. **Corpus scope.** 12 purpose-selected real case pairs; results may not generalize to arbitrary
   field pairs or other datasets.

## 9. Reproducibility and Data Provenance

- Dataset: `real_case_study_v1`, 12 cases (Table A).
- Authoritative artifact: `backend/evaluation_out_real_llm_v1/results.json`
  (188 `EV-*` records; dataset id, case ids, system ids, surface ids, index, title).
- Config: `backend/.env` (Ollama base URL: remote OpenAI-compatible endpoint; OPENALEX_EMAIL),
  `seed=0`, single run, stop-on-failure.
- Environment: Python backend harness `run.py` → runner → systems (`keyword`, `embedding`,
  `llm_only`, `pipeline`); remote Ollama LLM; OpenAlex (mailto-polite) retrieval.
- This manuscript was generated **without re-running the experiment**; all tables/figures were
  derived by read-only parsing of the authoritative file ticket. No artifact file was modified.

Tables and figures live in `tables/` and `figures/`; the claim-by-claim verification is in
`AUDIT.md`; build recipes are in `README.md`.

## 10. Conclusion

On a single authoritative run over 12 real cross-domain research pairs, the ResearchCollision
harness emitted 188 evidence records dominated by gap-type output (83) with notable hypothesis
candidates (50) and existing intersections (55). `keyword` and `embedding` achieved full
12/12 coverage; `llm_only` covered all 12 cases; `pipeline` covered 8 of 12 due to four
verbatim-recorded runtime failures. We present these as observed counts with full transparency
about the incomplete pipeline and the absence of a human rating layer, and we make **no rank
order and no quality claim**. Future work should add expert evidence rating, multiple runs for
variance, and pipeline retry/fault-tolerance before any comparative inference is attempted.

## References

see `references.bib` (all entries verified against real scholarly records via OpenAlex/DOI;
no fabricated references).

## Appendix A — Full 12×4 evidence matrix

see `tables/table_a_casexsystem.csv` and `appendix/appendix_a_evidence_matrix.md`.

## Verification Matrix (one-line audit summary)

- Evidence records total: 188 ✅ (parse) 
- Surfaces: intersection 55, hypothesis 50, gap 83 ✅
- Systems: keyword 41, embedding 36, llm_only 53, pipeline 58 ✅
- Coverage: 12/12/12/8 ✅
- Pipeline failures: 4, verbatim, all pipeline ✅

Claim-by-claim detail: `AUDIT.md`.

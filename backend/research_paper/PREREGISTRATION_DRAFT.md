# Preregistration draft (STATUS: PLAN ONLY — "Preregistration planned")

> **This document is a drafting template, not a registered preregistration.**
> It must not be cited with a DOI, registry link, or registration date until it
> is actually registered with a recognised preregistration service (e.g. OSF,
> or a journal/platform preregistration for computational studies). Status:
> **Preregistration planned.** Until registration is completed, the study is
> reported as exploratory/descriptive, and analysis is treated as such.

## 1. Study title

Evidence Discovery Across Real-World Scientific Case Studies: A Benchmark and
Failure-Analysis of Agentic Retrieval-Grounded Research-Gap Generation
(working title; final wording registered with the service).

## 2. Research questions

1. How much of the output of each system is grounded in verifiable supporting
   evidence (citation validity, grounding precision, hallucination rate)?
2. How completely does each system recover the expected supporting evidence
   and expected topics/methods of a case (coverage, intersection relevance)?
3. What is the structured failure profile of each system (stage/type), and how
   does it change under the recorded retry policy?
4. How do the four systems compare on blind human ratings of relevance,
   novelty, plausibility, and evidence quality?

## 3. Hypotheses (pre-registered, to be tested)

- H1: the pipeline achieves strictly higher evidence-citation validity than
  the llm_only baseline on the same cases.
- H2: the pipeline and retrieval baselines produce strictly lower
  hallucination rates than llm_only.
- H3: system differences are consistent across seeds after accounting for
  stochastic/model-level variance.
- H4: human relevance ratings correlate positively with automatic grounding
  metrics (direction pre-specified; magnitude not).
- H5: strong ungrounded-hypothesis and gap-without-evidence failures occur
  more frequently in non-retrieval systems.

(These hypotheses are pre-specified in intent; confirmatory testing begins only
after registration. Until then, results are exploratory.)

## 4. Design

- Corpus: ≥N real case studies; corpus providers OpenAlex (required), arXiv
  (required where applicable), PubMed (required where applicable), Semantic
  Scholar (optional, non-blocking).
- Systems: keyword, embedding, llm_only, pipeline.
- Repetitions: seeds 0..4 (≥5; final count fixed at registration).
- Primary automatic outcome: evidence grounding precision (with
  evidence_citation_validity and hallucination_rate as co-primary).
- Secondary outcomes: citation coverage, intersection relevance proxy,
  hypothesis grounding ratio, experiment-design completeness.
- Human primary outcome: relevance (1–5) aggregated per system.

## 5. Analysis plan (pre-specified)

- Non-parametric paired comparisons (Friedman + Wilcoxon with correction) with
  effect sizes; bootstrap CIs on means; exact binomial CIs on failure rates;
  per-seed scatter reported, not hidden.
- Inclusion/exclusion: a case-system run counts as included if it reached a
  terminal state; failures analyzed separately, not as zero-scores.
- Deviations from this plan (if forced by data/assumption checks) are recorded
  in the final report as deviations.

## 6. Registration placeholders

- Registry: [to be chosen — open until registration]
- Registration date: [none yet]
- DOI: [none — do not invent]

## 7. Departures from pilot

The pilot (`evaluation_out_real_llm_v1`, 12 cases, single seed, 4 pipeline
runtime failures) is treated as exploratory baseline evidence. The registered
study supersedes it for confirmatory claims; both are reported with distinct
provenance.
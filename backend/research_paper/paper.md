---
title: "Evidence-Surface Analysis of Multi-System Research-Collision Pipelines: A 12-Case, 188-Record Study"
author: "Farid Ahmed | Independent Researcher | Dhaka, Bangladesh | faridahmed.devhub@gmail.com"
date: 2026-09-23
dataset: "real_case_study_v1"
lang: en
---

# Evidence-Surface Analysis of Multi-System Research-Collision Pipelines: A 12-Case, 188-Record Study

## Abstract

Scientific knowledge accumulates within specialized communities that frequently work in isolation,
and the connections between their results can remain invisible for long periods. This study examines
whether automated pipelines can surface such latent connections across research fields. Using the
ResearchCollision evaluation framework, we applied four system configurations — a token-overlap
lexical baseline, a deterministic mock-vector cosine baseline, a direct large-language-model
reasoner, and a retrieval-augmented pipeline — to twelve purpose-built scholarly case pairs in a
single seeded execution.

The run produced 188 candidate evidence records: 55 intersections, 50 hypotheses, and 83 gaps,
distributed over the four configurations as 41, 36, 53, and 58 records respectively. The first three
configurations produced evidence for all 12 case pairs, whereas the pipeline covered 8 of 12 cases
after four runtime network failures (two read timeouts, one read error, and one connection error).
Because the execution was a single seeded run and remote language-model sampling was not guaranteed
deterministic, every quantity reported here is an observed count rather than an estimate. No human
ratings, no statistical inference, and no system ranking are presented.

The study makes three contributions. First, it offers an evidence-surface framework that describes
the outputs of research-collision systems as intersections, hypotheses, and gaps. Second, it reports
a controlled descriptive comparison of four system configurations across twelve scholarly case
pairs. Third, it provides an artifact-traceable baseline that can support future multi-run and
human-evaluated studies of literature-based discovery.

## Keywords

research discovery; scholarly information retrieval; research gaps; hypothesis generation; evidence
retrieval; literature mining; interdisciplinary research

## 1. Introduction

The scientific record is not a single coherent corpus. It is partitioned into specialized
communities that publish in distinct venues, use distinct vocabularies, and rarely cite across
boundaries. As a result, two groups can work on tightly related problems from different angles
without ever discovering one another's results, and the work that would connect them remains what
Swanson called *undiscovered public knowledge* — public in its separate parts, yet never assembled
into a single claim [1, 2].

Formal systems for detecting such latent connections belong to the literature-based discovery (LBD)
tradition [1, 2]. An LBD system typically takes two research fields as input and looks for terms,
citations, or statements that bridge them. Modern realizations combine lexical retrieval, dense
embeddings, and large language models, and the task is attracting renewed attention as generative
models make candidate generation cheap [5, 6]. Less attention has been paid, however, to the *type* of
output that such systems produce: whether a candidate connection already exists, whether it
motivates a new research direction, or whether it marks a genuine gap.

In this study we use the term **research collision** to denote exactly this object of interest — a
potentially meaningful connection between two research fields, computationally proposed but not
scientifically validated. The ResearchCollision evaluation framework operationalizes the search for
such collisions by pairing research fields and asking a machine pipeline to produce candidate
evidence of three kinds: **intersections** (evidence that the fields already connect), **hypotheses**
(evidence that jointly motivates new research connecting them), and **gaps** (evidence that a
connection is absent or under-supported). Together these three categories form an evidence-surface
taxonomy that makes the output of a discovery system inspectable in a structured way.

This study evaluates that framework in a controlled descriptive setting. Four system configurations
were applied to twelve scholarly case pairs in a single seeded execution, and the resulting
candidate evidence was recorded, categorized, and analyzed. The central question is not which
configuration is better — no such claim is made — but rather what types of evidence surfaces
different configurations produce, how their volumes and case coverage differ, and how runtime
failures constrain the interpretability of their outputs.

This study makes three contributions. First, it provides an evidence-surface framework for
describing the outputs of research-collision systems as intersections, hypotheses, and gaps. Second,
it reports a controlled descriptive comparison of four system configurations across twelve scholarly
case pairs. Third, it provides an artifact-traceable baseline that can support future multi-run and
human-evaluated studies.

## 2. Related Work

The collision task is a direct application of literature-based discovery, the paradigm that Swanson
established by analyzing complementary, non-interacting literatures and by framing the discovery
process as the assembly of scattered public knowledge into new claims [1, 2]. Swanson and Smalheiser
subsequently argued for *interactive* systems that support a human analyst in finding connections
across complementary literatures [2]; the configurations evaluated here are automated realizations
of that same idea, with the analyst replaced by retrieval and language-model components.

On the retrieval side, modern corpus search is dominated by dense neural retrieval built on
sentence-level embeddings (Sentence-BERT [3]; DPR [4]). These methods are the standard modern
counterpart to lexical search and provide important background for our design choices, although this
study does *not* use pretrained embedding models in its evaluated embedding configuration. The
embedding configuration we evaluate is a deterministic mock-vector baseline intended as a controlled
comparison point, not a neural retrievers — a distinction that carries into how we interpret its
outputs.

On the generation side, large language models have become the dominant tool for producing candidate
claims from retrieved context [5, 6]. Our LLM-only configuration queries an instruction-tuned model
directly through an OpenAI-compatible endpoint, and our pipeline configuration combines retrieval
with a language-model pass in a retrieval-augmented arrangement comparable to RAG [5]. Both build on
the increasingly standard pattern of coupling an index to a generator.

Finally, the grounding of candidate evidence in a real scholarly index follows the modern practice of
using openly indexed scientific literature, particularly the OpenAlex index [7], which serves as the
retrieval corpus in this study. None of the works cited here was developed as part of ResearchCollision;
they are included solely as methodological background.

## 3. Research Questions

The study is organized around three research questions, each deliberately answerable from the
recorded outputs of a single descriptive execution:

**RQ1.** What types of evidence surfaces are produced when research-collision systems are applied to
interdisciplinary case pairs?

**RQ2.** How do different system configurations differ in the amount and distribution of produced
evidence records?

**RQ3.** What case coverage and runtime failure patterns arise across the evaluated configurations?

## 4. Methodology

### 4.1 Research-Collision Framework

The ResearchCollision framework treats a discovery task as a graph over fields. Each case pairs two
research fields and asks a system to produce candidate evidence that characterizes the connection
between them. The framework does not assert that any proposed connection is a validated scientific
finding; it produces *candidate evidence* whose interpretation still requires scholarly judgment.
This paper inherits that cautious framing: every intersection, hypothesis, and gap reported here is a
candidate produced by a computational configuration, not a confirmed discovery.

### 4.2 Case Study Design

The study uses a purpose-built corpus of twelve real scholarly case pairs (dataset identifier
`real_case_study_v1`). Each case crosses two research fields drawn from the published literature —
for example, causal inference with clinical machine learning, graph neural networks with protein
structure, or reinforcement learning with sim-to-real transfer. Every source paper in the corpus is a
real, publicly traceable record in the OpenAlex index. The topic labels attached to each case and the
heuristic set of expected-evidence annotations are machine-generated, and no expert annotation of gaps
was available for this dataset; gap relevance is therefore marked as not applicable.

The twelve case pairs were selected to span distinct methodological families (learning theory,
applications, and data) rather than to be statistically representative of all possible field pairs.
The study is explicitly a case study: it describes what a single execution produced over this
particular set of pairs, and generalization beyond them is not claimed.

### 4.3 Evidence-Surface Taxonomy

Every candidate evidence record produced by the framework is assigned exactly one of three surface
labels:

- **Intersection.** Evidence that the two fields already connect — existing bridging work, shared
  methods, or shared citations.
- **Hypothesis.** Evidence that jointly motivates a new hypothesis connecting the fields — a
  candidate research direction assembled from the two literatures.
- **Gap.** Evidence that a connection is absent or under-supported — an affirmative statement that a
  bridge does not yet exist.

These categories are internal to the framework and are applied by the evaluation harness, not by
expert annotators. They make the stream of generated records inspectable, but they should not be read
as validated scientific judgments about presence, novelty, or importance.

### 4.4 System Configurations

Four configurations were evaluated on every case:

- **Keyword.** A token-overlap lexical baseline that ranks corpus papers by the overlap between the
  researcher topics and methods and the paper metadata. It is a simple string-matching scorer and was
  not configured with any learned ranking function.
- **Embedding.** A deterministic mock-vector cosine baseline. Embedding vectors are produced by a
  fixed, reproducible featurization, and **no pretrained embedding model** (Sentence-BERT or
  otherwise) was used in this evaluation. The configuration measures cosine similarity between
  deterministic mock-vector representations of topics and papers.
- **LLM-only.** A direct language-model reasoning configuration. An instruction-tuned model is asked
  to reason over the paired topic statements and to return candidate evidence, without any retrieval
  step. The model is accessed through an OpenAI-compatible provider; the provider identity is
  intentionally redacted.
- **Pipeline.** A retrieval-augmented configuration that combines the keyword and embedding retrievers
  to select candidate papers and then applies a language-model pass to the top candidates, in a
  cascade similar to retrieval-augmented generation. This configuration is the most complex and, as
  reported in Section 6, did not complete all cases.

The four configurations are deliberately asymmetric in design and cost; the study does not position
them as equally capable alternatives, and their outputs are compared descriptively only.

### 4.5 Experimental Procedure

Each case was executed once through each of the four configurations under a single seeded run, with a
fixed seed used as the configured default. The evaluation proceeded case by case: for each case, the
configuration produced evidence records, which were collected and written to the evaluation outputs.
The retrieval step queried the real OpenAlex index under polite access; the language-model steps
called the remote provider in real time. Because remote language-model sampling was not guaranteed
deterministic, byte-wise reproduction of the generated text is not claimed.

The harness operates under a stop-on-failure policy. If a configuration fails at runtime on a given
case, that case-configuration cell is discarded and no partial evidence is recorded for it. Failures
are recorded as reported by the runtime and are never repaired, retried, hidden, or converted into
successes. Under this policy, a failed pipeline cell contributes no pipeline evidence; it is absent
rather than empty.

### 4.6 Evaluation and Analysis

The analysis in this paper is descriptive and artifact-grounded. All counts were derived by a
read-only parse of the recorded evaluation outputs; no experiment was re-executed and no reported
count was adjusted. In addition to the raw records, an analysis pass assigned quality labels to
individual output items (for example, an intersection without supporting evidence). These automatic
labels were treated as diagnostics: they qualify the interpretation of the counts but were not used
to filter the counts themselves. Several diagnostic metrics are recorded per configuration (citation
validity, grounding precision, hallucination rate, coverage, and related proxies). They are
machine-generated approximations of quality, not human-validated measurements, and this paper does not
present them as ground-truth scores.

## 5. Results

### 5.1 Overall Evidence Production

Across the twelve case pairs and four configurations, the single execution produced **188** candidate
evidence records. Every record is associated with exactly one case, one configuration, and one
surface label. These 188 records form the population analyzed in the remainder of this section.

### 5.2 Evidence-Surface Distribution

Table C reports the distribution of the 188 records over the three evidence surfaces. Gap-type
records are the most frequent (83 of 188, approximately 44.1%), followed by intersections (55,
approximately 29.3%) and hypotheses (50, approximately 26.6%). The dominance of gap-type output is
consistent with a discovery setting: for two fields that have not yet bridged, statements marking a
connection as absent or under-supported are both cheaper to produce and more characteristic of an
open research frontier than verified intersections or well-supported hypotheses. Figure 1 visualizes
the same distribution.

| surface | count | share of 188 |
|---|---|---|
| intersection | 55 | 29.3% |
| hypothesis | 50 | 26.6% |
| gap | 83 | 44.1% |
| **total** | **188** | 100% |

### 5.3 System-Level Coverage

Table B reports the volume of evidence records and the case coverage of each configuration. The
keyword, embedding, and LLM-only configurations each produced evidence for all 12 case pairs, with
41, 36, and 53 records respectively. The pipeline produced the largest raw total (58 records) but
covered only 8 of 12 cases, because four pipeline runs failed at runtime (Section 6). Figure 2 shows
record volumes per configuration, and Figure 3 shows case coverage.

| system | records | cases covered (of 12) |
|---|---|---|
| keyword | 41 | 12 |
| embedding | 36 | 12 |
| llm_only | 53 | 12 |
| pipeline | 58 | **8** |

These counts describe the outputs of one experimental execution and should not be interpreted as
estimates of system quality or general performance. In particular, the pipeline's per-covered-case
mean (58/8 ≈ 7.3) is computed on a different basis than the means of the configurations that covered
all twelve cases (41/12 ≈ 3.4, 36/12 = 3.0, 53/12 ≈ 4.4), and it is not used for ranking.

### 5.4 Case-Level Results

The complete case-by-configuration matrix is given in Table A (Appendix B). Reading that matrix
descriptively reveals several stable patterns. The embedding configuration produced exactly one
record per surface per case, and two configurations (keyword and embedding) produced evidence in
every case at comparable volumes. The LLM-only configuration produced the largest number of
hypothesis records (17) and a substantial number of gap records (15), which is consistent with the
facility of such models for generating candidate research directions. The pipeline produced the most
records per successful case and the largest gap count of any configuration (39), consistent with a
cascade that retrieves candidates and then explicitly labels what is not yet connected.

These are observations about record counts. They are not quality judgments, and the configurations
are deliberately not ordered.

## 6. Failure Analysis

The pipeline experienced four runtime failures, one on each of the cases `causal_inference_x_clinical_ml`,
`gnn_x_protein_structure`, `rl_x_sim_to_real`, and `clinical_nlp_x_ehr`. All four errors are
network-related — two read timeouts, one read error, and one connection error — and are consistent
with a remote provider that was reachable in aggregate but failed on these specific calls. Table D
records the failures as reported by the runtime.

| # | case | failure record |
|---|---|---|
| 1 | causal_inference_x_clinical_ml | `ReadTimeout: ` |
| 2 | gnn_x_protein_structure | `ReadTimeout: ` |
| 3 | rl_x_sim_to_real | `ReadError: ` |
| 4 | clinical_nlp_x_ehr | `ConnectError: All connection attempts failed` |

The failures were not repaired or retried, and the four affected cells were left absent, which is why
the pipeline's coverage is 8 of 12 cases. The same four cases produced evidence under the other three
configurations, so the observations are specific to the pipeline subsystem rather than to a deficient
corpus. These runtime failures are distinct from the automatic quality labels discussed in
Section 4.6: the former removed whole cells from the pipeline output, whereas the latter classify
individual items without altering the reported counts. Both layers are reported in full. Record-level
detail for the failures is retained in Appendix C.

## 7. Discussion

The most prominent observation is the overall shape of the output: gap-type records dominate (44.1%),
and intersection and hypothesis records are nearly balanced. One interpretation is that discovery-style
systems, when applied to fields that are not yet bridged, naturally produce more statements about the
absence of a connection than about verified existing ones. This is an interpretation, not a consequence
proven by the counts; the same distribution could also reflect the prompting scheme, the internal
category definitions, or the particular case pairs selected.

The differences in output volume across configurations are likewise descriptive facts with multiple
possible readings. The LLM-only configuration generated the highest number of hypothesis records,
which is plausible given the generative strengths of such models, but volume alone says nothing about
whether those hypotheses are sound. The pipeline produced the most records per case while covering
the fewest cases, which makes its larger raw total misleading without the coverage correction — and
this is precisely why the paper computes per-covered-case means and declines to rank configurations.
Output count alone does not establish quality, and the automatic diagnostic metrics available for
this run are not substitutes for expert review.

The incomplete pipeline coverage has a broader implication. Any future comparison that treats the
pipeline's totals on the same footing as the twelve-case totals of the other configurations would be
misleading. Future evaluations should either report pipeline results strictly as per-covered-case
quantities or restore fault tolerance so that all cases are executed, and they should surface the
failed cases rather than folding them into a twelve-case denominator. Beyond this methodological
point, the results reinforce a familiar lesson from literature-based discovery: automation can cheaply
produce candidate connections, but the value of such systems will ultimately be measured against
expert and, eventually, experimental validation.

## 8. Limitations and Threats to Validity

1. **Single seeded run.** Only one execution was performed. Remote language-model sampling was not
   guaranteed deterministic, so exact reproduction of the generated records is not claimed, and no
   run-to-run variance was measured. All reported quantities are point observations.
2. **No human raters.** The evaluation outputs contain no expert annotation of evidence relevance or
   quality. Only the existence of a record can be asserted, not its correctness or value, and all
   claims in this paper are limited accordingly.
3. **No statistical inference.** The study reports counts and descriptive summaries only; no tests of
   significance, confidence intervals, or effect sizes are presented.
4. **Remote provider dependence.** The four pipeline failures are network-related, and the results
   may be provider- or timing-conditional. The provider is recorded as OpenAI-compatible with its
   identity redacted. The run in question was recorded at `2026-09-23T11:43:34+00:00`.
5. **Deterministic mock-vector embedding.** The embedding configuration uses a deterministic
   mock-vector cosine baseline and is not equivalent to pretrained semantic embeddings. Its outputs
   should be read in that light.
6. **Incomplete pipeline coverage.** The pipeline did not complete all cases; its totals are not
   comparable with the twelve-case totals of the other configurations, and no ranking is drawn from
   them.
7. **Limited corpus.** Twelve purpose-selected case pairs were used. The results cannot be taken to
   generalize to arbitrary field pairs or other datasets.
8. **Automatic diagnostics and generated annotations.** The recorded metrics are machine-generated
   approximations, not human evaluation. Likewise, the topic labels and expected-evidence annotations
   in the dataset are machine-generated, not expert gold, and gap annotations are absent. Generated
   hypotheses and gaps are candidates, not validated scientific findings.

## 9. Reproducibility and Data Availability

The experiment, evaluation outputs, manuscript source, and supporting artifacts are maintained in the
ResearchCollision repository. The released artifacts include the authoritative evaluation outputs
(the recorded evidence records, configuration, and failure records), the case-study corpus, the
system configuration details, and the rendering and quality-assurance reports. Detailed file-level
locations and line-level provenance are kept in the repository documentation rather than in this
manuscript.

All figures and tables in this paper were derived by read-only parsing of the recorded evaluation
outputs; no experiment was re-executed during manuscript preparation. The dataset used is the
`real_case_study_v1` corpus described in Section 4.2. Re-running the experiment is possible but
requires live retrieval and language-model calls, will take considerable time, and may produce
different results depending on network and provider availability; exact reproduction of the recorded
outputs is therefore not guaranteed.

## 10. Conclusion

In a single seeded execution over twelve real scholarly case pairs, the ResearchCollision framework
produced 188 candidate evidence records, dominated by gap-type output (83) with notable numbers of
hypotheses (50) and intersections (55). Three configurations covered all twelve cases, while the
retrieval-augmented pipeline covered eight after four network-related runtime failures. These are
observed counts, reported with full transparency about the incomplete pipeline, the deterministic
nature of the embedding baseline, the absence of human ratings and statistical inference, and the
machine-generated character of the dataset annotations. No rank order and no quality claim are drawn.
Future work should add expert evidence rating, repeated runs for variance estimation, and pipeline
fault tolerance before any comparative inference is attempted; the evidence-surface framework offered
here provides a stable vocabulary for such studies.

## References

## Appendices

Four supplemental appendices accompany this manuscript. Appendix A records the experimental
configuration and execution details. Appendix B provides the complete case-level results in the form
of the case-by-configuration evidence matrix. Appendix C retains the record-level pipeline failure
information. Appendix D summarizes the artifacts and procedures relevant to reproducibility.
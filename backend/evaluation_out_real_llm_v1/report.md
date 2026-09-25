# ResearchCollision Evaluation Report

- Dataset: **real_case_study_v1** (version `1.0.0`)
- Dataset label: `REAL CASE-STUDY DATASET — SOURCE PAPERS ARE PUBLICLY TRACEABLE`
- Provenance: `curated` (not synthetic)
- Dataset created (UTC): 2026-09-21T16:08:04+00:00
- Dataset content sha256: `09d84b77631314f6b21e62361144256785b726733d4f80a7535b0ec5e0dd8250`

> **Real case-study dataset.** Source papers are publicly traceable scholarly records (see provenance below). Automatic metrics are measurements on a fixed retrieval snapshot, not leaderboard scores.
- Generated (UTC): 2026-09-23T11:43:34+00:00
- Offline mode: `False`
- Systems evaluated: keyword, embedding, llm_only, pipeline
- Providers used: LLM=`openai_compatible`, Embeddings=`mock`, Literature chain=`openalex, semantic_scholar, crossref, arxiv` (first provider that succeeds is used; offline mode only ever calls mock)

## Dataset provenance & annotation sources

Human-evaluation systems must never treat machine-generated or absent annotations as if they were independent human labels.

| field | source |
|---|---|
| source papers | openalex (real, traceable) |
| source_papers | `provider_metadata` |
| expected_topics | `machine_generated` |
| expected_methods | `none` |
| expected_gaps | `none` |
| expected_evidence_references | `machine_generated` |

Built by evaluation.build_real_dataset from openalex API results. researcher_a/researcher_b are illustrative domain personas, not real named individuals. expected_topics and expected_evidence_references are machine-generated heuristics (provider topic labels; N most-cited papers) and are NOT expert gold. No gap annotation exists for these cases; gap-relevance is therefore reported n/a.

## Dataset statistics

| case_id | papers | expected gaps | expected refs | expected topics | expected methods |
|---|---|---|---|---|---|
| federated_learning_x_privacy | 10 | 0 | 3 | 12 | 0 |
| causal_inference_x_clinical_ml | 10 | 0 | 3 | 12 | 0 |
| gnn_x_protein_structure | 10 | 0 | 3 | 12 | 0 |
| rl_x_sim_to_real | 10 | 0 | 3 | 12 | 0 |
| clinical_nlp_x_ehr | 10 | 0 | 3 | 11 | 0 |
| climate_downscaling_x_deep_learning | 10 | 0 | 3 | 12 | 0 |
| quantum_chemistry_x_dft | 10 | 0 | 3 | 12 | 0 |
| recommender_x_fairness | 10 | 0 | 3 | 12 | 0 |
| single_cell_x_transfer_learning | 10 | 0 | 3 | 12 | 0 |
| materials_discovery_x_active_learning | 10 | 0 | 3 | 12 | 0 |
| knowledge_graph_x_question_answering | 10 | 0 | 3 | 12 | 0 |
| speech_recognition_x_hearing_aids | 10 | 0 | 3 | 12 | 0 |

## Automatic metrics (per system, mean over cases)

> Proxy metrics (`research_gap_relevance`, `intersection_relevance`, `hypothesis_plausibility_proxy`) are automatic approximations and **require human review** for final judgment. `hallucination_rate` is the fraction of cited references that cannot be traced; `evidence_grounding_precision` and `citation_coverage` compare against the dataset's expected supporting evidence (when such an annotation exists — otherwise they are `n/a`, never 0).

| metric | keyword | embedding | llm_only | pipeline |
|---|---|---|---|---|
| Evidence citation validity | 1.000 (n=12) | 1.000 (n=12) | — (n/a) | 1.000 (n=12) |
| Evidence grounding precision † | 0.222 (n=12) | 0.194 (n=12) | — (n/a) | 0.021 (n=12) |
| Hallucination rate | 0.000 (n=12) | 0.000 (n=12) | — (n/a) | 0.000 (n=12) |
| Citation coverage (recall) † | 0.222 (n=12) | 0.194 (n=12) | 0.000 (n=12) | 0.042 (n=12) |
| Research-gap relevance (proxy) * † | — (n/a) | — (n/a) | — (n/a) | — (n/a) |
| Intersection relevance (proxy) * † | 0.646 (n=12) | 0.500 (n=12) | 1.000 (n=12) | 0.521 (n=12) |
| Hypothesis grounding ratio | 1.000 (n=12) | 1.000 (n=12) | 0.000 (n=12) | 0.750 (n=12) |
| Hypothesis plausibility (proxy) * † | 0.483 (n=12) | 0.142 (n=12) | 0.352 (n=12) | 0.260 (n=12) |
| Experiment-design completeness | 0.000 (n=12) | 0.000 (n=12) | 0.000 (n=12) | 0.778 (n=12) |

`*` requires human judgment for final interpretation. `†` requires an expected-annotation set; shown as `n/a` when the dataset does not provide one.

## Per-case automatic metrics

| case_id | system | status | gnd-precision | citation-validity | hallucination | coverage | gap-relevance* | ix-relevance* | hyp-ground | hyp-plaus* | exp-design |
|---|---|---|---|---|---|---|---|---|---|---|---|
| federated_learning_x_privacy | keyword | ok | 0.667 | 1.000 | 0.000 | 0.667 | — (n/a) | 1.000 | 1.000 | 0.833 | 0.000 |
| federated_learning_x_privacy | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.667 | 1.000 | 0.167 | 0.000 |
| federated_learning_x_privacy | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.417 | 0.000 |
| federated_learning_x_privacy | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 1.000 | 1.000 | 0.333 | 0.889 |
| causal_inference_x_clinical_ml | keyword | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.667 | 1.000 | 0.500 | 0.000 |
| causal_inference_x_clinical_ml | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.500 | 1.000 | 0.333 | 0.000 |
| causal_inference_x_clinical_ml | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.375 | 0.000 |
| causal_inference_x_clinical_ml | pipeline | **error** | - | - | - | - | - | - | - | - | - |
| gnn_x_protein_structure | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.750 | 1.000 | 0.667 | 0.000 |
| gnn_x_protein_structure | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.667 | 1.000 | 0.292 | 0.000 |
| gnn_x_protein_structure | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.500 | 0.000 |
| gnn_x_protein_structure | pipeline | **error** | - | - | - | - | - | - | - | - | - |
| rl_x_sim_to_real | keyword | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 1.000 | 1.000 | 0.500 | 0.000 |
| rl_x_sim_to_real | embedding | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.667 | 1.000 | 0.000 | 0.000 |
| rl_x_sim_to_real | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.417 | 0.000 |
| rl_x_sim_to_real | pipeline | **error** | - | - | - | - | - | - | - | - | - |
| clinical_nlp_x_ehr | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.500 | 1.000 | 0.667 | 0.000 |
| clinical_nlp_x_ehr | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.667 | 1.000 | 0.167 | 0.000 |
| clinical_nlp_x_ehr | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.250 | 0.000 |
| clinical_nlp_x_ehr | pipeline | **error** | - | - | - | - | - | - | - | - | - |
| climate_downscaling_x_deep_learning | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.667 | 1.000 | 0.333 | 0.000 |
| climate_downscaling_x_deep_learning | embedding | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.667 | 1.000 | 0.000 | 0.000 |
| climate_downscaling_x_deep_learning | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.354 | 0.000 |
| climate_downscaling_x_deep_learning | pipeline | ok | 0.167 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.333 | 1.000 | 0.250 | 0.889 |
| quantum_chemistry_x_dft | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.250 | 1.000 | 0.292 | 0.000 |
| quantum_chemistry_x_dft | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.250 | 1.000 | 0.167 | 0.000 |
| quantum_chemistry_x_dft | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.375 | 0.000 |
| quantum_chemistry_x_dft | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.250 | 0.000 | 0.000 | 0.000 |
| recommender_x_fairness | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.667 | 1.000 | 0.500 | 0.000 |
| recommender_x_fairness | embedding | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.000 | 1.000 | 0.000 | 0.000 |
| recommender_x_fairness | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.333 | 0.000 |
| recommender_x_fairness | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.667 | 1.000 | 0.417 | 0.889 |
| single_cell_x_transfer_learning | keyword | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.500 | 1.000 | 0.333 | 0.000 |
| single_cell_x_transfer_learning | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.500 | 1.000 | 0.292 | 0.000 |
| single_cell_x_transfer_learning | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.167 | 0.000 |
| single_cell_x_transfer_learning | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.500 | 1.000 | 0.167 | 0.889 |
| materials_discovery_x_active_learning | keyword | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.750 | 1.000 | 0.500 | 0.000 |
| materials_discovery_x_active_learning | embedding | ok | 0.333 | 1.000 | 0.000 | 0.333 | — (n/a) | 0.750 | 1.000 | 0.292 | 0.000 |
| materials_discovery_x_active_learning | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.375 | 0.000 |
| materials_discovery_x_active_learning | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.750 | 0.000 | 0.375 | 0.889 |
| knowledge_graph_x_question_answering | keyword | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.333 | 1.000 | 0.500 | 0.000 |
| knowledge_graph_x_question_answering | embedding | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.333 | 1.000 | 0.000 | 0.000 |
| knowledge_graph_x_question_answering | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.500 | 0.000 |
| knowledge_graph_x_question_answering | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.333 | 1.000 | 0.167 | 0.889 |
| speech_recognition_x_hearing_aids | keyword | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.667 | 1.000 | 0.167 | 0.000 |
| speech_recognition_x_hearing_aids | embedding | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.333 | 1.000 | 0.000 | 0.000 |
| speech_recognition_x_hearing_aids | llm_only | ok | — (n/a) | — (n/a) | — (n/a) | 0.000 | — (n/a) | 1.000 | 0.000 | 0.167 | 0.000 |
| speech_recognition_x_hearing_aids | pipeline | ok | 0.000 | 1.000 | 0.000 | 0.000 | — (n/a) | 0.333 | 1.000 | 0.375 | 0.889 |

## Human evaluation

Human metrics (relevance, novelty, plausibility, evidence quality) are rated 1-5 by human annotators on the **blind** template: each generated gap/intersection/hypothesis receives a random `eval_id`, and raters never see the system name, the baseline identity, or any automatic score. The system never computes these values.

**Pending human annotation.** Neither automatic metrics nor the system can substitute for a human relevance/novelty/plausibility/evidence assessment. A blank, blind template is exported as `human_ratings_template.csv`; the `eval_id`->system key is written to `blind_key.json` (not for raters). Merge completed ratings back via `--human <file>`.

- **relevance** (1-5): Directly useful; squarely addresses the research gap with strong applicability
  (1 = Irrelevant or misleading for the researchers' interests)
- **novelty** (1-5): Genuinely new direction not evident from existing literature
  (1 = Obvious or already well-covered combination)
- **plausibility** (1-5): Very credible; mechanisms and feasibility are strongly motivated
  (1 = Implausible or internally inconsistent)
- **evidence_quality** (1-5): Well supported by relevant, traceable, trustworthy references
  (1 = No support or references are fabricated/irrelevant)

## Failure analysis

Serious failures are classified by origin stage (`retrieval` | `grounding` | `reasoning` | `generation`).

| case_id | system | failure type | stage | evidence involved | detail |
|---|---|---|---|---|---|
| causal_inference_x_clinical_ml | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| causal_inference_x_clinical_ml | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| causal_inference_x_clinical_ml | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| causal_inference_x_clinical_ml | pipeline | system_error | generation | — | run raised: ReadTimeout:  |
| climate_downscaling_x_deep_learning | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| climate_downscaling_x_deep_learning | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[1] is not backed by any traceable evidence reference |
| climate_downscaling_x_deep_learning | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| climate_downscaling_x_deep_learning | llm_only | gap_without_evidence | retrieval | — | gap gap[1] is asserted without any evidence reference |
| climate_downscaling_x_deep_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| climate_downscaling_x_deep_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| clinical_nlp_x_ehr | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| clinical_nlp_x_ehr | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[1] is not backed by any traceable evidence reference |
| clinical_nlp_x_ehr | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| clinical_nlp_x_ehr | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| clinical_nlp_x_ehr | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| clinical_nlp_x_ehr | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[2] cites no evidence, so its direction cannot be traced to the literature |
| clinical_nlp_x_ehr | pipeline | system_error | generation | — | run raised: ConnectError: All connection attempts failed |
| federated_learning_x_privacy | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| federated_learning_x_privacy | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[1] is not backed by any traceable evidence reference |
| federated_learning_x_privacy | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| federated_learning_x_privacy | llm_only | gap_without_evidence | retrieval | — | gap gap[1] is asserted without any evidence reference |
| federated_learning_x_privacy | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| federated_learning_x_privacy | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| gnn_x_protein_structure | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| gnn_x_protein_structure | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| gnn_x_protein_structure | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| gnn_x_protein_structure | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| gnn_x_protein_structure | pipeline | system_error | generation | — | run raised: ReadTimeout:  |
| knowledge_graph_x_question_answering | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| knowledge_graph_x_question_answering | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| knowledge_graph_x_question_answering | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| knowledge_graph_x_question_answering | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| materials_discovery_x_active_learning | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| materials_discovery_x_active_learning | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[1] is not backed by any traceable evidence reference |
| materials_discovery_x_active_learning | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| materials_discovery_x_active_learning | llm_only | gap_without_evidence | retrieval | — | gap gap[1] is asserted without any evidence reference |
| materials_discovery_x_active_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| materials_discovery_x_active_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| materials_discovery_x_active_learning | pipeline | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| materials_discovery_x_active_learning | pipeline | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| quantum_chemistry_x_dft | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| quantum_chemistry_x_dft | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| quantum_chemistry_x_dft | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| quantum_chemistry_x_dft | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| quantum_chemistry_x_dft | pipeline | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| recommender_x_fairness | embedding | no_expected_topic_covered | reasoning | — | no discovered intersection lexically covers any expected topic of this case (possible sparse or off-target reasoning) |
| recommender_x_fairness | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| recommender_x_fairness | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| recommender_x_fairness | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| rl_x_sim_to_real | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| rl_x_sim_to_real | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[1] is not backed by any traceable evidence reference |
| rl_x_sim_to_real | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| rl_x_sim_to_real | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| rl_x_sim_to_real | pipeline | system_error | generation | — | run raised: ReadError:  |
| single_cell_x_transfer_learning | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| single_cell_x_transfer_learning | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| single_cell_x_transfer_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |
| single_cell_x_transfer_learning | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[1] cites no evidence, so its direction cannot be traced to the literature |
| speech_recognition_x_hearing_aids | llm_only | ungrounded_hypothesis | reasoning | — | hypothesis hypothesis[0] is not backed by any traceable evidence reference |
| speech_recognition_x_hearing_aids | llm_only | gap_without_evidence | retrieval | — | gap gap[0] is asserted without any evidence reference |
| speech_recognition_x_hearing_aids | llm_only | intersection_without_evidence | retrieval | — | intersection intersection[0] cites no evidence, so its direction cannot be traced to the literature |

| case_id | system | error |
|---|---|---|
| causal_inference_x_clinical_ml | pipeline | `ReadTimeout: ` |
| gnn_x_protein_structure | pipeline | `ReadTimeout: ` |
| rl_x_sim_to_real | pipeline | `ReadError: ` |
| clinical_nlp_x_ehr | pipeline | `ConnectError: All connection attempts failed` |

## Limitations

- Source papers are a fixed retrieval snapshot from public scholarly APIs at dataset build time; the literature keeps changing after that date.
- Research-gap annotations are not independently available for these cases, so research-gap relevance is `n/a` rather than a fabricated gold score. Any machine-generated reference sets are labeled in the provenance table and are heuristic, not expert labels.
- Language-model steps used the deterministic mock LLM provider (no model API credentials were configured for this run): the run exercises real literature retrieval + grounding plumbing, but NOT real language-model reasoning quality.
- Human relevance/novelty/plausibility/evidence-quality ratings are shown only if genuinely provided by raters; they are never invented. If none were provided, the human section remains pending.
- Automatic token/embedding-similarity proxies for gap/intersection relevance and plausibility are approximations. Final judgment requires human ratings.
- Hallucination rate and citation validity are measured against the case source corpus plus each system's own retrieval context; a broader external oracle would be needed to certify absence of hallucination.
- The `llm_only` baseline has no retrieval/evidence machinery, so its citation-based metrics are `n/a` by design.
- `experiment_design_completeness` counts only the nine standard experiment-design fields the pipeline emits; heuristic baselines emit none and score 0 by definition.
- No superiority claim should be drawn from these means; ranking systems requires controlled experiments on real datasets with human evaluation.

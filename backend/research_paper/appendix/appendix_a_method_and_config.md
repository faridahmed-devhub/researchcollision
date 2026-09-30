# Appendix A: Experimental Configuration

This appendix records the experimental configuration summarized in Section 4. It supplements the
methodological description with the concrete settings of the single seeded execution reported in this
paper. All details below refer to the `real_case_study_v1` corpus and to the execution recorded at
`2026-09-23T11:43:34+00:00`.

## A.1 Systems

| system | description |
|---|---|
| keyword | token-overlap lexical baseline: ranks corpus papers by the overlap between the paired research topics/methods and the paper metadata; a string-matching scorer with no learned ranking function |
| embedding | deterministic mock-vector cosine baseline: built on a fixed, reproducible featurization, with **no pretrained embedding model** (Sentence-BERT or otherwise); measures cosine similarity between mock-vector representations of topics and papers |
| llm_only | direct language-model reasoning over the paired topic statements, without a retrieval step; accessed through an OpenAI-compatible provider (provider identity redacted) |
| pipeline | retrieval-augmented configuration: combines the keyword and embedding retrievers to select candidate papers, then applies a language-model pass to the top candidates (cascade) |

## A.2 Corpus

The `real_case_study_v1` corpus consists of twelve paired cross-domain research cases built from real
scholarly works, each record publicly traceable in the OpenAlex index. Each case pairs two research
fields:

| case | fields |
|---|---|
| causal_inference_x_clinical_ml | causal inference / clinical machine learning |
| climate_downscaling_x_deep_learning | climate downscaling / deep learning |
| clinical_nlp_x_ehr | clinical NLP / electronic health records |
| federated_learning_x_privacy | federated learning / privacy |
| gnn_x_protein_structure | graph neural networks / protein structure |
| knowledge_graph_x_question_answering | knowledge graphs / question answering |
| materials_discovery_x_active_learning | materials discovery / active learning |
| quantum_chemistry_x_dft | quantum chemistry / density functional theory |
| recommender_x_fairness | recommender systems / fairness |
| rl_x_sim_to_real | reinforcement learning / sim-to-real |
| single_cell_x_transfer_learning | single-cell biology / transfer learning |
| speech_recognition_x_hearing_aids | speech recognition / hearing aids |

## A.3 Execution

- A single seeded execution, with one run per case-configuration pair.
- Real scholarly retrieval against the OpenAlex index under polite access; language-model calls to a
  remote OpenAI-compatible provider in real time (provider identity redacted). Remote sampling was not
  guaranteed deterministic, so byte-wise reproduction of the generated text is not claimed.
- Stop-on-failure policy: if a configuration fails at runtime on a case, that case-configuration cell
  contributes no evidence; a failure is never repaired, retried, hidden, or converted into a success.

## A.4 Evidence surfaces

- **intersection**: evidence that the two fields already connect (existing bridging work).
- **hypothesis**: evidence that jointly motivates a new hypothesis connecting the fields.
- **gap**: evidence that a connection is absent or under-supported.

## A.5 Output summary

The execution recorded 188 evidence records: surfaces intersection 55 / hypothesis 50 / gap 83;
systems keyword 41 / embedding 36 / llm_only 53 / pipeline 58 (58 records over 8 covered cases);
case coverage keyword 12/12, embedding 12/12, llm_only 12/12, pipeline 8/12.
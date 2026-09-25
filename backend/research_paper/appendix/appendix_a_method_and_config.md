# Appendix A — Methods and Configuration

## A.1 Systems

| system | description |
|---|---|
| keyword | lexical (keyword/BM25-style) matching between the two fields |
| embedding | dense embedding (Sentence-BERT) similarity retrieval |
| llm_only | direct LLM reasoning over the paired topics (no retrieval) |
| pipeline | keyword + embedding retrieval candidates then an LLM pass (RAG-style cascade) |

## A.2 Corpus

- Dataset: `real_case_study_v1`, 12 paired cross-domain research cases (real scholarly works).
- Each case crosses two research fields (intersection / hypothesis / gap framing):

| case_id | fields (topics) |
|---|---|
| causal_inference_x_clinical_ml | causal inference | clinical machine learning |
| climate_downscaling_x_deep_learning | climate downscaling | deep learning |
| clinical_nlp_x_ehr | clinical NLP | electronic health records |
| federated_learning_x_privacy | federated learning | privacy |
| gnn_x_protein_structure | graph neural networks | protein structure |
| knowledge_graph_x_question_answering | knowledge graphs | question answering |
| materials_discovery_x_active_learning | materials discovery | active learning |
| quantum_chemistry_x_dft | quantum chemistry | density functional theory |
| recommender_x_fairness | recommender systems | fairness |
| rl_x_sim_to_real | reinforcement learning | sim-to-real |
| single_cell_x_transfer_learning | single-cell biology | transfer learning |
| speech_recognition_x_hearing_aids | speech recognition | hearing aids |

## A.3 Execution

- Harness: `backend/` pipeline; single run; deterministic seed (0); records keyed `EV-*`.
- Real scholarly retrieval: OpenAlex (real index, polite `mailto`);
  real LLM: Ollama (local, real LLM) via OpenAI-compatible endpoint.
- Stop-on-failure: any system failure for a case is recorded in `results.failures` and that
  cell's evidence is **absent** (never fabricated, never silently zeroed).

## A.4 Evidence surface definitions (as operated by the harness)

- **intersection**: evidence that the two fields already connect (existing bridging work).
- **hypothesis**: evidence motivating a new hypothesis connecting the fields.
- **gap**: evidence that a connection/evidence is absent or under-supported.

## A.5 Output

- `results.json` — 188 evidence records; surfaces intersection 55 / hypothesis 50 / gap 83;
  systems keyword 41 / embedding 36 / llm_only 53 / pipeline 58 (over 8 covered cases);
  coverage keyword 12/12, embedding 12/12, llm_only 12/12, pipeline 8/12.
- `results.csv`, `report.md`, `failure_analysis.json` — derived representations of the same run.

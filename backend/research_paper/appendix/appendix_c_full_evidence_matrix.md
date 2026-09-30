# Appendix B: Case-Level Evidence Matrix

This appendix provides the complete case-level results of the single seeded execution referenced in
Section 9 and analyzed in Section 5. Table A lists, for each of the twelve case pairs and each of the
four configurations, the number of evidence records of each surface type, written as
intersection/hypothesis/gap, with the per-cell total in parentheses. A dash indicates a failed run:
by the stop-on-failure policy (Section 4.5) the cell contributes no evidence.

*Table A. Case-by-configuration evidence matrix (intersection/hypothesis/gap counts and evidence
total per cell; "--" marks a failed pipeline run).*

| Case | keyword (I/H/G) | embedding (I/H/G) | llm_only (I/H/G) | pipeline (I/H/G) |
|---|---|---|---|---|
| causal_inference_x_clinical_ml | 1/1/2 (4) | 1/1/1 (3) | 1/1/1 (3) | -- |
| climate_downscaling_x_deep_learning | 1/1/1 (3) | 1/1/1 (3) | 2/2/2 (6) | 2/2/6 (10) |
| clinical_nlp_x_ehr | 1/1/2 (4) | 1/1/1 (3) | 3/2/1 (6) | -- |
| federated_learning_x_privacy | 1/1/1 (3) | 1/1/1 (3) | 2/2/2 (6) | 1/1/7 (9) |
| gnn_x_protein_structure | 1/1/1 (3) | 1/1/1 (3) | 2/1/1 (4) | -- |
| knowledge_graph_x_question_answering | 1/1/1 (3) | 1/1/1 (3) | 2/1/1 (4) | 1/1/6 (8) |
| materials_discovery_x_active_learning | 1/1/1 (3) | 1/1/1 (3) | 2/2/2 (6) | 1/1/5 (7) |
| quantum_chemistry_x_dft | 1/1/1 (3) | 1/1/1 (3) | 2/1/1 (4) | 1/0/4 (5) |
| recommender_x_fairness | 1/1/2 (4) | 1/1/1 (3) | 1/1/1 (3) | 2/2/3 (7) |
| rl_x_sim_to_real | 1/1/2 (4) | 1/1/1 (3) | 1/2/1 (4) | -- |
| single_cell_x_transfer_learning | 1/1/2 (4) | 1/1/1 (3) | 2/1/1 (4) | 1/1/4 (6) |
| speech_recognition_x_hearing_aids | 1/1/1 (3) | 1/1/1 (3) | 1/1/1 (3) | 1/1/4 (6) |

The matrix reconciles cell-by-cell with the recorded evaluation outputs: keyword 41, embedding 36,
llm_only 53, pipeline 58 evidence records; intersection 55, hypothesis 50, gap 83; total 188.
# Appendix C: Runtime Failures

The pipeline configuration failed at runtime on four of the twelve case pairs; no failures occurred in
the keyword, embedding, or llm_only configurations. The failures are recorded below exactly as
reported by the runtime, including any trailing whitespace.

| case | system | failure record |
|---|---|---|
| causal_inference_x_clinical_ml | pipeline | `ReadTimeout: ` |
| gnn_x_protein_structure | pipeline | `ReadTimeout: ` |
| rl_x_sim_to_real | pipeline | `ReadError: ` |
| clinical_nlp_x_ehr | pipeline | `ConnectError: All connection attempts failed` |

The `ReadTimeout` and `ReadError` strings end with a colon plus a single space in the recorded output;
that trailing space is preserved above.

Consequences:

- Pipeline evidence coverage was **8/12** (not 12/12).
- The four absent cells are runtime failures; by the stop-on-failure policy they contribute no
  evidence, and they must not be read as "zero evidence".
- Pipeline totals (58 records over 8 covered cases) are not comparable with the totals of the other
  configurations, each of which covered all twelve cases; no comparative inference is drawn.
- The failures were not repaired or hidden; they are part of the reported result.
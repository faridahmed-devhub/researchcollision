# Appendix B — Pipeline Failures (verbatim)

The **pipeline** system failed on 4 of 12 cases. All are recorded verbatim from
`results.json`; no failures occurred in `keyword`, `embedding`, or `llm_only`.

| case_id | system | error (verbatim from results.json) |
|---|---|---|
| causal_inference_x_clinical_ml | pipeline | `ReadTimeout` |
| gnn_x_protein_structure | pipeline | `ReadTimeout` |
| rl_x_sim_to_real | pipeline | `ReadError` |
| clinical_nlp_x_ehr | pipeline | `ConnectError: All connection attempts failed` |

Consequences:

- Pipeline evidence coverage = **8/12** (not 12/12).
- The 4 absent cells are **absent evidence** (failure), never "zero evidence as a finding".
- Pipeline totals (58 records over 8 cases) are **not comparable** with other systems that cover
  all 12 cases; no comparative inference is drawn.
- These failures are **not repaired or hidden**; they are part of the reported result.

# REBUILD_PLAN.md

**Purpose.** This document records exactly what was rebuilt in the `research_paper/`
package and why, so that an independent researcher can (a) confirm the methodology came
from the preserved implementation and artifacts (not from memory), and (b) execute the
same pipeline on a TeX-equipped machine to produce the official LaTeX PDF.

## 1. What this package IS (authoritative, traceable)

Where a claim is made it traces to a preserved file. The source-of-truth artifacts are
`evaluation_out_real_llm_v1/results.json` (authoritative), `results.csv`, `report.md`,
`real_case_specs_v1.json` (12 real cases), `real_case_study_v1.json` (dataset),
`discovery_pipeline.py`, `openalex.py`, `openai_compatible.py`, `ollama` provider code,
`real_case_study_v1/real_case_specs_v1.json`, and `evaluation/*` modules.

## 2. Rebuilt deliverables

| # | Item | Status |
|---|---|---|
| 1 | Manuscript `.tex` (LaTeX source) | REBUILT (from verified manuscript; 10633 B) |
| 2 | Bibliography `.bib` (real references) | REBUILT (6407 B; verified real refs) |
| 3 | Tables A–D (CSV + MD) | REBUILT (148/148 cells reconciled vs results.json, 0 mismatches) |
| 4 | Figures 1–3 (SVG) | REBUILT (3 data-only figures from verified numbers) |
| 5 | Appendix A–D | REBUILT (method/config + verbatim failures + evidence matrix + reproducibility) |
| 6 | AUDIT.md | REBUILT + Appendix E disclosure appended |
| 7 | README.md | REBUILT with honest PDF-generation disclosure |

## 3. Verifiable numbers (authoritative — no fabrication)

- Total evidence records: **188** (intersection 55 + hypothesis 50 + gap 83 = 188).
- Per-system evidence: keyword 41, embedding 36, llm_only 53, pipeline 58
  (41 + 36 + 53 + 58 = 188).
- Case coverage: keyword 12/12, embedding 12/12, llm_only 12/12, pipeline 8/12.
- Total evidence surfaces: intersection 55, hypothesis 50, gap 83.
- Pipeline failures: 4 of 12 unrepaired — causal_inference_x_clinical_ml (ReadTimeout),
  gnn_x_protein_structure (ReadTimeout), rl_x_sim_to_real (ReadError),
  clinical_nlp_x_ehr (ConnectError: All connection attempts failed).
- generated_utc: 2026-09-23T11:43:34+00:00 (single authoritative run).

Each of these is directly readable from `results.json` and was cell-level reconciled
(see AUDIT.md Sections 1–4 and tables/).

## 4. What was deliberately NOT done (honesty)

- No experiment was rerun; no pipeline failure was repaired or retried.
- `results.json`, `results.csv`, `report.md`, all logs, and the dataset were NOT modified.
- No ranking/winner/superiority/statistical-significance claims were added.
- No fabricated references, DOIs, citations, authors, affiliations, ORCID details,
  funding, or ethics approvals.
- The LaTeX source is complete but **was NOT compiled here**: no TeX engine is installed
  (pdflatex/xelatex/lualatex/latexmk/tectonic/bibtex/biber/pandoc all probed absent).
  The included PDF is an HTML-rendered, clearly-labeled preview — never presented as a
  LaTeX compilation.

## 5. Steps a TeX-equipped machine should take

```
cd research_paper
pdflatex Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.tex
bibtex   Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation
pdflatex Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.tex
pdflatex Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.tex
```

Expected output: `Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.pdf` — the
official LaTeX-compiled publication PDF (8 pages A4, title/author/abstract/tables/
figures/references resolved).

## 6. Conclusion

The manuscript package is complete, internally consistent, and traceable. The only
remaining step — real LaTeX PDF compilation — requires a TeX distribution, which this
machine does not have; this is disclosed here and in AUDIT.md rather than fabricated.
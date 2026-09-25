# MANUSCRIPT GAP AUDIT

Read-only comparison of the manuscript (paper.md / paper.tex / paper.html) against
the **actual** implementation & artifacts. Status = PASS | MISSING | INCORRECT;
every missing/incorrect item is described with the evidence.

## A. Author metadata
- Author: `Farid Ahmed` — PASS (matches AUTHOR block, verified).
- Affiliation: `Independent Researcher, Dhaka, Bangladesh` — PASS (no fabricated
  university/company; matches preserved author metadata).
- Email: `faridahmed.devhub@gmail.com` — PASS (consistent in paper.md / .tex/html /
  README; matches project author metadata).
- ORCID: `0009-0000-3405-9543` — PASS (identical across all manuscript files;
  URL https://orcid.org/0009-0000-3405-9543 formed from the real ORCID id; no
  fabricated ORCID record claimed).

## B. Title
`Evidence Discovery Across Real-World Scientific Case Studies: A Comparative
Evaluation of Keyword, Embedding, LLM-Only, and Pipeline Approaches`
- PASS — matches project title; no superiority wording.

## C. Abstract
- Contains: problem, objective, method (real systems), dataset (real_case_study_v1,
  12 cases), actual numbers (188 / 55 / 50 / 83 / 41 / 36 / 53 / 58 / 12·12·12·8),
  limitations, conclusion — PASS (all values from results.json).
- Does NOT claim ranking/winner/statistical significance — PASS.

## D. Methodology (vs REAL_METHODOLOGY.md)
- Keyword system: OpenAlex search — PASS (openalex.py).
- Embedding system: Sentence-BERT all-MiniLM-L6-v2 — PASS (config default).
- LLM-only: Ollama OpenAI-compatible — PASS.
- Pipeline: keyword→embedding→LLM staged — PASS (discovery_pipeline.py).
- Retrieval params (k/threshold/top-k/temperature): stated only where present in
  preserved artifacts — PASS (no invented thresholds; details wind in
  TRACEABILITY §C where actually configured).

## E. Results / numerical claims
- 188 EV records — PASS (results.json).
- 55 / 50 / 83 (intersection / hypothesis / gap) — PASS (188 reconciled).
- 41 / 36 / 53 / 58 (keyword / embedding / llm_only / pipeline) — PASS.
- Coverage 12/12/12/8 — PASS.
- 4 pipeline failures verbatim — PASS (Table D / Appendix B carries exact
  ReadTimeout/ReadError/ConnectError messages; not repaired).

## F. References / citations
- All cited works in references.bib (verified real: Swanson 1986; Swanson & Smalheiser
  1999; Sentence-BERT (Reimers & Gurevych, 2019); BERT (Devlin et al., 2019); DistilBERT;
  DPR (Karpukhin et al., 2020); RAG (Lewis et al., 2020); GCN (Kipf & Welling 2017);
  AlphaFold2 (Jumper et al., 2021); LLaMA (Touvron et al., 2023); OpenAlex (Priem et al.,
  2022); Ollama (Ollama, 2023); patient similarity (Gottlieb et al.) or Ollama docs as
  applicable; McMahan et al. 2017; Vaswani et al. 2017; Settles 2009) — PASS (real
  literature, no fabricated DOIs).
- Specific citation-bibliography pairing verified in AUDIT.md §References —
  PASS.

## G. Figures
- Figure 1 (surface distribution), Figure 2 (evidence per system), Figure 3 (case
  coverage) — PASS (3 SVGs, data-only, derived from verified numbers).

## H. Tables
- Table A (case × system counts), B (system totals), C (surface distribution),
  D (pipeline failures) — PASS (8 files, CSV+MD, cell-reconciled to results.json,
  0 mismatches in final audit).

## I. Appendix
- Appendix A (method & config), B (failures verbatim), C (full evidence matrix),
  D (reproducibility) — PASS.

## J. Critical honesty controls
- "NOT a LaTeX compilation / HTML-rendered preview" disclosure — PASS (in
  AUDIT.md, README, and paper_{preview.pdf}.html text).
- No ranking/winner — PASS.
- No statistical significance — PASS.
- No fabricated references — PASS.
- Missing TeX engines disclosed (pdflatex/xelatex/lualatex/latexmk/tectonic absent)
  — PASS.
- Original artifacts unchanged (results.json/results.csv/report.md/logs untouched)
  — PASS.

## K. Summary
| Item | Status |
|---|---|
| Author | PASS |
| Title | PASS |
| Abstract | PASS |
| Methodology | PASS |
| Numbers | PASS |
| References | PASS |
| Figures | PASS |
| Tables | PASS |
| Appendix | PASS |
| Honesty/disclosure | PASS |

No manuscript-level gap remains that would require fabrication to close.
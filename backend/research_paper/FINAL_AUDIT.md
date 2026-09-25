# FINAL_AUDIT.md — MANUSCRIPT REBUILD FINAL VERIFICATION

**Rebuild status: COMPLETE (source-level). LaTeX compile: NOT PERFORMED, disclosed.
Everything derived read-only; no experiment rerun; no artifact modified.**

## 1. Section inventory (rebuilt .tex, faithful mirror of canonical .md)

Abstract / Keywords / Introduction+Background / Related Work / Research
Questions (RQ1–RQ4) / Methodology (design, corpus, case representation,
literature retrieval, keyword system, embedding system, llm_only system,
pipeline system, OpenAlex integration, Ollama integration, prompt design,
evidence extraction, evidence categories, storage/aggregation, failure
handling) / Experimental Setup (dataset, cases, models, retrieval config,
LLM config, execution procedure) / Results (overall, per-system, per-case,
evidence-type, coverage, failures) / Discussion (observation vs
interpretation) / Threats to Validity / Reproducibility / Conclusion /
References / Appendix (+ Appendix A–D pointers).

## 2. Number tie-out (verbatim from results.json; read-only)

- 188 EV records: 55 intersection + 50 hypothesis + 83 gap = 188 ✅
- keyword 41 / embedding 36 / llm_only 53 / pipeline 58 = 188 ✅
- coverage 12/12/12/8 (pipeline 8/12) ✅
- generated_utc = 2026-09-23T11:43:34+00:00 ✅
- 4 pipeline failures verbatim: causal_inference_x_clinical_ml (ReadTimeout),
  gnn_x_protein_structure (ReadTimeout), rl_x_sim_to_real (ReadError),
  clinical_nlp_x_ehr (ConnectError) ✅

## 3. Citation wiring (only real keys)

ALL 12 distinct keys cited in .tex EXIST in the .bib; 0 broken keys.
15 real bib entries (verified via OpenAlex/DOI); no fabricated references.

## 4. Figure wiring

ALL 3 includegraphics targets EXIST on disk (fig1_surface_distribution.svg,
fig2_evidence_per_system.svg, fig3_case_coverage_per_system.svg); 0 broken.

## 5. Honest disclosures (none hidden)

1. **LaTeX COMPILATION: NOT performed.** No TeX engine exists on this machine
   (pdflatex/xelatex/lualatex/latexmk/tectonic/bibtex/biber/pandoc probed,
   read-only, all absent). The delivered PDF is an **HTML-rendered preview
   only**, explicitly labeled (filename + AUDIT.md Appendix E + README). It is
   never presented as a LaTeX compilation.
2. **No rerun, no repair, no fabrication.** All numbers/tables/figures derived
   by read-only parsing of results.json; nothing re-executed; 4 failures kept
   verbatim and unrepaired.
3. **No ranking, no quality claim, no human rating layer** (explicit in
   manuscript Section 5 / Discussion).
4. **Coverage caveat**: pipeline totals not comparable (8/12) — explicitly
   stated, no ranking drawn.

## 6. Reproducible rebuild (source complete)

- pdflatex Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.tex
- bibtex   Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation
- pdflatex (x2)
Expect a complete 12-section LaTeX PDF on any TeX-equipped machine.
SVGs require conversion to PDF/PNG (or use svg package + inkscape +
shell-escape) per README.md.

**Bottom line:** manuscript source is complete, faithful, and honest; the
only step not possible here — real LaTeX compilation — is disclosed, never
faked.
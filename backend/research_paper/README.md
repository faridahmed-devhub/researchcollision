# research_paper — Manuscript deliverables for the ResearchCollision evaluation

This directory contains a **single-run, descriptive, artifact-grounded manuscript** describing the
12-case / 4-system empirical evaluation stored in
`backend/evaluation_out_real_llm_v1/results.json`.

## Important scope statements

- **Descriptive only.** Single run, single seed, no variance estimation, no statistical tests,
  no p-values, no error bars, no system ranking, no efficacy or quality claims.
- **No human rating layer.** `results.json` contains no expert/quality annotation; the manuscript
  makes **no claim** about the relevance or correctness of evidence, and says so.
- **Pipeline is incomplete.** The pipeline system only produced evidence for 8 of 12 cases; 4
  pipeline runs failed (all recorded verbatim in Table D and the appendix). Pipeline totals are
  reported but are **explicitly not comparable** to the other systems' coverage, and no
  comparative inference is drawn from them.

## Contents

```
research_paper/
├── paper.md                 # Complete manuscript (Markdown)
├── paper.tex               # LaTeX source (Elsevier-like class, xelatex/pdfLaTeX)
├── references.bib          # Verified references with DOIs (real scholarly records only)
├── AUDIT.md               # Claim-by-claim verification vs results.json
├── README.md              # This file
├── tables/
│   ├── table_a_casexsystem.csv / .md        # 12 cases × 4 systems (I/H/G per cell; FAIL = no pipeline evidence)
│   ├── table_b_system_totals.csv / .md      # keyword 41, embedding 36, llm_only 53, pipeline 58
│   ├── table_c_surface_distribution.csv / .md # intersection 55, hypothesis 50, gap 83
│   └── table_d_pipeline_failures.csv / .md  # 4 verbatim pipeline failures (not hidden)
├── figures/
│   ├── fig1_surface_distribution.svg        # surface distribution (55/50/83)
│   ├── fig2_evidence_per_system.svg         # system totals (41/36/53/58)
│   └── fig3_case_coverage_per_system.svg    # case coverage (12/12/12/8)
└── appendix/
    ├── appendix_a_method_and_config.md      # systems, corpus, parameters, procedure
    ├── appendix_b_failures_verbatim.md      # all 4 pipeline failures, verbatim
    ├── appendix_c_full_evidence_matrix.md   # full 12 × 4 cell matrix (reference to tables/)
    └── appendix_d_reproducibility.md        # how to reproduce/verify (read-only)
```

## Reproducibility (how the numbers were produced)

- Full experiment description is in the repository README and `backend/` code paths
  (`run.py`, `keyword/`, `embedding/`, `llm_only/`, `pipeline/` modules).
- *This manuscript* was generated **without re-running the experiment**; every number in it was
  obtained by a read-only parse of the authoritative `results.json` only.
- To verify any claim, re-run the read-only reconciliation documented in `AUDIT.md`.

## Claim scope (what this paper does NOT assert)

1. It does not rank the four systems.
2. It does not assert statistical significance or generalizability.
3. It does not claim evidence is correct/relevant (no human rating available).
4. It does not hide or repair the 4 pipeline failures; they are reported verbatim and used to
   flag pipeline coverage as 8/12.

---

## Upgrade program (appended 2026-09-25)

This single-run manuscript stays frozen while the reproducible upgrade proceeds
under `UPGRADE_PLAN.md` (audit + 12-phase workflow). Relevant documents:

- `UPGRADE_PLAN.md` — audit findings, evidence inventory, phase plan (Phases 1–12).
- `PREREGISTRATION_DRAFT.md` — drafting template, **status: “Preregistration planned”** (not registered, no DOI).
- `backend/REPRODUCIBILITY.md` — how to reproduce evaluation runs (seed semantics, artifacts, failures policy).
- `backend/EXPERIMENT_PROTOCOL.md` — planned repeated-run protocol for the future manuscript rewrite (Phase 11).

---

## File-naming note (appended 2026-09-24T07:04:27Z)

The four publication deliverables are also provided under the required canonical names as
byte-identical copies of the verified sources listed at the top of this README (no re-run, no
re-compilation, no new numbers):

| Required name | Identical copy of | Notes |
|---|---|---|
| Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.md  | paper.md  | canonical manuscript (Markdown) |
| Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.tex | paper.tex | LaTeX source, compile-ready |
| Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.bib | eferences.bib | bibliography |
| Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.pdf | paper_preview.pdf | **HTML-rendered preview**, NOT a LaTeX compilation (see disclosure in AUDIT.md Appendix C and the PDF itself). TeX toolchain (pdflatex/xelatex/lualatex/latexmk/ibtex/iber/pandoc/wkhtmltopdf/wkhtmltoimage) is **absent** on this machine and is disclosed, not fabricated. |

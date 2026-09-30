# Paper Finalization Report

**Date:** 2026-09-29
**Scope:** Final academic rendering pass of the 12-case, 188-record evidence-surface study in `backend/research_paper`.

---

## 1. Final artifacts

| Artifact | Notes | SHA-256 |
|---|---|---|
| `paper.md` | Final manuscript source (canonical `.md` re-synced byte-identical) | `36C4BBA4773D71F198E5C0E6EA90F3BF0A88DE9AEF71EE19ABBDD307EC27DA26` |
| `research_paper.pdf` | Final rendered PDF (16 pages, 5031 words) | `9D8DC364F90A717604DD41E8877387D78C2EC1340100CFEF9692ABD61BCA5079` |
| `research_paper.html` | Final rendered HTML (same content as PDF) | `2E8F947BB2BCF962F282CBF10A511D9BF5E310A4C519375D8767439F0E88814F` |
| `render_manifest.json` | Register of the 55 QA checks + render metadata | `CD8288C3B77CB67263D4060A567DD34B711B3036B8AFF478585E287E1A4CEFB5` |
| `Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.{md,pdf,html}` | Canonical deliverable copies, re-synced byte-identical to the final artifacts | match the above |
| `qa_pages/`, `_mupdf_pages/` | 16/16 poppler + 16/16 mupdf rasters, regenerated from the final PDF | — |
| `appendix/*.md` | Appendix A, B, C, D sources (rewritten in this pass) | — |

## 2. What was changed in this final pass

- **Renderer (`render_research_paper.py`)**:
  - Master appendices branch fixed from `hid.startswith("Appendix")` to `hid.lower().startswith("appendices")` — the previous condition never matched the "Appendices" heading (spelling "appendices"), so the appendix body was silently dropped and only the intro paragraph rendered. This is the fix that made the four appendices physically appear in the PDF/HTML.
  - References now render with a single numbering scheme. The `<ol>` was wrapped in `<div class="refs">` so `list-style: none` applies; "1. [1]" double numbering is gone; entries show only `[1]`–`[7]`.
  - Author/title block: subtitle rendered only when present; author string split on " | " into separate rows; "Source artifact" row, disclosure box, and render footer removed.
  - Appendix label map: Appendix A: Experimental Configuration, Appendix B: Case-Level Evidence Matrix, Appendix C: Runtime Failures, Appendix D: Reproducibility Information (labels, TOC rows, and main() special rows all updated consistently).
  - `appendix_html()` adds `class="wide-table"` so appendix tables fit the page width.
  - Table D rubric marker + caption; Figure figure-anchor detection; academic References note; `.refkey` hidden.
  - TOC page-field baking now uses `body_start_page()` (page after the "Contents" page) so TOC rows are not mistaken for body headings.
- **Appendix sources**: A = experimental configuration (systems, corpus, execution, surfaces, output summary); B = condensed 12-case x 4-system evidence matrix (derived from `tables/table_a_casexsystem.md`; failed pipeline cells marked "--"); C = the four runtime failures with the byte-exact runtime-reported strings (no "exact bytes" phrasing, no "verbatim"); D = reproducibility and data availability (repository-level; no secrets).
- **Figures**: removed a single audit footnote text node from `figures/fig1_surface_distribution.svg` ("Authoritative: results.json (188 EV records)..."). No geometry, labels, or counts changed.
- **QA harness**: `qa_run.py` anchors updated (single-instance headings, §5.2/§5.3 figure checks, `scan_from` logic overridden to skip the TOC page); `qa_bars.py` now locates figure pages dynamically and rasterizes in-memory with PyMuPDF (no dependency on stale pre-rendered pages).
- **Rasters**: regenerated both `_mupdf_pages/m*.png` (150 dpi) and `qa_pages/page-*.png` (110 dpi) from the final PDF; ink scan confirms no blank page.

## 3. What was not changed

- `results.json`, `failure_analysis.json`, and `tables/table_a_casexsystem.md` were **not modified** — they remain the read-only authoritative sources.
- All counts preserved: 188 records; surfaces 55 / 50 / 83; systems 41 / 36 / 53 / 58; coverage 12 / 12 / 12 / 8; four pipeline runtime failures (case ids causal_inference_x_clinical_ml, gnn_x_protein_structure, rl_x_sim_to_real, clinical_nlp_x_ehr).
- Section ordering of `paper.md` unchanged: Section 6 "Failure Analysis" remains a top-level section per the earlier instructions (runtime-failure content stays there, referenced from §5).
- Research questions, system-design paragraphs, and the mandated title were kept as previously settled.
- The mock-vector embedding baseline remains described as deterministic with **no pretrained embedding model (Sentence-BERT or otherwise)**; no superiority, ranking, or statistical claims were added; generalization is explicitly not claimed.
- No secrets: endpoint, `.env`, keys, and redacted provider details appear nowhere in the final artifacts.

## 4. Final manuscript structure

1. Introduction · 2. Related Work · 3. Research Questions · 4. Methodology (incl. 4.3 Evidence-Surface Taxonomy, 4.6 quality labels) · 5. Results (5.1 corpus overview, 5.2 Evidence-Surface Distribution, Fig. 1; 5.3 System-Level Coverage, Fig. 2/Fig. 3, Table B) · 6. Failure Analysis (the four runtime failures, Table D) · 7. Discussion · 8. Limitations and Threats to Validity · 9. Reproducibility and Data Availability · 10. Conclusion · References · Appendices.

- **References:** 7, all cited in text (`[1]`–`[7]`), single numbering scheme, no duplicates and no uncited entries.
- **Appendices:** 4 (A Experimental Configuration, B Case-Level Evidence Matrix, C Runtime Failures, D Reproducibility Information), each verified to occupy exactly one body page with real content.

## 5. QA results (final render)

- `python qa_run.py` → **55 passed, 0 failed**; `render_manifest.json` regenerated.
- `qa_bars.py` (invoked inside `qa_run`) → PASS; bar proportionality fig1 [55,50,83], fig2 [41,36,53,58], fig3 [12,12,12,8] in SVG and raster.
- Verification battery over the final PDF text: appendix headings present once each with content; all 12 case ids, `ReadTimeout`, `ReadError`, `ConnectError:Allconnectionattemptsfailed` present; counts 188/55/50/83 and 41/36/53/58 present; no "1. [1]" double numbering; no markdown/HTML leakage; **no banned strings** (`results.json`, `.py` filenames, "55/55", "PASS", "Verification Matrix", "exact bytes", "verbatim", source artifact, endpoint `203.96.189.126`/`11434`, `.env`, secrets); no Windows paths.
- Raster ink scan: 16/16 pages carry ink (no blank page).
- Final PDF: 16 pages, 5031 words (>3500 required). TOC page numbers for all sections and the four appendices match the actual page positions.

## 6. Known limitations (unchanged, reported in the manuscript)

- Remote LLM sampling is not guaranteed deterministic; byte-wise reproduction of generated text is not claimed.
- No human raters and no statistical inference; only counts and descriptive summaries.
- Pipeline evidence is intentionally incomplete (8 of 12 cases) because four runs failed at runtime; the failures were not repaired or retried and are reported transparently.
- The embedding baseline is deterministic (no pretrained embedding model); records are API-level artifacts, not validated scholarly claims.
- The 61 analysis-level flagged/discarded records are machine-labeled and are not counted as evidence.
- Programmatic gates all pass; a purely perceptual defect (color/contrast/aesthetic) can still only be caught by human review of `qa_pages/`, which is published next to the PDF.

## 7. Experimental status

**The experiment was NOT re-run.** Every number in the manuscript and appendices is parsed read-only from the recorded evaluation outputs (`evaluation_out_real_llm_v1/results.json`, single seeded execution, timestamp `2026-09-23T11:43:34+00:00`, corpus `real_case_study_v1`) and `failure_analysis.json`. No inference artifacts were regenerated in this pass.

---

**FINAL_MANUSCRIPT_STATUS = HUMAN-WRITING-READY**
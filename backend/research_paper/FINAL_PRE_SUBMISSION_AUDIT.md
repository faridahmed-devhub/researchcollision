# FINAL PRE-SUBMISSION AUDIT

**Audited artifact:** `backend/research_paper/research_paper.pdf` (final render, 16 pages, 5031 words)
**Audit date:** 2026-09-29
**Mode:** Read-only. No experiment, `results.json`, frozen evaluation artifacts, or manuscript content were modified.

---

## STATUS = PASS

| # | Check | Status | Evidence | Action Required |
|---|---|---|---|---|
| 1 | Author block | **PASS** | PDF p1 title page extracts verbatim: "Farid Ahmed", "Independent Researcher", "Dhaka, Bangladesh", "faridahmed.devhub@gmail.com". | None |
| 2 | Title/abstract consistency | **PASS** | Title: "Evidence-Surface Analysis of Multi-System Research-Collision Pipelines: A 12-Case, 188-Record Study". Abstract (p2) states a 12-case, 188-record study of evidence surfaces via four system configurations, explicitly "descriptive", "single seeded execution". No mismatch between title, abstract, and body numbers. | None |
| 3 | All 4 appendices present | **PASS** | Appendix A (p13), Appendix B: Case-Level Evidence Matrix (p14), Appendix C: Runtime Failures (p15), Appendix D: Reproducibility Information (p15); each heading appears exactly once on its body page and is followed by substantive content (no empty appendix sections). | None |
| 4 | TOC page numbers match actual pages | **PASS** | All 19 TOC rows verified: printed TOC number == first body page for Abstract 2, Keywords 2, 1–10 sections (2,3,4,4,6,9,10,10,11,11), References 12, Appendices 12, Appendix A 13, B 14, C 15, D 15. 0 mismatches. | None |
| 5 | Figure/table referential integrity | **PASS** | Captions present: Figure 1 (p7), Figure 2 & 3 (p8); Table A (p14, appendix matrix), Table B (p9), Table C (p7), Table D (p9). Every figure and table referenced in the text also exists; no orphan references. | None |
| 6 | Citations ↔ references | **PASS** | In-text citations are [1]–[7] only; all 7 cited; no citation without an entry and no uncited entry. | None |
| 7 | Reference formatting / no fabricated DOI | **PASS** | 7 entries ([1]–[7]) formatted `Authors (year). Title. Venue. DOI/arXiv id`. DOIs found: `10.1353/pbm.1986.0087` (Swanson 1986), `10.1016/S0004-3702…` (Swanson & Smalheiser 1997), `10.18653/v1/D19-1410` (Sentence-BERT 2019), `10.18653/v1/2020.emnlp-main.550` (DPR 2020), `10.48550/arXiv.2005.11401` (RAG 2020), `10.48550/arXiv.2302.13971` (LLaMA 2023), `10.48550/arXiv.2205.01833` (OpenAlex 2022). All belong to the real cited publications; no `10.0000`–style or placeholder DOIs. | None |
| 8 | No markdown/HTML leakage | **PASS** | PDF text extraction contains no `##`, `**`, `#`, `</`, `<p`, `<table`, HTML entities, or code fences. | None |
| 9 | No paths, keys, tokens, .env, private endpoints | **PASS** | No Windows path patterns, `sk-*`, `api_key`, `.env`, `ollama`, `11434`, `203.96.189.126`, `OPENAI_BASE_URL`, `Bearer`, or any `http(s)://` string in the PDF/PAPER text. | None |
| 10 | No unsupported superiority/statistics claims | **PASS** | Zero hits for: statistical significance/p-value, human evaluation/rating/anotation, outperform, superior, surpass, state-of-the-art, SOTA, best/benchmark/beats/exceeds/leading/win, novel-method trophy claims. Paper explicitly states "no rank order and no quality claim". | None |
| 11 | Mock-vector baseline not presented as a pretrained embedding model | **PASS** | All 8 "mock" occurrences describe a deterministic mock-vector cosine baseline on fixed, reproducible featurization. Explicit negations in text: "does not use pretrained embedding models in its evaluated embedding configuration", "no pretrained embedding model (Sentence-BERT or otherwise)". Sentence-BERT/DPR appear only in Section 2 background and reference entries [3]/[4]. | None |
| 12 | Identified as single-run descriptive case study | **PASS** | Contains "case study", "single seeded execution", "descriptive", "generalization ... not claimed", "no rank order", "no quality claim"; Limitations section states results "may not generalize". | None |
| 13 | Numerical results trace to `results.json` | **PASS** | Re-tallied read-only from `backend/evaluation_out_real_llm_v1/results.json`: surfaces {hypothesis 50, intersection 55, gap 83} = 188; per-system {keyword 41, embedding 36, llm_only 53, pipeline 58}; case coverage {keyword 12, embedding 12, llm_only 12, pipeline 8}; failures = 4 with exact strings `ReadTimeout: `, `ReadTimeout: `, `ReadError: `, `ConnectError: All connection attempts failed`; `failure_analysis` = 61 flagged records. All match the paper/figures/tables byte-for-byte. | None |
| 14 | Experiment not re-run during finalization | **PASS** | `results.json` mtime 2026-09-23T17:43:34Z (run time), unchanged under git (no working-tree modifications); final PDF rendered 2026-09-29. Manuscript states no experiment is re-executed during preparation. | None |
| 15 | PDF text extraction + structural checks | **PASS** | 16 pages, 5031 words; all 18 headings (Abstract … Appendix D) found exactly once in body; no blank page (per-page ink scan, 16/16); appendix TOC anchors resolve to real pages; extraction renders cleanly, no garbage glyphs. | None |

---

## Informational note (no manuscript action)

`backend/evaluation_out_real_llm_v1/report.md` (a separate evaluation-side deliverable) contains one boilerplate Limitations line — "Language-model steps used the deterministic mock LLM provider" — that contradicts `results.json` `config.providers.llm_provider = "openai_compatible"` (offline_mode `false`). The manuscript's wording ("OpenAI-compatible endpoint", non-deterministic sampling caveat) is consistent with `results.json`; the contradiction lives inside `report.md` itself. Recommend the author reconcile that single line in `report.md` before sharing the evaluation package. This does not affect the manuscript and is flagged purely for transparency.

## Scope statement

This audit certifies the manuscript as internally consistent, accurate against its recorded evaluation outputs, and free of the listed unsupported claims, secrets, and leakage. No claim of peer-review acceptance or publication readiness is made.

**MANUSCRIPT IS READY FOR EXTERNAL SUBMISSION AS A DESCRIPTIVE EMPIRICAL CASE STUDY.**
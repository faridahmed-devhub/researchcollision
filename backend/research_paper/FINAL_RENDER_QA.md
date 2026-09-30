# FINAL RENDER QA - 12-case / 188-evidence-study paper (post-correction)

- Generated UTC: `2026-09-29T00:00:00+00:00` (regenerated after manuscript correction)
- Artifacts: `research_paper.html` (55,002 bytes), `research_paper.pdf` (16 pages, 640,323 bytes)
- Correction source: `PAPER_CONTENT_AUDIT.md` (12 prioritized problems) -> `PAPER_CORRECTION_REPORT.md`

## Programmatic QA gate

- qa_run.py: **55 passed, 0 failed** (veto gate for RENDER COMPLETE)
- qa_bars.py (SVG + raster proportionality, exit 0): PASS — fig1 [55,50,83], fig2 [41,36,53,58], fig3 [12,12,12,8]
- Footer "Page N of M" extractable on every page: PASS
- All fonts embedded (no base-14 / base-35 fallback): PASS
- TOC: 18 rows, no duplicate labels, all page numbers match actual heading pages
- Figures: Fig1 on the §4.1 page, Fig2/Fig3 on the §4.2 page
- Blank pages: none
- Markdown/HTML leakage scan (PDF text and HTML body): zero hits for
  `<div class="table-caption">`, `## `, `# Appendix`, `**`, `*not*`
- Forbidden/contradicted claim strings in the final rendered text: none
  ("Sentence-BERT" and "Ollama" appear ONLY as intentional background/negative references:
  the cited Sentence-BERT paper title and the "not Ollama" disclosure)

## Corrections verified in this render

1. System descriptions: `embedding` = mock-vector cosine baseline (`MockEmbeddingProvider`),
   no pretrained embeddings; `keyword` = token-overlap lexical baseline (no BM25 claim).
2. Reproducibility: "single seeded run (seed 0, configured/default); remote LLM sampling not
   guaranteed deterministic" (no "deterministic run" claim).
3. LLM provider: `openai_compatible` endpoint, identity redacted (no "self-hosted Ollama" claim).
4. 61 analysis-level flags disclosed (§3.6) with by_type/by_stage/by_system breakdowns.
5. Automatic metrics disclosed as machine diagnostics, not human judgments
   (`human.provided = false`).
6. Failure table: exact bytes (`ReadTimeout: ` / `ReadError: ` with trailing space) verified in
   the HTML `<code>` spans; PDF body states their byte-exactness.
7. References: rendered list pruned to the 7 genuinely-cited entries; Kaiser diacritic bug fixed
   (no more "Kaiser, \.,").
8. Numbers preserved verbatim: 188; 55/50/83; 41/36/53/58; 12/12/12/8; 4 failures.

## Honest status

RENDER COMPLETE - HTML AND PDF VERIFIED is claimed **only** in the sense of the programmatic QA
gate. True pixel-level human inspection is NOT claimed: this model cannot view images (every
raster read returns a file this model cannot visually interpret). All numeric, geometric,
textual, figure-integrity and font-level checks pass; the raster previews (`qa_pages/`,
`_mupdf_pages/`, `_diff_iso/`) are published beside the PDF for manual eyeball review.
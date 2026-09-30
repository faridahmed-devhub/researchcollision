# Visual QA Report — research_paper.pdf

- Generated UTC: `2026-09-29T04:55:18+00:00`
- Method: programmatic pixel/geometry/ink/font checks per page (rasters in `qa_pages/`, `_mupdf_pages/`).
- **Limitation:** true human pixel inspection is NOT performed; see note below.

## Per-page checks

| Page | Result | Spans | Ink ratio | Notes |
|---|---|---|---|---|
| 1 | PASS | 50 | 0.0583 | ok |
| 2 | PASS | 103 | 0.0879 | ok |
| 3 | PASS | 59 | 0.0614 | ok |
| 4 | PASS | 73 | 0.0529 | ok |
| 5 | PASS | 33 | 0.0998 | ok |
| 6 | PASS | 40 | 0.1354 | ok |
| 7 | PASS | 76 | 0.0743 | ok |
| 8 | PASS | 81 | 0.0752 | ok |
| 9 | PASS | 83 | 0.0715 | ok |
| 10 | PASS | 57 | 0.0927 | ok |
| 11 | PASS | 184 | 0.0764 | ok |
| 12 | PASS | 151 | 0.0705 | ok |
| 13 | PASS | 88 | 0.0688 | ok |
| 14 | PASS | 75 | 0.0654 | ok |
| 15 | PASS | 21 | 0.016 | ok |

## Cross-page checks

- Page size: A4 (`page width 595.0pt`, height 841.9pt`)
- Margins respected on every page (no text past L51.0/R544.0): PASS
- Footers `Page N of 15` on every page (searchable text): PASS
- All fonts embedded (no base-14 fallback): PASS
- Bar proportionality (SVG source + raster): PASS
- Blank pages: PASS (none)

## Verdict

- Programmatic visual QA: **PASS**

## Honest limitation

This environment's QA is **programmatic**: it verifies geometry, ink coverage, glyph rendering, font embedding, figure proportionality, table fit and footer presence per page. It does **not** include a human (or vision-capable model) eyeball inspection of the rendered pages. If a purely perceptual defect exists (e.g. subtle color/contrast or aesthetic issues that pass all numeric thresholds), it will not be caught here. Raster previews are in `qa_pages/` for manual review.

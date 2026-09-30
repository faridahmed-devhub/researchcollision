# PAPER CORRECTION REPORT — ResearchCollision manuscript and rendering pipeline

- Date: 2026-09-29
- Basis: `backend/research_paper/PAPER_CONTENT_AUDIT.md` (12-item prioritized problem list) — the authoritative correction list.
- Scope: `paper.md`, `render_research_paper.py`, appendix files, canonical bibliography, `evaluation/report.py`, `qa_run.py`.
- Guardrails honored (UNCHANGED): authoritative `backend/evaluation_out_real_llm_v1/results.json`,
  `failure_analysis.json`, dataset files, figures' underlying data, historical/frozen docs
  (`AUDIT.md`, `FINAL_AUDIT.md`, `Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.md`,
  `MANUSCRIPT_GAP_AUDIT.md`, `caching_paper_deliverable_20260926/`, legacy `references.bib`,
  historical `report.md`). No experiment was re-run; **no** numerical result was invented,
  edited, or re-derived in a way that altered `results.json`.

---

## 1. Priority resolution summary

| P# | Problem (audit) | Status | Evidence |
|---|---|---|---|
| P1 | `embedding` described as Sentence-BERT dense retrieval; `keyword` as BM25 | FIXED | §2/§3.2/appendix A rewritten; QA grep: no "SBERT"/"BM25" in rendered text |
| P2 | "one deterministic run, seed 0" overclaim | FIXED | seed wording corrected in Abstract/§1/§3.2/§8/appendix A/D |
| P3 | 61 analysis-level records omitted | FIXED | new §3.6 with by_type/by_stage/by_system tables |
| P4 | automatic metrics vs human ratings conflated | FIXED | §3.6 "Automatic (machine) metrics vs. human evaluation"; `human.provided=false` disclosed |
| P5 | "real Ollama"/"self-hosted Ollama" + report.py unconditional mock-LMM disclaimer | FIXED | provider wording everywhere = `openai_compatible`, redacted; report.py disclosure now conditional |
| P6 | literal markdown/HTML leakage (`<div class="table-caption">`, `##`, `#`, `**`, `*`) | FIXED | renderer rewritten (headings, list continuation, inline emphasis, caption sentinels); QA zero leaks |
| P7 | duplicate "Appendix A", stale `appendix_a_evidence_matrix.md` pointer | FIXED | master appendix renamed; pointers fixed; single A/B/C/D hierarchy; TOC unique |
| P8 | "Kaiser, \.," artifact; uncited refs in rendered bibliography | FIXED | `_plain` brace-order bug fixed; rendered refs pruned to 7 cited keys |
| P9 | typo/prose errors | FIXED | all 5 flagged typos corrected (below) |
| P10 | failure table "verbatim" cells trimmed | FIXED | exact byte strings (trailing colon+space) now rendered; HTML `<code>` verified byte-exact |
| P11 | numeric integrity | PRESERVED | qa_bars PASS; read-only tally = 188/55/50/83/41/36/53/58/12/12/12/8 (see §3) |
| P12 | regenerate artifacts + QA reports | DONE | research_paper.html/.pdf, render_manifest.json, html/pdf_qa_report.md, FINAL_RENDER_QA.md, refreshed audit |

---

## 2. Issue-by-issue corrections

Columns: **Issue — Old wording → Corrected wording — Source evidence — Files changed — Verification**.

### 2.1 P1 — System descriptions

| # | Item | Old wording | Corrected wording | Evidence |
|---|---|---|---|---|
| 1 | `embedding` system | "dense embedding similarity (sentence-transformers, Sentence-BERT family)" | "deterministic mock-vector cosine-similarity baseline using `MockEmbeddingProvider`; **no pretrained embedding checkpoint was used in this run**" | `baselines.py:255-257` instantiates `MockEmbeddingProvider`; `results.json` `config.providers.embedding_provider = "mock"`; `results.json:142` |
| 2 | `keyword` system | "lexical (keyword/BM25-style) matching" | "token-overlap lexical baseline: ranks corpus papers by overlap between researcher topics/methods and paper metadata" | `baselines.py:164` hand-rolled token-overlap scorer (not BM25) |
| 3 | §2 Related Work | claimed Sentence-BERT/DPR as the embedding implementation | kept citations **as background only**; explicit "**Background only:** the evaluation's `embedding` system does *not* implement this" | rendered PDF text search: "SBERT"/"BM25" absent; "Sentence-BERT" only in background sentence + reference title |
| 4 | `references.bib`/`sbert`/`ollama` in rendered list | rendered 15 entries incl. uncited software | rendered list = 7 genuinely-cited entries; uncited entries remain in the canonical `.bib` (provenance) but are excluded | `render_research_paper.py` `CITED_KEYS`; QA "Rendered refs are only the cited subset" PASS |

Files changed: `paper.md` (§2, §3.2), `appendix/appendix_a_method_and_config.md`, `render_research_paper.py`.

### 2.2 P2 — Reproducibility

| # | Item | Old wording | Corrected wording | Evidence |
|---|---|---|---|---|
| 1 | Abstract | "one experiment, one run, seed `0`, real Ollama (remote, OpenAI-compatible)" | "one experiment, one run, single seeded run using seed `0` as the configured/default seed; remote LLM sampling was **not** guaranteed deterministic … LLM provider recorded as `openai_compatible` (endpoint/model identity redacted)" | `results.json` has no seed field; runner default seed 0; `REPRODUCIBILITY.md` "if endpoint supports deterministic sampling — not guaranteed" |
| 2 | §1 | "on one deterministic run" | "on one seeded run (seed `0`, the configured/default seed; remote LLM sampling was not guaranteed deterministic)" | same |
| 3 | appendix D | "real rank/embedding/LLM calls" ; validation "deterministic" | clarifies mock-vector embedding; adds "remote LLM sampling is not guaranteed deterministic, so exact byte-wise reproduction is not claimed" | `appendix_d_reproducibility.md` |

Files changed: `paper.md`, `appendix/appendix_d_reproducibility.md`.

### 2.3 P3 + P4 — 61 analysis-level flags; automatic metrics vs human ratings

- New §3.6 "Transparency: analysis-level flags and automatic metrics" added to `paper.md`:
  - 61 flags table: `intersection_without_evidence` 23, `ungrounded_hypothesis` 18, `gap_without_evidence` 15, `system_error` 4, `no_expected_topic_covered` 1 (total 61).
  - By stage: `reasoning` 19, `retrieval` 38, `generation` 4. By system: `llm_only` 53, `pipeline` 7, `embedding` 1.
  - Explicit statement that these are analysis-level classifications of output items, NOT additional runtime failures, and that they do not alter the 188-record counts.
  - `**Automatic (machine) metrics vs. human evaluation.**` — metric names listed; `human.provided = false`; grounding-precision example values 0.222/0.194/0.021 disclosed as diagnostics, "**not equivalent to, and not a substitute for, human expert quality judgments**".
  - §8 limitation #2 and #7 reworded accordingly.
- Evidence (read-only): `results.json` `failure_summary` = `{"total": 61, "by_stage": {reasoning:19, retrieval:38, generation:4}, "by_type": {ungrounded_hypothesis:18, gap_without_evidence:15, intersection_without_evidence:23, system_error:4, no_expected_topic_covered:1}, "by_system": {llm_only:53, pipeline:7, embedding:1}}`; `failure_analysis.json` (61 items); `human.provided=false`, `ratings_count=0`.
- Files changed: `paper.md`, (linter) `appendix_c_full_evidence_matrix.md` (unchanged content).

### 2.4 P5 — LLM provider wording + `report.py`

| # | Item | Old wording | Corrected wording | Evidence |
|---|---|---|---|---|
| 1 | §3.2 | "All LLM calls go to a real, self-hosted **Ollama** instance exposed through an OpenAI-compatible endpoint" | "All LLM calls in this run went to an OpenAI-compatible LLM provider (recorded in `results.json` config as `llm_provider = openai_compatible`); the endpoint and model identity are intentionally redacted here because no artifact persists them" | `results.json` `config.providers.llm_provider = "openai_compatible"` |
| 2 | Abstract | "real Ollama (remote, OpenAI-compatible) as the LLM provider" | "LLM provider is recorded as `openai_compatible` (endpoint/model identity redacted)" | same |
| 3 | §9 config | "`backend/.env` (Ollama base URL …)" | "`llm_provider = openai_compatible` (endpoint/model identity redacted), `embedding_provider = mock`, `literature_chain = [openalex, semantic_scholar, crossref, arxiv]`, `offline_mode = false`, seed `0` (configured/default), single run, stop-on-failure" | `results.json` `config.providers` + `config.offline_mode=false`; `generated_utc` |
| 4 | appendix A | "real LLM: Ollama (local, real LLM) via OpenAI-compatible endpoint" | "LLM provider recorded in `results.json` as `openai_compatible` (endpoint/model identity redacted; not Ollama, not a mock LLM for this artifact)" | same |
| 5 | `report.py` | unconditional "Language-model steps used the deterministic mock LLM provider (no model API credentials were configured for this run)" for real datasets | provider-aware: offline/mock → mock sentence; real recorded provider → "`Language-model steps used the configured real LLM provider (`{llm_provider}`; endpoint and model identity are not persisted in this report and are redacted). Remote model sampling was not guaranteed deterministic…" | `report.py` `_limitations(dataset, offline_mode(), llm_provider=…)`; historical `report.md` NOT regenerated |

Files changed: `paper.md`, `appendix/appendix_a_method_and_config.md`, `backend/evaluation/report.py`.

### 2.5 P6 — Markdown/HTML leakage (renderer)

Renderer (`render_research_paper.py`) fixes — each with an in-pipeline reason and a source example:

| # | Issue (old) | Root cause | Fix | Verification |
|---|---|---|---|---|
| 1 | `<div class="table-caption">` leaked verbatim into body (pp.5-7) | `insert_captions` injected raw `<div>` into markdown; `esc()` then escaped it | insert captions as `@@CAPTIONn@@` sentinels; after `md_block`, swap `<p>@@CAPTIONn@@</p>` for the real caption div | QA + grep: `"<div class=\"table-caption\">" not in html/full` PASS |
| 2 | `## A.1 Systems` / `# Appendix …` leaked (pp.12-14) | `appendix_html` used `re.sub(r"^#.*\n?$", …)` without `re.MULTILINE`, and `md_block` had no heading support | `md_block` now emits real `<h1>…<h4>` with ids; appendix files' own H1 is dropped, `## A.x` live rendered as headings | QA: `"## "` / `"# Appendix"` absent; appendix_html assert PASS |
| 3 | `**…**` spanning two lines leaked (p.4) | list items inline-processed per line, then joined | join raw item lines FIRST, then apply `md_inline(esc(...))` once | QA: `"**" not in full` PASS |
| 4 | `*not*` leaked (p.5) | `_INLINE` lacked single-`*` handling | added `\*[^*]+\*` → `<em>` | QA: `"*not*" not in full` PASS |
| 5 | wrapped list continuation became separate paragraphs (so 3.5's bold split leaked) | `md_block` only consumed consecutive lines starting with `- ` | bullets/ordered items now absorb non-starter continuation lines | unit tests + QA PASS |
| 6 | numbered list only detected when block ended in `**` | brittle heuristic | numbered-list branch rewritten generically (any `^\d+\.\s` block, wrap-absorbing) | §8/§3.5 render correctly; QA PASS |

Files changed: `render_research_paper.py`. Verification: unit test script (`test_renderer.py`, all asserts PASS), `qa_run.py` 55/55, PDF-text + HTML-body leak grep = zero hits.

### 2.6 P7 — Appendix structure

- Master appendix heading: `## Appendix A — Full 12×4 evidence matrix` → `## Appendix — Evidence Matrix and Supplemental Materials` (removes duplicate "Appendix A" in TOC: master + supplemental A were both "Appendix A").
- Supplemental appendices keep unique labels A–D; Appendix B renamed "Pipeline Failures (exact bytes)".
- Stale pointer `appendix/appendix_a_evidence_matrix.md` (nonexistent file) replaced with the real supplemental files list.
- Files changed: `paper.md`, `render_research_paper.py` (labels/slugs), `appendix/appendix_b_failures_verbatim.md`. QA: TOC 18 rows no duplicates; single-instance heading check PASS.

### 2.7 P8 — Bibliography

| # | Issue | Fix | Verification |
|---|---|---|---|
| 1 | "Kaiser, \.," in reference 6 | `_plain` stripped `}` BEFORE applying the diacritics map, so `{\L}` → literal `\L`. Reordered: diacritics first, then brace/escape removal. `_plain("Kaiser, {\\L}ukasz")` now returns "Kaiser, Lukasz"; author initials "L.". Also de-accents `O{\u{g}}uz`→Oguz, `Ag{\"u}era`→Aguera. | unit test PASS; rendered ref list shows no backslash initials |
| 2 | rendered bibliography included uncited entries (ollama, sbert, vaswani, devlin, mcmahan, kipf, jumper, settles) | rendered list = `CITED_KEYS` (7 genuinely cited refs) only; canonical `.bib` keeps all 15 for provenance; legacy `references.bib` untouched | QA: "bib key: ollama"/"sbert" absent from HTML; rendered = cited subset PASS; `[1]..[7]` markers present |
| 3 | paper.md pointed to legacy `references.bib` | References section now names `Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.bib` as the canonical render source; legacy `references.bib` labeled as retained-for-provenance | `paper.md` References section; renderer note count dynamic (`len(CITED_KEYS)`) |

Files changed: `render_research_paper.py`, `paper.md`. Bib files: unchanged (canonical keeps 15; legacy kept).

### 2.8 P9 — Typo / prose fixes

| # | Old | New | Location |
|---|---|---|---|
| 1 | "An 12-Case, 188-Record" | "A 12-Case, 188-Record" | frontmatter title + H1 |
| 2 | "never brought together in print Ringnet." | "never brought together in print." | §1 |
| 3 | "No non-pipeline failure was recorded capitalize." | "No non-pipeline failure was recorded." | §3.4 |
| 4 | "not quality judgmentsfavored." | "not quality judgments." | §5 |
| 5 | "the authoritative file ticket." | "the authoritative `results.json`." | §9 |
| 6 | "verbatim-recorded runtime failures" | "byte-exact-recorded runtime failures" | §7 / Conclusion |

Verification: grep of `paper.md` for "Ringnet", "capitalize", "judgmentsfavored", "file ticket", "12-Case,-" (title) → zero.

### 2.9 P10 — Failure table byte-exactness

- §6 table + appendix B + abstract table now carry the exact raw bytes: `` `ReadTimeout: ` `` (2×), `` `ReadError: ` ``, `` `ConnectError: All connection attempts failed` ``. The trailing colon+space is preserved and noted in the body.
- Header wording changed from "error (verbatim from results.json)" to "error (exact bytes from results.json)".
- `tables/table_d_pipeline_failures.md` updated to the same exact strings.
- Verification: HTML contains `<code>ReadTimeout: </code>` (exact) — QA byte-exact checks PASS. PDF text extraction drops trailing cell whitespace (lossy layout), so byte-exactness is asserted against the HTML render source (the visible PDF shows "ReadTimeout:" which is the same content, trailing space being invisible).

### 2.10 P11 — Numeric integrity (no changes, re-verified)

Read-only verification against `results.json`:
- 188 `EV-*` record keys present in `results.json` (exact JSON string keys `"EV-…"` = 188).
- Surfaces: intersection 55 / hypothesis 50 / gap 83 (matches §4.1, Table C, Fig 1, `aggregates`).
- Systems: keyword 41 / embedding 36 / llm_only 53 / pipeline 58 (matches §4.2/Table B/Fig 2; note pipeline 58 across 8 cases).
- Coverage: keyword 12, embedding 12, llm_only 12, pipeline 8 (Fig 3; 12/12/12/8).
- Failures: 4, all pipeline, raw bytes as §6.
- Automatic-metric means recomputed from `aggregates` (e.g., keyword grounding 0.2222, embedding 0.1944, pipeline 0.0208 — as quoted in §3.6).
- `qa_bars.py` PASS (SVG + raster proportionality); no figure SVG was regenerated.

### 2.11 P12 — Regenerated artifacts + QA reports

- `research_paper.html` (55,002 bytes) and `research_paper.pdf` (16 pages, 640,323 bytes) regenerated via `render_research_paper.py` (Edge headless).
- `render_manifest.json`, `html_qa_report.md`, `pdf_qa_report.md` regenerated by `qa_run.py` — **55 passed, 0 failed**.
- `bar_proportionality_qa.json` regenerated by `qa_bars.py` (exit 0).
- `FINAL_RENDER_QA.md` regenerated (above).
- `PAPER_CONTENT_AUDIT.md` refreshed with this correction-status section.
- PDF-text + HTML-body scans: leaked-syntax strings and forbidden/contradicted claims ("deterministic run", "self-hosted Ollama", "BM25", "SBERT") → zero; "Sentence-BERT"/"Ollama" appear only as the intentional background/negative references noted in §2.1.3/§2.4.4.

---

## 3. Verification commands used (read-only where required)

```
python render_research_paper.py          # pass1 + pass2 -> research_paper.{html,pdf}
python qa_run.py                         # 55 passed, 0 failed
python qa_bars.py                        # PASS (SVG + raster, exit 0)
# counts re-tallied from results.json (see P11)
# leak/claim grep on extracted PDF text and HTML body: zero unintended hits
```

## 4. Final rule applied

Accuracy of the scientific description was prioritized over presentation: the paper now states a
single seeded run with non-guaranteed-deterministic remote LLM sampling, discloses the mock
embedding baseline and redacted OpenAI-compatible provider, discloses the 61 analysis flags and
automatic-metric diagnostics, and reports the byte-exact failure strings. No claim of
"publication ready" is made here without verification: the repository's QA gate (55 checks +
bar proportionality) passes, but the audit's scientific caveats (single run, no human ratings,
incomplete pipeline coverage) remain in the manuscript as deliberate, non-negotiable disclosures.
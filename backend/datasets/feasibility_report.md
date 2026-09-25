# Feasibility Audit — v2 Corpus Access (protocol §3K)

Date: 2026-09-25 · Phase 3 (dataset build, not system evaluation).

Goal: verify that each required corpus can support the sampling design before
final selection. Per protocol §3K these probes do not constitute evaluation of
any discovery system.

## Findings

### OpenAlex (required — screening + every case build)
- **Earlier probes (same day, earlier hours):** search API functional; occasional
  429 throttling under concurrency; results contain usable abstracts.
- **Current status:** **BLOCKED at IP level.** A single polite-pool request
  (`?search=...&per-page=3&mailto=buildbyfarid@gmail.com`) returns
  `429 Too Many Requests` with:
  - `x-ratelimit-remaining: 0`
  - `retry-after: 68600` (~19 h)
- **Cause:** cumulative probe + screening volume from this network today
  exceeded OpenAlex's rate limit for the IP; the 429 window is a hard
  cooldown rather than a per-request transient.
- **Implication:** the final v2 build cannot be run from this network until the
  limit resets. Screening was paused; `candidate_population.json` was not
  (re)written this session.
- **Mitigations implemented (code):** `_OpenAlexWithRetry` now raises instead of
  returning `[]` on persistent failure (no more silent `0/0` corruption), and
  screening concurrency was reduced (`OPENALEX_CONCURRENCY=2`,
  `OPENALEX_MIN_DELAY=0.35`, attempts=4, backoff 3/9/27 s). Re-run the build
  from a network/IP with a fresh limit, or after cooldown.

### PubMed / NCBI E-utilities (required when a side is `biomed`)
- Functional throughout; throttled to `MIN_INTERVAL=0.35` s (≥3 req/s without
  an API key).
- `esearch`+`efetch` (JSON + XML) verified via live probe:
  `count=392` for a graph-neural-networks × protein-structure query; abstract
  and DOI parse correctly.
- No key configured (`ncbi_email=""`); self-throttling applied. No 429/block
  observed.

### arXiv (best-effort, never blocking — protocol §3)
- **Unreliable this session:** repeated `429 Too Many Requests` and timeouts
  from `export.arxiv.org`. Occasionally a request succeeds.
- The build pre-probes arXiv and records `arxiv_probe_ok`; on failure all arXiv
  work is skipped and documented in the manifest + dataset card (no build
  failure). This is the designed behavior, not a change to the protocol.

## Conclusion for sampling design
- Stratified seeded sampling is corpus-independent (pool/seed/frame are fully
  deterministic) — the design can proceed.
- OpenAlex is the **single point of failure** for the live pull. Wait for the
  IP rate-limit to reset (or use a different network), then run
  `python -m evaluation.datav2.build --root datasets/v2`.
- If OpenAlex remains unavailable longer than the schedule allows, options
  before any protocol change: (a) wait for cooldown, (b) run from a different
  IP/email, (c) *then* consider a protocol amendment (explicit approval
  required) — the frozen protocol §3K makes the current choice to document +
  pause the correct one.

## Evidence (verbatim)
```
GET https://api.openalex.org/works?search=test&per-page=1  (user-agent includes mailto)
HTTP/1.1 429
x-ratelimit-remaining: 0
retry-after: 68600
```
PubMed probe: esearch JSON `{"esearchresult":{"count":"392","idlist":[...]}}`.
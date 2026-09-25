# CASE_SAMPLING_PROTOCOL.md — v2 Benchmark Dataset Sampling Protocol

**Status: FROZEN** (Phase 3A, 2026-09-25). This protocol is frozen BEFORE final
case selection. The v2 dataset and all sampling artifacts must be reproducible
from this protocol, the versioned domain pool, the fixed sampling seed, and the
live scholarly-corpus responses snapshotted in `candidate_population.json`.
The v1 pilot dataset (12 cases) is preserved unchanged and is never merged with
v2.

Version of this protocol: `v1.0.0`. Content hash is recorded in
`datasets/v2/sampling_manifest.json` (`protocol_sha256`).

---

## 1. Target population / corpus

The target population is the **published research literature indexed by three
scholarly corpora**, used as evidence sources for cross-disciplinary research
pairings:

| Corpus | Role | API | Access |
|---|---|---|---|
| OpenAlex | primary (required for every case) | `api.openalex.org/works` | public, polite pool via `mailto` identifier |
| PubMed (MEDLINE) | required where a case involves a life/health domain | NCBI E-utilities `esearch`+`efetch` | public, rate-limited (3 req/s without API key) |
| arXiv | best-effort secondary (record availability only; never blocks) | `export.arxiv.org/api/query` | public; observed transient 429 / timeouts |

Corpus applicability is determined by domain flags in the frozen domain pool
(`domain_pool_v1.json`): `biomed=True` ⇒ PubMed applicable; all domains are
OpenAlex-applicable. arXiv is attempted for every domain and its availability
is recorded (`corpus_access.json`); a transient arXiv outage does not exclude a
candidate (documented feasibility limitation), it only reduces arXiv coverage
for that case, which is reported in the dataset card.

## 2. Unit of analysis

A **research-pairing case**: an ordered pair of research domains `(A, B)`, each
represented by (i) a researcher persona (domain label + derived topics), and
(ii) one frozen search query per domain. The evaluated unit is the pairing —
what evidence-grounded gaps, hypotheses, and intersections a discovery system
finds at the boundary of A and B.

## 3. Case definition

A v2 case is the tuple `(case_id, domain_a, query_a, domain_b, query_b,
field_query, evaluation_question)` plus the per-side source-paper corpora
retrieved at build time. A case is **included** in the final dataset only if it
passes the eligibility criteria in §7 and is selected by the randomization in
§9. Case IDs follow `v2_<slug_a>_<slug_b>` (§11).

## 4. Inclusion criteria

A candidate pairing may be included only when **both** sides are evidence-rich:

- IN1 — Both `query_a` and `query_b` return at least **4 usable records** from
  OpenAlex during eligibility screening (§7), where a usable record is a work
  with a resolvable identifier (DOI or provider id) and a non-empty abstract.
- IN2 — The pairing belongs to the frozen candidate frame (§6) and passes the
  eligibility screen with reason `eligible`.

## 5. Exclusion criteria

- EX1 — Either side returns fewer than 4 usable records in screening (recorded
  as `insufficient_evidence_side_a` / `insufficient_evidence_side_b`).
- EX2 — Resolution failures under the retry policy (§8) leave a side with no
  usable records (recorded as `provider_unavailable` with the verbatim error).
- EX3 — The pairing is a duplicate of another candidate already in the frame
  (deterministic, see §6) — excluded at frame construction, not at build time.
- EX4 — Corpus-retrieval deduplication (§10) removes the *record*, never the
  case; a case is only excluded by EX1/EX2.

Selection is otherwise **independent of any system's evaluation outputs** (§15).

## 6. Sampling frame

The frame is built deterministically from the frozen domain pool:

1. **Domain pool** `eval/datav2/domain_pool_v1.json` — a fixed, versioned table
   of 30 research domains across 4 discipline strata (`life_health`,
   `physical_eng`, `cs_ai`, `quant_methods`); each domain has `id`, `name`,
   `discipline`, `query`, and `biomed` flag. Content hash pinned in the manifest.
2. **Pairing universe** U = all unordered pairs within and across these strata
   (`intra<d>` pairs within each discipline; `inter<c1,c2>` pairs between every
   pair of disciplines). No pair is hand-chosen at this stage.
3. **Candidate frame** F = a seeded, stratified random draw of `N_FRAME = 96`
   pairs from U (allocation, §9): half the candidates are inter-disciplinary,
   half intra-disciplinary, allocated proportionally per strata combination.
   F is written to `candidate_frame.json` and is the exhaustive list that goes
   to eligibility screening. F is reproducible from the pool + seed alone.

## 7. Eligibility screening

For every candidate in F, run screening queries `query_a` and `query_b` against
OpenAlex (limit 10 per query, one call per side; retry policy §8). Count usable
records per side. Decide each candidate: `eligible` (IN1) or `excluded` (EX1),
or `excluded_provider` (EX2, if a side could not be screened). The full
screening record — per-side usable counts, sample provider ids, decision,
reason — is written to `candidate_population.json`, which **is** the recorded
candidate population from which the final sample is drawn.

## 8. Network / retry policy (dataset construction)

- Every OpenAlex call: up to 3 attempts on HTTP 429/5xx/connect/read failures,
  exponential backoff (1 s, 2 s, 4 s) with ±20 % jitter, and a small per-call
  delay (≥0.15 s) plus concurrency ≤3 to respect the polite pool.
- PubMed: provider self-throttles to ≥0.35 s between calls (NCBI guideline);
  retried once on transient failure.
- arXiv: best-effort, bounded to 2 attempts with 20 s read timeout; transient
  429/timeout failures are recorded verbatim and never block a candidate.
- Timeouts/failures are logged and stored; a failure is **never** converted into
  success or substituted with synthetic data.

## 9. Randomization procedure (+ sampling seed)

- **Sampling seed:** `20260925` (fixed integer, recorded everywhere).
- Step 1 — frame allocation (deterministic): partition U into 7 strata groups
  (4 intra×discipline, 3 minus symmetry for the 6 inter discipline-pairs → the
  intra groups and the inter pairs-of-discipline groups). Size-N_FRAME
  proportional allocation per group using `random.Random(seed).sample`.
- Step 2 — final sample (deterministic): from the eligible subset of F, apply a
  second seeded draw of size `N_TARGET = 60` with proportional allocation per
  strata group (rounding via largest remainder); reserve candidates sorted
  deterministically are used only if a group yields fewer eligible than its
  allocation (stopping rule §13).
- Seed applied exclusively through `random.Random(seed)`; no unseeded RNG is
  used anywhere in sampling. Recorded in the manifest: seed, universe size,
  frame size, number excluded (per reason), number selected, number retained
  after dedup, final dataset size.

## 10. Deduplication rules (deterministic, audit-logged)

Matchers are applied in priority order within and across corpus sources for a
given case side; a record is a duplicate and is dropped if it matches an already
kept record at any level:

1. **DOI** (case-insensitive, normalized).
2. **Normalized title + year** — title normalized to lowercase alphanumerics
   (`[^a-z0-9]+` removed); equal normalized title and equal publication year.
3. **Authoritative corpus identifier** — same provider id (OpenAlex `W…`,
   PubMed PMID, arXiv id) from the same corpus.
4. **Documented fallback** — same normalized title only, with a warning flag in
   the audit; such drops are reported separately so "look similar" merges are
   visible and never silently applied. Fallback merges require the titles to be
   identical after normalization (no fuzzy similarity).

Same-DOI records from different corpora keep the **OpenAlex record** as the
surviving copy (richest citation metadata); the dropped record's corpus and id
are recorded in `dedup_audit.json`. Cross-corpus equality is never asserted for
records that merely share a salient title; only DOI/normalized-title+year rules
apply. `dedup_audit.json` records every kept vs dropped decision with matcher id.

## 11. Case identifiers (v2 convention)

- New IDs: `v2_<slug_a>_<slug_b>`, where `<slug>` is the domain-pool `id`
  (ASCII, lower-case, underscore-separated). Unique by construction while all
  pair slugs differ; the validator asserts global uniqueness.
- No stale/fabricated identifiers are reused.
- v1 preservation: the authoritative 12 v1 case ids are kept byte-identical in
  `datasets/v1/` (read-only snapshot + manifest pinning sha256). v2 never uses
  those ids.
- Mapping `datasets/v1/v1_to_v2_mapping.json`: for each of the 12 v1 cases, the
  v2 counterpart **if** the identical domain pairing was elected by sampling
  (`v2_<slug_a>_<slug_b>`), else `"not_resampled"` (v1 retained as pilot,
  unchanged). v1 pairs are never force-included (§15).

## 12. Citation-gap criteria

A case-side is considered adequately covered if its corpus records come from
≥2 distinct sources (records/papers); selection does not depend on citation
counts. Citation counts are recorded per record (OpenAlex) or `0`/absent
(PubMed/arXiv) and are **not** a selection criterion. The "citation-gap" of the
pilot framework is an *output* of system evaluation, not an input to sampling;
it is therefore outside this protocol's scope (recorded as such).

## 13. Minimum evidence + stopping rule

- Minimum evidence per included case: ≥4 usable records on side A and ≥4 on
  side B **in screening**; the built case additionally retains ≥3 unique
  records per side after deduplication (else the case is failed loudly at build
  time and excluded, recorded in the manifest as `dropped_at_build`).
- Stopping rule: draw until 60 included cases or the eligible frame is
  exhausted (deterministic reserve order). If fewer eligible candidates than
  the target remain, sampling stops with the actual count and the shortfall is
  reported (no forced expansion, no fabricated cases).

## 14. Versioning procedure

- Domain pool, protocol, code (`evaluation/datav2/`), and every generated
  artifact are versioned; artifacts embed `created_utc` and content `sha256`.
- Any change to pool, seed, eligibility thresholds, dedup rules, or sampling
  code produces a **new version** (pool v2, protocol v1.1, etc.) and a
  regenerated, separately pinned dataset. v1 and v2 remain frozen forever.
- `datasets/v2/` writes go through the same immutability convention as
  experiments/v2: never overwrite an existing non-empty artifact directory
  without an explicit version bump.

## 15. Independence from system outputs (no selection bias)

Case selection completes **before** any v2 system evaluation is run. Eligibility
and sampling use only corpus metadata and the frozen frame. Pilot (v1) results
are not used to define eligibility. If pilot evidence is ever used to alter
eligibility in future versions, this protocol will be amended in writing and
the resulting dataset will be described as *conditioned on pilot results*, not
as an unbiased random sample.
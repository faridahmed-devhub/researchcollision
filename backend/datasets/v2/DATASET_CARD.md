# Dataset Card — v2 Crossing-Pair Discovery Benchmark

- **Protocol:** `CASE_SAMPLING_PROTOCOL.md` (frozen, sha256 `c51a2edca0db5903…`)
- **Sampling seed:** `20260925` · **method:** stratified seeded sampling
  (proportional allocation, largest-remainder; see protocol §6/§9)
- **Domain pool:** `evaluation/datav2/domain_pool_v1.json` (30 domains, sha256 `417a85650866b76e…`)
- **Built:** `2026-09-25T11:23:34+00:00` · **selection:** `2026-09-25T11:20:59+00:00`
- **Dataset file:** `dataset_v2.json` · sha256 `826263ae99a348b8cafc802e35a94afdd320c38d640cee553a22414cc3b126a4`
- **Status:** complete, immutable. Do not rebuild in place (see protocol §3I).

## Summary numbers

| Metric | Value |
|---|---|
| Pairing universe (all unordered domain pairs) | `435` |
| Candidate frame | `96` |
| Screened | `96` |
| Eligible (IN_T=4) | `87` |
| Target sample | `60` |
| Selected | `60` (reserve used: `True`) |
| Final dataset size | `60` cases |
| Records before dedup / kept | `2589` / `2525` |
| Dropped at build | 0 |

## Exclusion reasons (screening)

```json
{
  "EX1 insufficient_evidence_side_a=2": 9,
  "IN1": 87
}
```

## Copora access

- OpenAlex: always (screening + build), polite-pool mailto `buildbyfarid@gmail.com`.
- PubMed: used when a side's domain is `biomed` (protocol §3E).
- arXiv: best-effort, never blocks. Probe this session: `True`.
- API calls: {"openalex": 150, "arxiv": 120, "pubmed": 50}
- Corpus errors: []
- OpenAlex screening errors: []

## Stratum distribution

| Group | Universe | Frame alloc | Eligible | Selected |
|---|---|---|---|---|
| `inter_cs_ai_life_health` | 64 | 8 | 11 | 8 || `inter_cs_ai_physical_eng` | 64 | 10 | 14 | 10 || `inter_cs_ai_quant_methods` | 48 | 8 | 11 | 8 || `inter_life_health_physical_eng` | 64 | 8 | 11 | 8 || `inter_life_health_quant_methods` | 48 | 6 | 9 | 6 || `inter_physical_eng_quant_methods` | 48 | 7 | 11 | 7 || `intra_cs_ai` | 28 | 4 | 6 | 4 || `intra_life_health` | 28 | 3 | 5 | 3 || `intra_physical_eng` | 28 | 4 | 6 | 4 || `intra_quant_methods` | 15 | 2 | 3 | 2 |

## Dedup (protocol §10)

Hierarchy: DOI → normalized title+year → provider id → normalized-title fallback (flagged).

Matcher casualties: {"doi": 32, "norm_title_only_fallback(b)": 4, "norm_title+year": 25, "norm_title_only_fallback(a)": 3}
Audit log: `dedup_audit.json`.

## Provenance

- Case ids: `v2_<domain_a>_<domain_b>` with `candidate_id`/`sampling_stratum`/
  `selection_utc`/`inclusion_rationale`/`citation_gap_rationale` on each case (§3D).
- Each source paper records `source_provider`, `provider_id`, `doi`, `retrieved_utc`
  (corpus access date) and `evidence_text` (abstract) (§3E, §3D).
- v1 pilot is untouched (byte-identical snapshot + sha256 pin in `datasets/v1/MANIFEST.json`)
  and never mixed with v2 (§3I). Mapping: `datasets/v1/v1_to_v2_mapping.json`.

## Files

- `dataset_v2.json` — final dataset (sha256 `826263ae99a348b8cafc802e35a94afdd320c38d640cee553a22414cc3b126a4`)
- `candidate_frame.json` — deterministic 96-pair frame
- `candidate_population.json` — screening results
- `sampling_manifest.json` — full numbers, seeds, reasons, errors
- `dedup_audit.json` — dedup trace
- `DATASET_CARD.md` — this file

## Limitations

- 0 selected case(s) dropped at build:
- none
- arXiv may be under-represented if the API was unavailable during the build window.
- Screening/selection never used system outputs (protocol §3J); no evaluation ran on v2.

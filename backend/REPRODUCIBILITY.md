# Reproducibility guide (evaluation experiments)

This document states exactly how to reproduce evaluation runs of the
ResearchCollision evidence-discovery framework, what the seed controls, which
components are deterministic, which are not, how failures are recorded, and how
artifacts are kept immutable. It is the operating manual for the repeated
experiment protocol (see `EXPERIMENT_PROTOCOL.md`).

> Scope: pilot results in `evaluation_out_real_llm_v1/` remain an immutable
> single-run baseline and are governed by the audit in
> `research_paper/UPGRADE_PLAN.md`. This guide covers the Phase-2+ experiment
> infrastructure (`experiments/v2/seed<N>/`, batch runner, prompt archive).

## 1. Environment

| ingredient | required value / note |
|---|---|
| Python | 3.10 (2026-09 verification: 3.10.0) |
| Packages | `backend/requirements.txt` (incl. `numpy`, `scipy`, `tenacity`, `httpx`) |
| LLM endpoint | `LLM_PROVIDER=openai_compatible`, `OPENAI_BASE_URL=http://203.96.189.126:11434/v1`, `LLM_MODEL=qwen2.5:7b` (remote Ollama; verify reachability first) |
| LLM timeouts | `LLM_TIMEOUT_SECONDS=900`, `STRUCTURED_MAX_TOKENS=4096`, `STRUCTURED_MAX_TOKENS` never lowered below observed pilot need |
| Literature | `LITERATURE_PROVIDER=openalex`, `OPENALEX_EMAIL=` your public email (polite pool) |
| Offline default | `EVALUATION_FORCE_OFFLINE=1` (or unset) forces mock providers; use `0` only when intentionally running live |
| Secrets | `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `SECRET_KEY` are **never** written to artifact files (`config.json` redacts them) |

## 2. What the seed controls (and what it cannot)

The `--seed N` argument is plumbed end to end:
`evaluation/run.py`/`batch.py` → `run_evaluation` → per-system instances via
`get_system(name, seed)` → `DiscoveryPipeline(seed)` → agent `seed` →
`structured_generate(seed)` → provider `_chat`, which adds `"seed": N` to the
`/chat/completions` payload **only when N is not None**.

Seed-controlled:
- Random blind evaluation ids (`evaluation/human.py::make_blind_key`).
- LLM sampling, where the endpoint honors `seed` (Ollama does).
  Different seeds therefore produce different blind ids and, on a
  seed-honoring model, different sampling trajectories.

Deterministic regardless of seed (verified by `tests/test_seed_plumbing.py`):
- keyword / embedding baselines, mock providers, metrics, aggregation,
  failure analysis, CSV/JSON export. Under mock providers two runs with
  different seeds have identical metrics but distinguishable blind keys.

**Not controllable via seed** — document, never "reproducible":
- Model nondeterminism when the remote endpoint ignores `seed` or samples
  non-deterministically (batched decode, FP nondeterminism).
- Network / retry timing and transient failures. These are logged and
  recorded as failures, **never** converted into successes.

## 3. Reproducing a single seed

```powershell
cd backend
# offline/deterministic smoke run on the demo fixture:
python -m evaluation.experiment --dataset evaluation/data/demo_discovery.json ^
    --systems keyword,embedding,llm_only,pipeline --seed 0 --root experiments/v2

# live repeated run (Phase 5 style), with real providers:
$env:EVALUATION_FORCE_OFFLINE = "0"
python -m evaluation.experiment --dataset evaluation/data/real_case_study_v1.json ^
    --systems keyword,embedding,llm_only,pipeline --seed 0 --root experiments/v2
```

Every seed lands in an **immutable** directory `experiments/v2/seed<N>/`:

| file | content |
|---|---|
| `run_manifest.json` | seed, `status: completed`, timestamps, total runtime, contents list |
| `config.json` | full resolved config snapshot (seed, systems, offline mode, retry policy, settings with secrets redacted) |
| `prompt_versions.json` | per-prompt `{sha256, version, agent}` actually used |
| `corpus_meta.json` | dataset provenance, corpus availability, access-date policy |
| `status.json` | per-case/system `status`, `error`, `duration_ms`, totals |
| `results.json` / `results.csv` | normalized results and long-form metrics |
| `report.md` | human-readable report |
| `failure_analysis.json` / `failures.json` | structured failures (never hidden) |
| `outputs_per_case.json` | normalized per-case/per-system outputs |
| `blind_key.json` + `human_ratings_template.csv` | blind human-eval artifacts (when no ratings supplied) |

**Immutability rule:** a non-empty seed directory is never written again. To
re-run the same configuration, choose a new seed index. `batch.py` detects
completed dirs and can skip them (`--resume`).

## 4. Batch reproduction (seeds 0..N)

```powershell
python -m evaluation.batch --dataset evaluation/data/real_case_study_v1.json ^
    --seeds 0,1,2,3,4 --systems keyword,embedding,llm_only,pipeline ^
    --root experiments/v2 --resume
```

- sequential, one immutable dir per seed;
- `--resume` skips seeds with a completed `run_manifest.json`;
- partial/non-empty dirs without a completed manifest are reported as blocked
  (never overwritten, never silently "repaired");
- a machine-readable manifest is written to
  `experiments/v2/_batch_manifests/batch_<timestamp>.json` with a per-seed
  status summary.

## 5. Prompt provenance

Production prompts live in `backend/app/agents/prompts/*.txt`. A versioned,
immutable text archive is kept in `experiments/prompts/v1/`:

```powershell
python -m evaluation.prompt_archive --version v1 --root experiments/prompts
```

`MANIFEST.json` pins every prompt's sha256 and the agent/version that serves
it; seed runs persist the same hashes in `prompt_versions.json`, so any
executed seed can be re-traced to its exact prompt text even after the prompt
files change. `collaboration_ranking.txt` and `verification.txt` are marked
`unused` (present in the prompts dir but not loaded by any agent).

## 6. Retry & failure policy

- Retryable HTTP statuses: `429, 500, 502, 503, 504`; max 3 attempts with
  exponential backoff (`min 2s, max 15s`, multiplier 1) — see
  `app/providers/llm/openai_compatible.py` and the `retry_policy` block in any
  seed `config.json`.
- Non-retryable client errors (401/403/400) fail fast, without retries.
- Timeouts propagate as failures into `failures.json` with case/system and the
  verbatim error; they are never retried into "successes".
- This policy is recorded in every seed's `config.json` so statistical analysis
  can account for retry-policy effects.

## 7. Known reproducibility limitations (honest)

1. Remote model determinism depends on the endpoint honoring `seed`.
2. Raw LLM request/response traces are not yet persisted (provider-level trace
   capture is part of Phase 4); normalized outputs are persisted now.
3. Corpus access dates are recorded at build/query time (Phase 3/5), not for
   the pilot v1 dataset.
4. Human ratings are pending real raters; the infrastructure exports blind
   templates, but no fabricated or LLM-substitute scores are produced.
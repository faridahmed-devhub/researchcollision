"""Markdown evaluation report generation.

The report reflects ONLY what was actually measured. Human metrics are shown
as *pending annotation* unless a real human-ratings file was provided and
merged. Inter-rater reliability is shown only when >=2 real raters exist.
Limitation notes are mandatory because fixtures, proxy metrics and
machine-generated reference sets must never be presented as real research
performance.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluation.environment import offline_mode
from evaluation.metrics import (
    AUTOMATIC_METRICS,
    HUMAN_RATINGS,
)
from evaluation.schemas import SYNTHETIC_FIXTURE_LABEL


def _fmt(v: float | None, nd: int = 3) -> str:
    if v is None:
        return "— (n/a)"
    return f"{v:.{nd}f}"


def _mean_row(agg: dict[str, Any], key: str) -> str:
    m = (agg.get("metrics") or {}).get(key) or {}
    mean = m.get("mean")
    count = m.get("n")
    if mean is None:
        return "— (n/a)"
    return f"{mean:.3f} (n={count})"


def build_report(
    *,
    dataset: Any,
    case_stats: list[dict[str, Any]],
    config: dict[str, Any],
    case_results: list[dict[str, Any]],
    aggregates: dict[str, Any],
    human: dict[str, Any],
    failures: list[dict[str, str]],
    out_path: str | Path,
    failure_analysis: list[dict[str, Any]] | None = None,
    inter_rater: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    add = lines.append

    add("# ResearchCollision Evaluation Report")
    add("")
    add(f"- Dataset: **{dataset.dataset_id}** (version `{getattr(dataset, 'version', 'n/a')}`)")
    add(f"- Dataset label: `{dataset.label}`")
    add(f"- Provenance: `{dataset.provenance}` "
        f"({'' if dataset.is_synthetic else 'not '}synthetic)")
    if getattr(dataset, "created_utc", None):
        add(f"- Dataset created (UTC): {dataset.created_utc}")
    if getattr(dataset, "content_sha256", None):
        add(f"- Dataset content sha256: `{dataset.content_sha256}`")
    if dataset.is_synthetic:
        add("")
        add(f"> **{SYNTHETIC_FIXTURE_LABEL}** — automatic numbers in this report are "
            f"a *synthetic demo*, not a measure of real-world research performance.")
    else:
        add("")
        add("> **Real case-study dataset.** Source papers are publicly traceable "
            "scholarly records (see provenance below). Automatic metrics are "
            "measurements on a fixed retrieval snapshot, not leaderboard scores.")
    add(f"- Generated (UTC): {config.get('generated_utc', 'unknown')}")
    add(f"- Offline mode: `{offline_mode()}`")
    add(f"- Systems evaluated: {', '.join(config.get('systems', []))}")
    providers = config.get("providers", {})
    add(f"- Providers used: LLM=`{providers.get('llm_provider')}`, "
        f"Embeddings=`{providers.get('embedding_provider')}`, "
        f"Literature chain=`{', '.join(providers.get('literature_chain', []))}` "
        f"(first provider that succeeds is used; offline mode only ever calls mock)")
    add("")

    # -- provenance / annotation sources -----------------------------------
    add("## Dataset provenance & annotation sources")
    add("")
    add("Human-evaluation systems must never treat machine-generated or absent "
        "annotations as if they were independent human labels.")
    add("")
    add("| field | source |")
    add("|---|---|")
    src_providers = getattr(dataset, "source_providers", []) or ["(none recorded)"]
    add(f"| source papers | {', '.join(src_providers)} (real, traceable) |")
    prov = getattr(dataset, "annotation_provenance", {}) or {}
    if prov:
        for field, source in prov.items():
            add(f"| {field} | `{source}` |")
    else:
        add("| annotations | (not recorded) |")
    add("")
    if getattr(dataset, "notes", None):
        add(dataset.notes)
        add("")

    add("## Dataset statistics")
    add("")
    add("| case_id | papers | expected gaps | expected refs | expected topics | expected methods |")
    add("|---|---|---|---|---|---|")
    for s in case_stats:
        add(
            f"| {s['case_id']} | {s['n_source_papers']} | {s['n_expected_gaps']} | "
            f"{s['n_expected_refs']} | {s['n_expected_topics']} | {s['n_expected_methods']} |"
        )
    add("")

    add("## Automatic metrics (per system, mean over cases)")
    add("")
    add("> Proxy metrics (`research_gap_relevance`, `intersection_relevance`, "
        "`hypothesis_plausibility_proxy`) are automatic approximations and "
        "**require human review** for final judgment. `hallucination_rate` is "
        "the fraction of cited references that cannot be traced; "
        "`evidence_grounding_precision` and `citation_coverage` compare against "
        "the dataset's expected supporting evidence (when such an annotation "
        "exists — otherwise they are `n/a`, never 0).")
    add("")
    header = "| metric | " + " | ".join(aggregates.keys()) + " |"
    add(header)
    add("|" + "---|" * (len(aggregates) + 1))
    for spec in AUTOMATIC_METRICS:
        key = spec["key"]
        cells = [_mean_row(aggregates[system], key) for system in aggregates]
        flag = " *" if spec["requires_human"] else ""
        gold = " †" if spec.get("requires_gold") else ""
        add(f"| {spec['label']}{flag}{gold} | " + " | ".join(cells) + " |")
    add("")
    add("`*` requires human judgment for final interpretation. "
        "`†` requires an expected-annotation set; shown as `n/a` when the "
        "dataset does not provide one.")
    add("")

    add("## Per-case automatic metrics")
    add("")
    add("| case_id | system | status | gnd-precision | citation-validity | hallucination | coverage | gap-relevance* | ix-relevance* | hyp-ground | hyp-plaus* | exp-design |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for case in case_results:
        for system_name, run in case["systems"].items():
            if run["status"] != "ok":
                add(
                    f"| {case['case_id']} | {system_name} | **error** | - | - | - | - | - | - | - | - | - |"
                )
                continue
            m = run["metrics"]
            add(
                f"| {case['case_id']} | {system_name} | ok | "
                f"{_fmt(m.get('evidence_grounding_precision'))} | "
                f"{_fmt(m.get('evidence_citation_validity'))} | "
                f"{_fmt(m.get('hallucination_rate'))} | "
                f"{_fmt(m.get('citation_coverage'))} | "
                f"{_fmt(m.get('research_gap_relevance'))} | "
                f"{_fmt(m.get('intersection_relevance'))} | "
                f"{_fmt(m.get('hypothesis_grounding_ratio'))} | "
                f"{_fmt(m.get('hypothesis_plausibility_proxy'))} | "
                f"{_fmt(m.get('experiment_design_completeness'))} |"
            )
    add("")

    add("## Human evaluation")
    add("")
    add("Human metrics (relevance, novelty, plausibility, evidence quality) are "
        "rated 1-5 by human annotators on the **blind** template: each generated "
        "gap/intersection/hypothesis receives a random `eval_id`, and raters "
        "never see the system name, the baseline identity, or any automatic "
        "score. The system never computes these values.")
    if human.get("provided"):
        human_agg = human["aggregates"] or {}
        add("")
        add("| dimension | " + " | ".join(human_agg.keys()) + " |")
        add("|" + "---|" * (len(human_agg) + 1))
        for dim, spec in HUMAN_RATINGS.items():
            cells = []
            for system in human_agg:
                stats = human_agg[system].get(dim) or {}
                cells.append(
                    f"{stats['mean']:.2f} (n={stats['n']})"
                    if stats.get("mean") is not None else "— (no ratings)"
                )
            add(f"| {dim} | " + " | ".join(cells) + " |")
        add("")
        add(f"Raters provided {human.get('ratings_count', 0)} human rating rows "
            "across generated gaps, intersections and hypotheses.")
        add("")
        add("**Rating rubric (1-5):**")
        for dim, spec in HUMAN_RATINGS.items():
            add(f"- **{dim}**: {spec['definitions'][1]} | ... | {spec['definitions'][5]}")
        add("")
        if inter_rater is not None:
            add("### Inter-rater reliability")
            add("")
            add("| dimension | raters | shared items | % exact agreement | weighted kappa |")
            add("|---|---|---|---|---|")
            for dim in HUMAN_RATINGS:
                s = inter_rater.get(dim) or {}
                if s.get("available"):
                    add(
                        f"| {dim} | {s['n_raters']} | {s['n_shared_items']} | "
                        f"{s['percent_agreement']:.2f} | {s['weighted_kappa']:.3f} |"
                    )
                else:
                    add(f"| {dim} | {s.get('n_raters', 0)} | {s.get('n_shared_items', 0)} | — | n/a |")
            add("")
            add("Weighted kappa is the mean pairwise quadratic-weighted Cohen's "
                "kappa (ordinal 1-5). No agreement statistic is reported unless "
                "real ratings from >=2 raters exist.")
            add("")
    else:
        add("")
        add("**Pending human annotation.** Neither automatic metrics nor the system "
            "can substitute for a human relevance/novelty/plausibility/evidence "
            "assessment. A blank, blind template is exported as "
            "`human_ratings_template.csv`; the `eval_id`->system key is written to "
            "`blind_key.json` (not for raters). Merge completed ratings back via "
            "`--human <file>`.")
        add("")
        for dim, spec in HUMAN_RATINGS.items():
            add(f"- **{dim}** (1-5): {spec['definitions'][5]}")
            add(f"  (1 = {spec['definitions'][1]})")
        add("")

    add("## Failure analysis")
    add("")
    if failure_analysis:
        add("Serious failures are classified by origin stage "
            "(`retrieval` | `grounding` | `reasoning` | `generation`).")
        add("")
        add("| case_id | system | failure type | stage | evidence involved | detail |")
        add("|---|---|---|---|---|---|")
        for f in failure_analysis:
            evidence = "; ".join(f.get("evidence_involved") or []) or "—"
            add(
                f"| {f['case_id']} | {f['system']} | {f['failure_type']} | "
                f"{f['stage']} | {evidence} | {f['detail']} |"
            )
        add("")
    if failures:
        add("| case_id | system | error |")
        add("|---|---|---|")
        for f in failures:
            add(f"| {f['case_id']} | {f['system']} | `{f['error']}` |")
        add("")
    if not failure_analysis and not failures:
        add("_No system failures or other serious failures were recorded for this run._")
        add("")

    add("## Limitations")
    add("")
    for lim in _limitations(dataset, offline_mode()):
        add(f"- {lim}")
    add("")

    text = "\n".join(lines)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(text, encoding="utf-8")
    return text


def _limitations(dataset: Any, offline: bool) -> list[str]:
    common = [
        (
            "Automatic token/embedding-similarity proxies for gap/intersection "
            "relevance and plausibility are approximations. Final judgment requires "
            "human ratings."
        ),
        (
            "Hallucination rate and citation validity are measured against the case "
            "source corpus plus each system's own retrieval context; a broader "
            "external oracle would be needed to certify absence of hallucination."
        ),
        (
            "The `llm_only` baseline has no retrieval/evidence machinery, so its "
            "citation-based metrics are `n/a` by design."
        ),
        (
            "`experiment_design_completeness` counts only the nine standard "
            "experiment-design fields the pipeline emits; heuristic baselines emit "
            "none and score 0 by definition."
        ),
        (
            "No superiority claim should be drawn from these means; ranking systems "
            "requires controlled experiments on real datasets with human evaluation."
        ),
    ]
    if offline:
        common.append(
            "This run was in offline mode: the LLM is the deterministic mock provider "
            "and the logical model is fully mocked, so these numbers exercise "
            "plumbing, not real reasoning quality."
        )
    if dataset.is_synthetic:
        return [
            (
                "The bundled dataset is a SYNTHETIC DEMO fixture; numbers here are "
                "not evidence of real-world performance and must not be presented as such."
            ),
            *common,
        ]
    return [
        (
            "Source papers are a fixed retrieval snapshot from public scholarly APIs "
            "at dataset build time; the literature keeps changing after that date."
        ),
        (
            "Research-gap annotations are not independently available for these "
            "cases, so research-gap relevance is `n/a` rather than a fabricated gold "
            "score. Any machine-generated reference sets are labeled in the "
            "provenance table and are heuristic, not expert labels."
        ),
        (
            "Language-model steps used the deterministic mock LLM provider (no model "
            "API credentials were configured for this run): the run exercises real "
            "literature retrieval + grounding plumbing, but NOT real language-model "
            "reasoning quality."
        ),
        (
            "Human relevance/novelty/plausibility/evidence-quality ratings are shown "
            "only if genuinely provided by raters; they are never invented. If none "
            "were provided, the human section remains pending."
        ),
        *common,
    ]

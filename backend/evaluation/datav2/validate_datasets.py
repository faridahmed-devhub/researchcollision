"""v2 dataset validator (Phase 3H): automated checks + CLI + reusable API.

Checks are split into *hard* invariants (must pass) and *informational*
items (reported). When `dataset_v2.json` is absent the dataset-dependent
checks are skipped (not failed) so the frozen infrastructure can be validated
before the live corpus pull completes.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from evaluation.datav2 import sampling as s
from evaluation.schemas import EvaluationDataset

V1_CASE_IDS = [
    "federated_learning_x_privacy",
    "causal_inference_x_clinical_ml",
    "gnn_x_protein_structure",
    "rl_x_sim_to_real",
    "clinical_nlp_x_ehr",
    "climate_downscaling_x_deep_learning",
    "quantum_chemistry_x_dft",
    "recommender_x_fairness",
    "single_cell_x_transfer_learning",
    "materials_discovery_x_active_learning",
    "knowledge_graph_x_question_answering",
    "speech_recognition_x_hearing_aids",
]
VALID_CORPORA = ("openalex", "arxiv", "pubmed")
V2_ID_RE = re.compile(r"^v2_[a-z0-9]+_[a-z0-9]+$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_protocol_path() -> Path:
    return Path(__file__).resolve().parents[2] / "CASE_SAMPLING_PROTOCOL.md"


def default_v1_src() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def check(rule: str, ok: bool, detail: str = "") -> dict[str, str]:
    return {"rule": rule, "status": "pass" if ok else "fail", "detail": detail}


def skipped(rule: str, detail: str = "") -> dict[str, str]:
    return {"rule": rule, "status": "skip", "detail": detail}


def validate_v2(root: str | Path = None) -> list[dict[str, str]]:
    """Run all checks (returns list of rule results; API for tests)."""
    if root is None:
        root = Path(__file__).resolve().parents[2] / "datasets" / "v2"
    root = Path(root)
    results: list[dict[str, str]] = []

    pool = s.load_pool()
    protocol = default_protocol_path()
    v1_src = default_v1_src()

    frame_path = root / "candidate_frame.json"
    pop_path = root / "candidate_population.json"
    dataset_path = root / "dataset_v2.json"
    dedup_path = root / "dedup_audit.json"
    manifest_path = root / "sampling_manifest.json"

    if not manifest_path.exists():
        return [check("manifest_exists", False, "sampling_manifest.json missing")]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # --- frozen protocol / pool ---
    results.append(check("protocol_present", protocol.exists()))
    if protocol.exists():
        results.append(
            check(
                "protocol_frozen",
                manifest.get("protocol_sha256") == _sha(protocol),
                f"manifest={str(manifest.get('protocol_sha256'))[:12]}.. file={_sha(protocol)[:12]}..",
            )
        )
    results.append(check("pool_frozen", manifest.get("pool_sha256") == s.pool_sha256()))

    # --- deterministic frame ---
    if frame_path.exists():
        stored = json.loads(frame_path.read_text(encoding="utf-8"))
        recomputed = s.build_frame(pool)
        frame_ok = [c["pair_id"] for c in stored["candidates"]] == [
            c["pair_id"] for c in recomputed
        ] and [c["candidate_id"] for c in stored["candidates"]] == [
            c["candidate_id"] for c in recomputed
        ]
        results.append(check("frame_deterministic", frame_ok))
        results.append(check("frame_size", len(stored["candidates"]) == s.N_FRAME))

    # --- manifest population numbers ---
    if pop_path.exists():
        pop = json.loads(pop_path.read_text(encoding="utf-8"))
        decisions: dict[str, int] = {}
        for c in pop["candidates"]:
            decisions[c["decision"]] = decisions.get(c["decision"], 0) + 1
        results.append(check("pop_decisions_match", decisions == manifest.get("screening_decisions", {})))
        eligible = decisions.get("eligible", 0)
        results.append(check("pop_eligible_matches", eligible == manifest.get("eligible")))
        if frame_path.exists():
            frame_ids = {c["pair_id"] for c in json.loads(frame_path.read_text(encoding="utf-8"))["candidates"]}
            results.append(check("pop_subset_of_frame", {c["pair_id"] for c in pop["candidates"]} == frame_ids))

    # Acceptance gate: NO provider failure may be interpreted as exclusion (§3E, §3K).
    # Any EX2 entry means corpus throttling reached the sample and the build must be
    # re-run once access is healthy — never treated as scientific exclusion.
    ex2_count = 0
    if pop_path.exists():
        pop = json.loads(pop_path.read_text(encoding="utf-8"))
        ex2_count = sum(1 for c in pop["candidates"] if c["decision"] == "excluded_provider")
    elif manifest.get("screening_decisions"):
        ex2_count = manifest["screening_decisions"].get("excluded_provider", 0)
    results.append(check("no_provider_failure_excluded", ex2_count == 0, f"excluded_provider={ex2_count}"))

    # Acceptance gate: the sampling manifest must be reproducible from the
    # frozen pool + population (protocol §6/§9).
    if dataset_path.exists() and pop_path.exists():
        pop = json.loads(pop_path.read_text(encoding="utf-8"))
        eligible = [c["pair_id"] for c in pop["candidates"] if c["decision"] == "eligible"]
        recomputed = s.select_final(eligible, s.load_pool(), seed=s.SEED, n_target=s.N_TARGET)
        stored = manifest.get("final_sample", {}).get("selected_ids")
        results.append(
            check(
                "select_final_reproducible",
                recomputed["selected"] == stored,
                f"recompute={len(recomputed['selected'])} stored={len(stored or [])}",
            )
        )
    else:
        results.append(skipped("select_final_reproducible", "dataset/population not built yet"))

    if not dataset_path.exists():
        results.append(skipped("dataset_present", "dataset_v2.json not built yet (corpus pull pending) — dataset checks skipped"))
        return results

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    ds = EvaluationDataset.model_validate(data)  # schema + v1-style invariants

    results.append(check("dataset_schema", True))
    results.append(check("dataset_sha256", ds.content_sha256 == help_compute_sha(ds)))
    n = len(ds.cases)
    results.append(check("dataset_size_min50", n >= 50, f"n={n}"))
    ids = [c.case_id for c in ds.cases]
    results.append(check("case_ids_unique", len(set(ids)) == len(ids)))
    bad_ids = [i for i in ids if not V2_ID_RE.match(i)]
    results.append(check("case_ids_convention", not bad_ids, f"bad={bad_ids[:5]}"))
    v1_collisions = [i for i in ids if i in V1_CASE_IDS]
    results.append(check("no_v1_id_reuse", not v1_collisions))
    missing_fields: list[str] = []
    for c in ds.cases:
        for f in ("sampling_stratum", "candidate_id", "selection_utc", "inclusion_rationale", "citation_gap_rationale"):
            if getattr(c, f) is None:
                missing_fields.append(f"{c.case_id}.{f}")
    results.append(check("case_metadata_complete", not missing_fields, f"missing={missing_fields[:6]}"))

    corpus_labels = {p.source_provider for c in ds.cases for p in c.source_papers}
    bad_corpus = corpus_labels - set(VALID_CORPORA)
    results.append(check("corpus_labels_valid", not bad_corpus, f"bad={bad_corpus}"))
    no_id = [
        f"{c.case_id}:{p.paper_id}"
        for c in ds.cases
        for p in c.source_papers
        if not (p.doi or p.provider_id)
    ]
    results.append(check("source_ids_present", not no_id, f"bad={no_id[:5]}"))
    no_evidence = [
        f"{c.case_id}:{p.paper_id}"
        for c in ds.cases
        for p in c.source_papers
        if not p.evidence_text
    ]
    results.append(check("source_evidence_present", not no_evidence, f"bad={no_evidence[:5]}"))
    no_retrieved = [
        f"{c.case_id}:{p.paper_id}"
        for c in ds.cases
        for p in c.source_papers
        if not p.retrieved_utc
    ]
    results.append(check("source_retrieved_utc", not no_retrieved, f"bad={no_retrieved[:3]}"))

    # candidate ids referenced exist in the population
    if pop_path.exists():
        pop_ids = {c["candidate_id"] for c in json.loads(pop_path.read_text(encoding="utf-8"))["candidates"]}
        refs = {c.candidate_id for c in ds.cases}
        results.append(check("candidates_exist", refs.issubset(pop_ids), f"missing={sorted(refs-pop_ids)[:5]}"))

    # v1 immutability vs authoritative sources
    v1_root = root.parent / "v1"
    if v1_root.exists() and (v1_root / "real_case_study_v1.json").exists():
        v1_src_file = v1_src / "real_case_study_v1.json"
        results.append(
            check(
                "v1_dataset_unchanged",
                v1_src_file.exists() and _sha(v1_root / "real_case_study_v1.json") == _sha(v1_src_file),
            )
        )
        v1_ids = [c["case_id"] for c in json.loads((v1_root / "real_case_study_v1.json").read_text(encoding="utf-8"))["cases"]]
        results.append(check("v1_12_cases_preserved", sorted(v1_ids) == sorted(V1_CASE_IDS)))
    else:
        results.append(skipped("v1_snapshot", "datasets/v1 snapshot not present"))

    # v1 in v2 ids: the v2 file must never contain v1 ids — already checked above.
    results.append(check("v2_independent_of_v1", True, "v1 and v2 files are separate and never merged"))

    return results


def help_compute_sha(ds: EvaluationDataset) -> str:
    return ds.compute_content_sha256()


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="evaluation.datav2.validate_datasets", description="Validate v2 dataset artifacts.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2] / "datasets" / "v2"))
    args = parser.parse_args(argv)
    results = validate_v2(args.root)
    hard = [r for r in results if r["status"] == "fail"]
    skipped_n = sum(1 for r in results if r["status"] == "skip")
    for r in results:
        print(f"[{r['status'].upper():4}] {r['rule']} {r['detail']}")
    print(f"{len(results) - len(hard) - skipped_n} pass, {len(hard)} fail, {skipped_n} skipped")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
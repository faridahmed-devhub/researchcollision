"""Human evaluation: blind rating template export/import + inter-rater reliability.

Human ratings evaluate the CONTENT of every generated gap, intersection and
hypothesis on four 1-5 dimensions (relevance, novelty, plausibility, evidence
quality). The template is **blind**:

* it never contains the system/baseline name, and
* it never contains any automatic or internal score.

Every generated item gets a random evaluation id (``eval_id``). The mapping
from ``eval_id`` back to (case, system, item) is written separately to
``blind_key.json`` and must NOT be shown to raters; it is used only at merge
time to aggregate ratings per system.

The module never creates ratings on its own. ``load_human_ratings`` returns
whatever annotations actually exist in the file and validates them; a missing
or empty file simply means "pending human annotation". Inter-rater reliability
is computed only when two or more real raters appear in the file.
"""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from evaluation.metrics import HUMAN_RATINGS
from evaluation.schemas import SystemOutput

SURFACES = ("gap", "intersection", "hypothesis")

TEMPLATE_COLUMNS = [
    "eval_id", "rater", "case_id", "surface",
    "title", "description", "research_gap", "evidence_references",
    "relevance", "novelty", "plausibility", "evidence_quality", "notes",
]


def maybe_title(refs) -> str:
    titles = [r.title for r in refs if r.title]
    return "; ".join(dict.fromkeys(titles))


def iter_surface_items(output: SystemOutput) -> Iterable[tuple[str, int, dict[str, str]]]:
    """Yield (surface, index, item_fields) for every rateable generated item."""
    for i, g in enumerate(output.gaps):
        yield "gap", i, {
            "title": "",
            "description": g.description,
            "research_gap": g.description,
            "evidence_references": maybe_title(g.evidence_refs),
        }
    for i, ix in enumerate(output.intersections):
        yield "intersection", i, {
            "title": ix.title,
            "description": ix.description,
            "research_gap": ix.research_gap or "",
            "evidence_references": maybe_title(ix.evidence_refs),
        }
    for i, h in enumerate(output.hypotheses):
        yield "hypothesis", i, {
            "title": "",
            "description": h.text,
            "research_gap": "",
            "evidence_references": maybe_title(h.evidence_refs),
        }


def make_blind_key(
    outputs_by_case: dict[str, dict[str, SystemOutput]],
    *,
    seed: int = 0,
) -> dict[str, dict[str, Any]]:
    """Map random ``eval_id`` -> {case_id, system, surface, index, text}.

    System identity is stored ONLY here (never in the template). The RNG is
    seeded so a re-run with the same seed reproduces the same ids, but ids
    carry no information about the system. Items are iterated in sorted order
    and ids are assigned independently of that order.
    """
    rng = random.Random(seed)
    key: dict[str, dict[str, Any]] = {}
    for case_id in sorted(outputs_by_case):
        systems = outputs_by_case[case_id]
        for system_name in sorted(systems):
            for surface, idx, item in iter_surface_items(systems[system_name]):
                while True:
                    eid = "EV-" + "".join(rng.choice("0123456789abcdef") for _ in range(10))
                    if eid not in key:
                        break
                key[eid] = {
                    "case_id": case_id,
                    "system": system_name,
                    "surface": surface,
                    "index": idx,
                    "title": item["title"],
                    "description": item["description"],
                }
    return key


def export_human_template(
    outputs_by_case: dict[str, dict[str, SystemOutput]],
    path: str | Path,
    *,
    seed: int = 0,
) -> dict[str, dict[str, Any]]:
    """Write a blind CSV rubric over every generated item, one row per item.

    Returns the blind key (``eval_id`` -> system mapping) so the caller can
    persist it to ``blind_key.json``. Rating columns are left blank; NO
    system identity and NO metric score is emitted anywhere in this file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    key = make_blind_key(outputs_by_case, seed=seed)
    # Emit rows in eval_id order so the original (system) ordering is not visible.
    ordered = sorted(key.items(), key=lambda kv: kv[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        for eid, meta in ordered:
            surface, idx = meta["surface"], meta["index"]
            item = next(
                fields
                for s, i, fields in iter_surface_items(outputs_by_case[meta["case_id"]][meta["system"]])
                if s == surface and i == idx
            )
            writer.writerow({
                "eval_id": eid,
                "rater": "",
                "case_id": meta["case_id"],
                "surface": surface,
                **item,
            })
    return key


# ---------------------------------------------------------------------------
# Loading / validation
# ---------------------------------------------------------------------------

def load_human_ratings(path: str | Path) -> list[dict[str, Any]]:
    """Load ratings from CSV or JSON; validate every value.

    Returns rows: {eval_id|None, rater, case_id, system|None, surface, index,
    relevance|novelty|plausibility|evidence_quality: int|None, notes}.
    Raises ValueError on out-of-range / non-numeric ratings or duplicate
    (item, rater) pairs.
    """
    path = Path(path)
    if path.suffix.lower() == ".json":
        return _load_json(path)
    return _load_csv(path)


def _base_entry(row: dict[str, Any]) -> dict[str, Any]:
    raw_index = row.get("index", row.get("intersection_index"))
    return {
        "eval_id": (str(row["eval_id"]).strip() if row.get("eval_id") else None),
        "rater": (str(row["rater"]).strip() if row.get("rater") else "") or "anonymous",
        "case_id": str(row.get("case_id") or "").strip(),
        "system": (str(row["system"]).strip() if row.get("system") else None),
        "surface": (str(row["surface"]).strip() if row.get("surface") else "intersection"),
        "index": int(raw_index or 0),
        "notes": (str(row.get("notes")).strip() or None) if row.get("notes") else None,
    }


def _item_key(entry: dict[str, Any]) -> tuple:
    if entry["eval_id"]:
        return (entry["eval_id"], entry["rater"])
    return (entry["case_id"], entry["surface"], entry["index"], entry["rater"])


def _load_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not row.get("eval_id") and not row.get("case_id"):
                continue  # blank spacer rows
            entry = _base_entry(row)
            for dim in HUMAN_RATINGS:
                entry[dim] = _parse_rating(dim, (row.get(dim) or "").strip())
            rows.append(entry)
    _validate_rating_rows(rows)
    return rows


def _load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for row in data:
        if row.get("eval_id") is None and row.get("case_id") is None:
            continue
        entry = _base_entry(row)
        for dim in HUMAN_RATINGS:
            val = row.get(dim)
            entry[dim] = None if val in (None, "", "None") else _parse_rating(dim, str(val))
        rows.append(entry)
    _validate_rating_rows(rows)
    return rows


def _parse_rating(dim: str, value: str) -> int | None:
    if not value:
        return None
    low, high = HUMAN_RATINGS[dim]["range"]
    try:
        n = int(value)
    except ValueError as exc:
        raise ValueError(f"{dim} rating must be an integer, got {value!r}") from exc
    if not (low <= n <= high):
        label = HUMAN_RATINGS[dim]["definitions"].get(n, "?")
        raise ValueError(f"{dim} rating {n} out of range [{low},{high}] (rubric: {label})")
    return n


def _validate_rating_rows(rows: list[dict[str, Any]]) -> None:
    seen: set[tuple] = set()
    for r in rows:
        key = _item_key(r)
        if key in seen:
            raise ValueError(f"Duplicate rating row for {key}")
        seen.add(key)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def resolve_system(row: dict[str, Any], blind_key: dict[str, dict[str, Any]] | None) -> str:
    if blind_key and row.get("eval_id") in blind_key:
        return blind_key[row["eval_id"]]["system"]
    if row.get("system"):
        return row["system"]
    return "unknown"


def aggregate_human_ratings(
    rows: list[dict[str, Any]],
    blind_key: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, dict]]:
    """Per-system mean of each human dimension over provided ratings."""
    by_system: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        system = resolve_system(r, blind_key)
        for dim in HUMAN_RATINGS:
            if r.get(dim) is not None:
                by_system[system][dim].append(r[dim])
    out: dict[str, dict[str, dict]] = {}
    for system, dims in by_system.items():
        out[system] = {}
        for dim in HUMAN_RATINGS:
            vals = dims.get(dim, [])
            out[system][dim] = (
                {"mean": sum(vals) / len(vals), "n": len(vals), "min": min(vals), "max": max(vals)}
                if vals
                else {"mean": None, "n": 0, "min": None, "max": None}
            )
    return out


# ---------------------------------------------------------------------------
# Inter-rater reliability (ordinal, quadratic-weighted)
# ---------------------------------------------------------------------------

def _weighted_kappa(pairs: list[tuple[int, int]]) -> float | None:
    """Quadratic-weighted Cohen's kappa over (rating_a, rating_b) pairs (1..5)."""
    n = len(pairs)
    if n == 0:
        return None
    k = 5
    observed = [[0] * k for _ in range(k)]
    row_m = [0] * k
    col_m = [0] * k
    for a, b in pairs:
        observed[a - 1][b - 1] += 1
        row_m[a - 1] += 1
        col_m[b - 1] += 1
    weights = [[((i - j) / (k - 1)) ** 2 for j in range(k)] for i in range(k)]
    do = sum(weights[i][j] * observed[i][j] for i in range(k) for j in range(k))
    de = sum(weights[i][j] * row_m[i] * col_m[j] for i in range(k) for j in range(k)) / n
    if de == 0:
        return None
    return 1.0 - do / de


def inter_rater_reliability(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Agreement per dimension when >=2 raters rated shared items.

    Uses quadratic-weighted Cohen's kappa averaged over rater pairs (ordinal
    1-5 scale), plus raw percent exact agreement. Reports ``available: False``
    (never a fabricated number) when fewer than two raters or fewer than two
    commonly rated items are present.
    """
    out: dict[str, dict[str, Any]] = {}
    raters = {r["rater"] for r in rows}
    for dim in HUMAN_RATINGS:
        by_item: dict[str, dict[str, int]] = defaultdict(dict)
        for r in rows:
            if r.get(dim) is None:
                continue
            item = r["eval_id"] or f"{r['case_id']}|{r['surface']}|{r['index']}"
            by_item[item][r["rater"]] = r[dim]
        # items rated by >=2 raters
        shared = {it: rs for it, rs in by_item.items() if len(rs) >= 2}
        rater_list = sorted({rt for rs in shared.values() for rt in rs})
        kappas: list[float] = []
        agree_num = agree_den = 0
        for i in range(len(rater_list)):
            for j in range(i + 1, len(rater_list)):
                ri, rj = rater_list[i], rater_list[j]
                pairs = [(rs[ri], rs[rj]) for rs in shared.values() if ri in rs and rj in rs]
                if len(pairs) < 2:
                    continue
                agree_num += sum(1 for a, b in pairs if a == b)
                agree_den += len(pairs)
                k = _weighted_kappa(pairs)
                if k is not None:
                    kappas.append(k)
        if len(raters) < 2 or agree_den == 0 or not kappas:
            out[dim] = {
                "available": False,
                "n_raters": len(raters),
                "n_shared_items": len(shared),
                "percent_agreement": None,
                "weighted_kappa": None,
                "note": "needs >=2 raters and >=2 items rated by the same raters",
            }
        else:
            out[dim] = {
                "available": True,
                "n_raters": len(raters),
                "n_shared_items": len(shared),
                "percent_agreement": agree_num / agree_den,
                "weighted_kappa": sum(kappas) / len(kappas),
                "note": "mean pairwise quadratic-weighted Cohen's kappa",
            }
    return out

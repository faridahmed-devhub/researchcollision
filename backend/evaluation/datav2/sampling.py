"""Deterministic, stratified sampling logic for the v2 dataset (protocol §6, §9).

Pure functions only (no network): the pairing universe, the candidate frame,
and the final sample are fully reproducible from the frozen domain pool and the
fixed sampling seed. See CASE_SAMPLING_PROTOCOL.md (frozen) for definitions.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

POOL_PATH = Path(__file__).resolve().parent / "domain_pool_v1.json"
SEED = 20260925
N_FRAME = 96
N_TARGET = 60
IN_T = 4  # minimum usable records per side for eligibility (screening)


def load_pool(path: str | Path = POOL_PATH) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["domains"]


def pool_sha256(path: str | Path = POOL_PATH) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _index(pool: list[dict[str, Any]]) -> dict[str, int]:
    return {d["id"]: i for i, d in enumerate(pool)}


def group_of(pool: list[dict[str, Any]], a_id: str, b_id: str) -> str:
    da = next(d for d in pool if d["id"] == a_id)
    db = next(d for d in pool if d["id"] == b_id)
    if da["discipline"] == db["discipline"]:
        return f"intra_{da['discipline']}"
    cats = sorted((da["discipline"], db["discipline"]))
    return f"inter_{cats[0]}_{cats[1]}"


def universe(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """All unordered domain pairs (canonical a<b order by pool index)."""
    idx = _index(pool)
    pairs: list[dict[str, Any]] = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            a, b = pool[i], pool[j]
            pairs.append(
                {
                    "pair_id": f"v2_{a['id']}_{b['id']}",
                    "domain_a": a["id"],
                    "domain_b": b["id"],
                    "query_a": a["query"],
                    "query_b": b["query"],
                    "field_query": f"{a['query']} {b['query']}",
                    "group": group_of(pool, a["id"], b["id"]),
                }
            )
    pairs.sort(key=lambda p: (p["group"], p["pair_id"]))
    return pairs


def group_sizes(pool: list[dict[str, Any]]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for p in universe(pool):
        sizes[p["group"]] = sizes.get(p["group"], 0) + 1
    return sizes


def allocate(count: int, weights: dict[str, int]) -> dict[str, int]:
    """Proportional allocation via the largest-remainder method."""
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    exact = {k: count * (v / total) for k, v in weights.items()}
    base = {k: math.floor(v) for k, v in exact.items()}
    leftover = count - sum(base.values())
    remainders = sorted(weights, key=lambda k: exact[k] - base[k], reverse=True)
    for k in remainders[:leftover]:
        base[k] += 1
    return base


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def sample_groups(
    items_by_group: dict[str, list[dict[str, Any]]],
    allocations: dict[str, int],
    seed: int,
) -> list[dict[str, Any]]:
    rng = _rng(seed)
    out: list[dict[str, Any]] = []
    for group, k in sorted(allocations.items()):
        items = sorted(items_by_group.get(group, []), key=lambda p: p["pair_id"])
        if k > len(items):
            raise ValueError(f"group {group}: need {k} from {len(items)} available")
        out.extend(rng.sample(items, k))
    out.sort(key=lambda p: (p["group"], p["pair_id"]))
    return out


def build_frame(pool: list[dict[str, Any]], *, seed: int = SEED, n_frame: int = N_FRAME) -> list[dict[str, Any]]:
    """Stratified random candidate frame of n_frame pairs from the universe."""
    by_group: dict[str, list[dict[str, Any]]] = {}
    for p in universe(pool):
        by_group.setdefault(p["group"], []).append(p)
    alloc = allocate(n_frame, {g: len(v) for g, v in by_group.items()})
    frame = sample_groups(by_group, alloc, seed)
    for i, p in enumerate(frame):
        p["candidate_id"] = f"cand_{i:03d}"
    return frame


def select_final(
    eligible: list[str],
    pool: list[dict[str, Any]],
    *,
    seed: int = SEED,
    n_target: int = N_TARGET,
) -> dict[str, Any]:
    """Seeded stratified final draw from the eligible candidate pair ids.

    Returns the selected pair ids plus the allocation table, shortfalls and
    reserve usage for the sampling manifest.
    """
    frame = universe(pool)
    by_group: dict[str, list[dict[str, Any]]] = {}
    for p in frame:
        if p["pair_id"] in set(eligible):
            by_group.setdefault(p["group"], []).append(p)

    el_weights = {g: len(v) for g, v in by_group.items()}
    total_eligible = sum(el_weights.values())
    if total_eligible == 0:
        return {"selected": [], "target": n_target, "alloc": {}, "shortfalls": {}, "eligible_by_group": {}}

    alloc = allocate(n_target, el_weights)
    rng = _rng(seed + 1)
    selected: list[str] = []
    alloc_used = dict(alloc)
    shortfalls: dict[str, int] = {}
    reserve_order: list[dict[str, Any]] = []
    for group, k in sorted(alloc.items()):
        items = sorted(by_group.get(group, []), key=lambda p: p["pair_id"])
        if len(items) >= k:
            chosen = rng.sample(items, k)
        else:
            chosen = items
            shortfalls[group] = k - len(items)
        selected.extend(p["pair_id"] for p in chosen)
        remaining = [p for p in items if p not in chosen]
        reserve_order.extend(sorted(remaining, key=lambda p: p["pair_id"]))
    selected.sort(key=lambda pid: (frame_map(pool, pid)["group"], pid))

    # reserve: deterministic draw from all remaining eligible pairs
    if len(selected) < n_target and reserve_order:
        for p in reserve_order:
            if len(selected) >= n_target:
                break
            if p["pair_id"] not in selected:
                selected.append(p["pair_id"])
    selected.sort()

    return {
        "selected": selected,
        "target": n_target,
        "alloc": alloc_used,
        "shortfalls": shortfalls,
        "eligible_by_group": el_weights,
        "reserve_used": len(selected) >= n_target,
        "final_count": len(selected),
    }


def frame_map(pool: list[dict[str, Any]], pair_id: str) -> dict[str, Any]:
    return next(p for p in universe(pool) if p["pair_id"] == pair_id)


def eligible_counts(eligible: list[str], pool: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pid in eligible:
        g = frame_map(pool, pid)["group"]
        counts[g] = counts.get(g, 0) + 1
    return counts
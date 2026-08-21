"""Text utilities shared by agents and services."""
from __future__ import annotations

import re

_IGNORE_TOKENS = {
    "and", "or", "the", "of", "for", "with", "in", "on", "at", "to", "a", "an",
    "models", "model", "learning", "methods", "method", "systems", "data",
}


def topic_tokens(topic: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+", (topic or "").lower())
        if len(t) > 2 and t not in _IGNORE_TOKENS
    }


def topics_shared(a: list[str], b: list[str]) -> list[str]:
    """Fuzzy shared-topic detection: pairs whose tokens overlap >= 50%."""
    shared: list[str] = []
    seen: set[str] = set()
    for ta in a:
        ka = topic_tokens(ta)
        if not ka:
            continue
        for tb in b:
            kb = topic_tokens(tb)
            if not kb:
                continue
            inter = ka & kb
            if inter and len(inter) / max(1, min(len(ka), len(kb))) >= 0.5:
                label = f"{ta} x {tb}"
                if label.lower() not in seen:
                    seen.add(label.lower())
                    shared.append(label)
    return shared


def shared_topic_count(a: list[str], b: list[str]) -> int:
    return len(topics_shared(a, b))

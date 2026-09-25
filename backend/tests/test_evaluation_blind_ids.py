"""Blind-evaluation id assignment and template blindness."""
from __future__ import annotations

from evaluation.human import export_human_template, make_blind_key
from evaluation.schemas import (
    SystemGap,
    SystemHypothesis,
    SystemIntersection,
    SystemOutput,
)


def _outputs():
    return {
        "c1": {
            "keyword": SystemOutput(
                system="keyword",
                gaps=[SystemGap(description="gap kw 1"), SystemGap(description="gap kw 2")],
                intersections=[SystemIntersection(title="IX kw", description="d")],
                hypotheses=[SystemHypothesis(text="hyp kw")],
            ),
            "pipeline": SystemOutput(
                system="pipeline",
                gaps=[SystemGap(description="gap pl 1")],
                intersections=[
                    SystemIntersection(title="IX pl", description="d"),
                    SystemIntersection(title="IX pl 2", description="d"),
                ],
            ),
        },
        "c2": {
            "pipeline": SystemOutput(
                system="pipeline",
                intersections=[SystemIntersection(title="other", description="d")],
            ),
        },
    }


def test_blind_key_is_reproducible_for_same_seed():
    assert make_blind_key(_outputs(), seed=0) == make_blind_key(_outputs(), seed=0)


def test_blind_key_changes_with_seed():
    assert set(make_blind_key(_outputs(), seed=0)) != set(make_blind_key(_outputs(), seed=1))


def test_blind_key_covers_every_item_exactly_once():
    key = make_blind_key(_outputs())
    assert len(key) == 2 + 1 + 1 + 1 + 2 + 1  # 8 generated items
    assert len(set(key)) == len(key)
    assert all(v["system"] in {"keyword", "pipeline"} for v in key.values())
    assert {v["surface"] for v in key.values()} == {"gap", "intersection", "hypothesis"}


def test_template_never_leaks_system_identity(tmp_path):
    out = tmp_path / "t.csv"
    export_human_template(_outputs(), out, seed=0)
    text = out.read_text(encoding="utf-8")
    assert "system" not in text.splitlines()[0]
    assert "keyword" not in text
    assert "pipeline" not in text
    assert "novelty_confidence" not in text

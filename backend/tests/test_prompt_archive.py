"""Phase 2E: versioned prompt archive."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.prompt_archive import build_prompt_archive

SRC = Path(__file__).resolve().parents[1] / "app" / "agents" / "prompts"


def test_build_prompt_archive_creates_versioned_snapshot(tmp_path):
    result = build_prompt_archive(version="v1", root=tmp_path)
    assert result["status"] == "created"
    dest = tmp_path / "v1"
    assert (dest / "MANIFEST.json").exists()
    assert (dest / "README.md").exists()

    manifest = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["kind"] == "prompt_archive"
    assert manifest["version"] == "v1"

    # every source txt is copied, with the same bytes
    for src in SRC.glob("*.txt"):
        assert (dest / src.name).read_bytes() == src.read_bytes()
        entry = manifest["files"][src.name]
        assert len(entry["sha256"]) == 64
        assert entry["agent"]  # unused or a real agent name, never blank

    # registry attribution is honest
    assert manifest["files"]["hypothesis_generation.txt"]["agent"] == "hypothesis_agent"
    # experiment_design.txt is served by hypothesis agent at runtime
    assert manifest["files"]["experiment_design.txt"]["agent"] == "hypothesis_agent"


def test_build_prompt_archive_is_idempotent_when_identical(tmp_path):
    r1 = build_prompt_archive(version="v1", root=tmp_path)
    r2 = build_prompt_archive(version="v1", root=tmp_path)
    assert r1["status"] == "created"
    assert r2["status"] == "noop_identical"


def test_build_prompt_archive_never_overwrites_divergent_archive(tmp_path):
    # a pre-existing archive with a different manifest must never be overwritten
    dest = tmp_path / "v1"
    dest.mkdir(parents=True)
    (dest / "MANIFEST.json").write_text(
        '{"files": {"different.txt": {"sha256": "x", "agent_version": "unused"}}}',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="different content"):
        build_prompt_archive(version="v1", root=tmp_path)
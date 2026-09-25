"""Versioned prompt archive (Phase 2E).

Copies every production prompt from ``app/agents/prompts/*.txt`` into an
immutable versioned archive directory::

    experiments/prompts/
      v1/
        MANIFEST.json   # version, built_utc, root sha256, per-file {sha256, agent, version}
        README.md       # human-readable summary
        *.txt           # exact copies of the prompts actually used

Seed runs snapshot ``prompt_versions.json`` (sha256 per prompt file) into their
immutable seed directory. The archive keeps the *text* behind those hashes so
any previously executed seed can be re-traced even if ``app/agents/prompts``
changes later. Archive directories are never overwritten: if ``v1`` already
exists with identical content the build is a no-op; if it differs it raises.

Usage::

    python -m evaluation.prompt_archive --version v1 \
        --root experiments/prompts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMPTS_SOURCE = Path(__file__).resolve().parents[1] / "app" / "agents" / "prompts"
DEFAULT_ARCHIVE_ROOT = Path(__file__).resolve().parents[1] / "experiments" / "prompts"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_prompt_archive(
    version: str = "v1",
    root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    """Build (idempotently) a versioned immutable copy of the prompt files."""
    from evaluation.prompt_registry import agent_prompt_versions

    if not PROMPTS_SOURCE.exists():
        raise FileNotFoundError(f"Prompt source dir missing: {PROMPTS_SOURCE}")

    dest = root / version
    dest.mkdir(parents=True, exist_ok=True)

    files: list[Path] = sorted(PROMPTS_SOURCE.glob("*.txt"))
    if not files:
        raise RuntimeError(f"No *.txt prompts found under {PROMPTS_SOURCE}")

    registry = agent_prompt_versions()
    entries: dict[str, dict[str, str]] = {}
    for src in files:
        data = src.read_bytes()
        meta = registry.get(src.name, {})
        entries[src.name] = {
            "sha256": _sha256_bytes(data),
            "version": meta.get("version", "unknown"),
            "agent": meta.get("agent", "unknown"),
        }

    existing = (dest / "MANIFEST.json").exists()
    if existing:
        current = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
        if current.get("files") == entries:
            return {"version": version, "status": "noop_identical", "path": str(dest), "files": len(entries)}
        raise RuntimeError(
            f"Archive {dest} already exists with different content. "
            "Choose a new version tag (immutable archives are never overwritten)."
        )

    for src in files:
        shutil.copyfile(src, dest / src.name)

    manifest = {
        "kind": "prompt_archive",
        "version": version,
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_dir": str(PROMPTS_SOURCE),
        "files": entries,
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    readme = (
        f"# Prompt archive {version}\n\n"
        f"Immutable snapshot of `backend/app/agents/prompts/*.txt` as used by the "
        f"evaluation runs. Built at UTC {manifest['built_utc']}.\n\n"
        f"{len(entries)} prompt files. See MANIFEST.json for per-file sha256 and agent versions.\n\n"
        "Seed directories persist `prompt_versions.json` hashes; resolve the text here.\n"
    )
    (dest / "README.md").write_text(readme, encoding="utf-8")
    return {"version": version, "status": "created", "path": str(dest), "files": len(entries)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.prompt_archive")
    parser.add_argument("--version", default="v1", help="Archive version tag (default: v1).")
    parser.add_argument("--root", default=str(DEFAULT_ARCHIVE_ROOT), help="Archive root dir.")
    args = parser.parse_args(argv)

    result = build_prompt_archive(version=args.version, root=Path(args.root))
    print(
        f"Prompt archive {result['status']}: {result['path']} "
        f"({result['files']} prompt files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""CLI entrypoint for the evaluation framework.

Usage (from the backend directory):

    python -m evaluation.run --dataset evaluation/data/demo_discovery.json \
        --systems keyword,embedding,llm_only,pipeline --out-dir eval_out

Or directly:

    python evaluation/run.py --dataset ... --systems ...

Runs fully offline by default (deterministic mock providers) — no API keys are
required. Set EVALUATION_FORCE_OFFLINE=0 with real provider env vars to use
live providers (at your own risk; see evaluation/README.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `python evaluation/run.py` work regardless of CWD: ensure the backend
# root (which contains both `app/` and `evaluation/`) is importable.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_BACKEND_ROOT), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evaluation.environment import configure_offline_defaults
from evaluation.runner import main

configure_offline_defaults()

if __name__ == "__main__":
    raise SystemExit(main())
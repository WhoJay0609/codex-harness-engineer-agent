#!/usr/bin/env python3
"""SessionStart hook for active harness-engineer auto_harness runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def context_path() -> Path:
    return codex_home() / "harness-engineer-hooks" / "context.json"


def load_context() -> dict[str, Any] | None:
    path = context_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def emit_context(text: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": text,
                }
            },
            sort_keys=True,
        ),
        end="",
    )


def main() -> int:
    context = load_context()
    if not context or context.get("active") is not True:
        return 0
    run_dir = Path(str(context.get("run_dir") or ""))
    if not run_dir.exists():
        return 0
    lines = [
        "Active harness-engineer auto_harness context:",
        f"- Run directory: {run_dir}",
        "- Resume from auto_state.json and results.tsv; do not rely on memory alone.",
        "- Record every completed experiment with record_auto_iteration.py before starting another.",
        "- Use harness_runtime_ctl.py status/stop for detached background control.",
    ]
    emit_context("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stop hook for active harness-engineer auto_harness runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


TERMINAL_DONE = {"goal_met", "budget_exhausted", "failed_with_evidence", "policy_blocked", "environment_blocked"}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def context_path() -> Path:
    return codex_home() / "harness-engineer-hooks" / "context.json"


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def terminal_status(run_dir: Path) -> str | None:
    auto_state = load_json(run_dir / "auto_state.json")
    if not auto_state:
        return None
    state = auto_state.get("state")
    if not isinstance(state, dict):
        return None
    value = state.get("terminal_status")
    return value if isinstance(value, str) else None


def runtime_active(context: dict[str, Any]) -> bool:
    runtime_path = Path(str(context.get("runtime_path") or ""))
    runtime = load_json(runtime_path)
    if not runtime:
        return False
    return runtime.get("active") is True and runtime.get("status") in {"running", "stopping"}


def emit_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, sort_keys=True), end="")


def main() -> int:
    context = load_json(context_path())
    if not context or context.get("active") is not True:
        return 0
    run_dir = Path(str(context.get("run_dir") or ""))
    if not run_dir.exists():
        return 0
    status = terminal_status(run_dir)
    if runtime_active(context) or status not in TERMINAL_DONE:
        emit_block(
            "Continue the current harness-engineer auto_harness run. "
            "Do not rerun the launch wizard. If an experiment just completed, "
            "record it before starting the next one. Use harness_runtime_ctl.py status "
            "or stop if detached background control is needed."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

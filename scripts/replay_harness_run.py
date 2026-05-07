#!/usr/bin/env python3
"""Render a readable replay from harness run artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            row["_line"] = lineno
            rows.append(row)
    return rows


def text(value: Any, limit: int = 500) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    value = str(value).strip()
    if limit > 0 and len(value) > limit:
        return value[: limit - 3] + "..."
    return value


def render_event(row: dict[str, Any]) -> str:
    event_type = row.get("event_type") or row.get("event") or "event"
    label = f"- `{event_type}`"
    agent = row.get("agent_id")
    if agent:
        label += f" by `{agent}`"
    status = row.get("status")
    if status:
        label += f" status=`{status}`"
    details = []
    for key in ["skill", "tool", "action", "observation", "reason", "summary", "error_kind"]:
        if row.get(key):
            details.append(f"{key}: {text(row.get(key), 220)}")
    if details:
        label += "\n  " + "\n  ".join(details)
    return label


def render(run_dir: Path) -> str:
    manifest = load_json(run_dir / "manifest.json")
    metrics = load_json(run_dir / "metrics.json")
    events = load_jsonl(run_dir / "events.jsonl")
    subagents = load_jsonl(run_dir / "subagents.jsonl")
    skills = load_jsonl(run_dir / "skill_invocations.jsonl")
    failures = load_jsonl(run_dir / "failures.jsonl")

    lines = ["# Harness Run Replay", ""]
    if isinstance(manifest, dict):
        lines.extend(
            [
                f"- Experiment: `{manifest.get('experiment_id', '')}`",
                f"- Run: `{manifest.get('run_id', '')}`",
                f"- Goal: {text(manifest.get('goal'), 800)}",
                f"- Termination: `{(manifest.get('termination') or {}).get('status', '')}`",
                "",
            ]
        )

    if subagents:
        lines.extend(["## Subagents", ""])
        for row in subagents:
            if row.get("event") in {"created", "completed", "failed", "blocked", "stopped", "replaced"}:
                lines.append(render_event(row))
        lines.append("")

    if events:
        lines.extend(["## Event Timeline", ""])
        for row in events:
            lines.append(render_event(row))
        lines.append("")

    if skills:
        lines.extend(["## Skill Decisions", ""])
        for row in skills:
            lines.append(render_event(row))
        lines.append("")

    if failures:
        lines.extend(["## Failures", ""])
        for row in failures:
            lines.append(render_event(row))
        lines.append("")

    if isinstance(metrics, dict):
        lines.extend(["## Metrics", "", "```json", json.dumps(metrics, indent=2, sort_keys=True), "```", ""])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a markdown replay for a harness run")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    output = render(args.run_dir)
    if args.output:
        args.output.write_text(output)
    else:
        sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

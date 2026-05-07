#!/usr/bin/env python3
"""Query harness run JSONL artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


ARTIFACTS = [
    "events.jsonl",
    "tool_calls.jsonl",
    "skill_invocations.jsonl",
    "subagents.jsonl",
    "escalations.jsonl",
    "failures.jsonl",
]


def load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            continue
        row["_artifact"] = path.name
        row["_line"] = lineno
        yield row


def row_text(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=False)


def matches(row: dict[str, Any], args: argparse.Namespace) -> bool:
    checks = [
        ("event_type", args.event_type),
        ("agent_id", args.agent),
        ("skill", args.skill),
        ("status", args.status),
        ("tool", args.tool),
    ]
    for key, expected in checks:
        if expected is not None and str(row.get(key)) != expected:
            return False
    if args.field is not None:
        if args.field not in row:
            return False
        value = str(row.get(args.field))
        if args.equals is not None and value != args.equals:
            return False
        if args.contains is not None and args.contains not in value:
            return False
    elif args.equals is not None:
        return False
    if args.contains is not None and args.field is None and args.contains not in row_text(row):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Query harness run artifacts")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--event-type")
    parser.add_argument("--agent")
    parser.add_argument("--skill")
    parser.add_argument("--status")
    parser.add_argument("--tool")
    parser.add_argument("--field")
    parser.add_argument("--equals")
    parser.add_argument("--contains")
    args = parser.parse_args()

    for artifact in ARTIFACTS:
        for row in load_jsonl(args.run_dir / artifact):
            if matches(row, args):
                print(json.dumps(row, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

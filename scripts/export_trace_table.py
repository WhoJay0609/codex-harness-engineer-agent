#!/usr/bin/env python3
"""Export harness run artifacts as flat trace tables."""

from __future__ import annotations

import argparse
import csv
import json
import sys
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

DEFAULT_COLUMNS = [
    "artifact",
    "line",
    "ts",
    "event_id",
    "parent_id",
    "event_type",
    "source",
    "agent_id",
    "role",
    "tool",
    "tool_call_id",
    "skill",
    "status",
    "error_kind",
    "action",
    "observation",
    "reason",
    "summary",
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
        row["_line"] = lineno
        yield row


def shorten(value: Any, limit: int) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    else:
        text = str(value)
    text = text.replace("\n", "\\n")
    if limit > 0 and len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def collect_rows(run_dir: Path, limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for artifact in ARTIFACTS:
        path = run_dir / artifact
        for row in load_jsonl(path):
            flat = {
                column: shorten(row.get(column), limit)
                for column in DEFAULT_COLUMNS
            }
            flat["artifact"] = artifact
            flat["line"] = str(row.get("_line", ""))
            rows.append(flat)
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=DEFAULT_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)


def write_jsonl(rows: list[dict[str, str]]) -> None:
    for row in rows:
        print(json.dumps(row, sort_keys=True, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Export harness trace artifacts as CSV or JSONL")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    parser.add_argument("--max-cell", type=int, default=240)
    args = parser.parse_args()

    rows = collect_rows(args.run_dir, args.max_cell)
    if args.format == "jsonl":
        write_jsonl(rows)
    else:
        write_csv(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

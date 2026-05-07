#!/usr/bin/env python3
"""Summarize harness failure records across run directories."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def collect(run_dirs: list[Path]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        for row in load_jsonl(run_dir / "failures.jsonl"):
            row = dict(row)
            row["run_dir"] = str(run_dir)
            failures.append(row)
    return failures


def print_counter(title: str, counter: Counter[str]) -> None:
    print(f"## {title}")
    if not counter:
        print("No records.\n")
        return
    print("| value | count |")
    print("|---|---:|")
    for value, count in counter.most_common():
        print(f"| {value or '(missing)'} | {count} |")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize harness failures")
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args()

    missing = [str(path) for path in args.run_dirs if not path.exists()]
    if missing:
        print(f"missing run directories: {', '.join(missing)}", file=sys.stderr)
        return 1

    failures = collect(args.run_dirs)
    if args.json:
        print(json.dumps(failures, indent=2, sort_keys=True))
        return 0

    print(f"# Failure Summary\n\nTotal failures: {len(failures)}\n")
    print_counter("By Failure Type", Counter(str(row.get("failure_type", "")) for row in failures))
    print_counter("By Harness Gap", Counter(str(row.get("harness_gap", "")) for row in failures))
    print_counter("By Root Cause", Counter(str(row.get("root_cause", "")) for row in failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())

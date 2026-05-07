#!/usr/bin/env python3
"""Compare metrics across harness-engineer run directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else {}


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(flatten(value, name))
        elif isinstance(value, (str, int, float, bool)) or value is None:
            out[name] = value
    return out


def run_label(run_dir: Path, manifest: dict[str, Any]) -> str:
    run_id = manifest.get("run_id")
    if run_id:
        return str(run_id)
    return run_dir.name


def collect(run_dirs: list[Path]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    labels: list[str] = []
    rows: dict[str, dict[str, Any]] = {}
    for run_dir in run_dirs:
        manifest = load_json(run_dir / "manifest.json")
        metrics = flatten(load_json(run_dir / "metrics.json"))
        label = run_label(run_dir, manifest)
        labels.append(label)
        rows[label] = {
            "experiment_id": manifest.get("experiment_id", ""),
            "termination.status": (manifest.get("termination") or {}).get("status", ""),
            **metrics,
        }
    return labels, rows


def print_markdown(labels: list[str], rows: dict[str, dict[str, Any]]) -> None:
    keys = sorted({key for row in rows.values() for key in row})
    print("| metric | " + " | ".join(labels) + " |")
    print("|---|" + "|".join("---" for _ in labels) + "|")
    for key in keys:
        values = [str(rows[label].get(key, "")) for label in labels]
        print("| " + key + " | " + " | ".join(values) + " |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare harness run metrics")
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args()

    missing = [str(path) for path in args.run_dirs if not path.exists()]
    if missing:
        print(f"missing run directories: {', '.join(missing)}", file=sys.stderr)
        return 1

    labels, rows = collect(args.run_dirs)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_markdown(labels, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())

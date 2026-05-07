#!/usr/bin/env python3
"""Run harness-engineer regression eval packs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALS = ROOT / "evals" / "cases"
VALIDATOR = ROOT / "scripts" / "validate_harness_trace.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def run_case(case_dir: Path) -> tuple[bool, str]:
    expected_path = case_dir / "expected.json"
    expected = load_json(expected_path)
    expect = expected.get("expect")
    contains = expected.get("contains")
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(case_dir)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    passed = proc.returncode == 0
    if expect == "pass":
        ok = passed
    elif expect == "fail":
        ok = not passed
    else:
        return False, f"{case_dir.name}: expected.json expect must be pass or fail"
    if ok and contains:
        ok = str(contains) in proc.stdout
    status = "PASS" if ok else "FAIL"
    return ok, f"{status}: {case_dir.name}\n{proc.stdout.strip()}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run harness-engineer eval packs")
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_EVALS)
    args = parser.parse_args()

    case_dirs = [
        path for path in sorted(args.cases_dir.iterdir())
        if path.is_dir() and (path / "expected.json").exists()
    ]
    if not case_dirs:
        print(f"FAIL: no eval cases found under {args.cases_dir}")
        return 1

    failures = 0
    for case_dir in case_dirs:
        ok, output = run_case(case_dir)
        print(output)
        if not ok:
            failures += 1
    if failures:
        print(f"FAIL: {failures}/{len(case_dirs)} harness evals failed")
        return 1
    print(f"PASS: {len(case_dirs)} harness evals passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

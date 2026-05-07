#!/usr/bin/env python3
"""Shared helpers for harness-engineer auto_harness scripts."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTO_RESULTS_HEADER = ["iteration", "commit", "metric", "delta", "guard", "status", "description"]
AUTO_ROW_STATUSES = {
    "baseline",
    "keep",
    "discard",
    "crash",
    "no-op",
    "blocked",
    "refine",
    "pivot",
    "search",
    "drift",
}
AUTO_NON_BASELINE_STATUSES = AUTO_ROW_STATUSES - {"baseline"}
RUN_TERMINAL_STATUSES = {
    "goal_met",
    "budget_exhausted",
    "policy_blocked",
    "environment_blocked",
    "user_decision_needed",
    "failed_with_evidence",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    atomic_write(path, text)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp_name = handle.name
    os.replace(tmp_name, path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip("\n") + "\n")


def read_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    header_seen = False
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if not header_seen:
            header_seen = True
            if cells != AUTO_RESULTS_HEADER:
                raise ValueError(f"{path} header must be {'/'.join(AUTO_RESULTS_HEADER)}")
            continue
        if len(cells) != len(AUTO_RESULTS_HEADER):
            raise ValueError(f"{path} row has {len(cells)} columns, expected {len(AUTO_RESULTS_HEADER)}")
        rows.append(dict(zip(AUTO_RESULTS_HEADER, cells)))
    return rows


def coerce_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric, not boolean")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError(f"{name} must be numeric")


def format_metric(value: float) -> str:
    return f"{value:.12g}"


def is_improved(candidate: float, best: float, direction: str) -> bool:
    if direction == "higher":
        return candidate > best
    if direction == "lower":
        return candidate < best
    raise ValueError("direction must be higher or lower")


def parse_metric_output(output: str, verify_format: str = "scalar", primary_metric_key: str | None = None) -> float:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise ValueError("verify output is empty")
    final_line = lines[-1]
    if verify_format == "metrics_json":
        if not primary_metric_key:
            raise ValueError("primary_metric_key is required for metrics_json verify output")
        payload = json.loads(final_line)
        if not isinstance(payload, dict):
            raise ValueError("final verify output line must be a JSON object")
        if primary_metric_key not in payload:
            raise ValueError(f"metrics_json output missing key {primary_metric_key!r}")
        return coerce_float(payload[primary_metric_key], primary_metric_key)
    if verify_format != "scalar":
        raise ValueError("verify_format must be scalar or metrics_json")
    try:
        return float(final_line)
    except ValueError:
        match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", final_line)
        if not match:
            raise ValueError("final verify output line does not contain a numeric scalar")
        return float(match.group(0))


def git_commit(cwd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return "-"
    commit = proc.stdout.strip()
    return commit if proc.returncode == 0 and commit else "-"


def shell_run(command: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=merged_env,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def load_run_state(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = read_json(run_dir / "manifest.json")
    auto_state = read_json(run_dir / "auto_state.json")
    context = read_json(run_dir / "context.json")
    return manifest, auto_state, context


def next_event_id(run_dir: Path) -> str:
    events_path = run_dir / "events.jsonl"
    count = 0
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            if line.strip():
                count += 1
    return f"evt-{count + 1:04d}"

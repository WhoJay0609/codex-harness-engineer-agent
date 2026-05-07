#!/usr/bin/env python3
"""Record one auto_harness iteration and synchronize state artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_harness_common import (
    AUTO_NON_BASELINE_STATUSES,
    RUN_TERMINAL_STATUSES,
    append_jsonl,
    append_line,
    coerce_float,
    format_metric,
    git_commit,
    is_improved,
    load_run_state,
    next_event_id,
    read_results,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a harness-engineer auto_harness iteration")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--status", choices=sorted(AUTO_NON_BASELINE_STATUSES), required=True)
    parser.add_argument("--metric", type=float, default=None)
    parser.add_argument("--commit", default=None)
    parser.add_argument("--guard", choices=["pass", "fail", "-"], default="-")
    parser.add_argument("--description", required=True)
    parser.add_argument("--terminal-status", choices=sorted(RUN_TERMINAL_STATUSES), default=None)
    parser.add_argument("--failure-kind", default=None)
    return parser.parse_args()


def next_iteration(run_dir: Path, state_iteration: int) -> int:
    rows = read_results(run_dir / "results.tsv")
    integer_rows = [int(row["iteration"]) for row in rows if row.get("iteration", "").isdigit()]
    return max(integer_rows + [state_iteration]) + 1


def append_summary(run_dir: Path, iteration: int, status: str, metric: float, description: str) -> None:
    summary_path = run_dir / "summary.md"
    existing = summary_path.read_text(encoding="utf-8") if summary_path.exists() else "# Auto Harness Run\n"
    existing = existing.rstrip() + f"\n\n- Iteration {iteration}: `{status}` metric={format_metric(metric)} - {description}\n"
    summary_path.write_text(existing, encoding="utf-8")
    replay_path = run_dir / "replay.md"
    replay = replay_path.read_text(encoding="utf-8") if replay_path.exists() else "# Replay\n"
    replay = replay.rstrip() + f"\n- Iteration {iteration}: {status}, metric {format_metric(metric)}.\n"
    replay_path.write_text(replay, encoding="utf-8")


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    manifest, auto_state, context = load_run_state(run_dir)
    if manifest.get("mode") != "auto_harness" or auto_state.get("mode") != "auto_harness":
        print("run_dir is not an auto_harness run", file=sys.stderr)
        return 2

    config = auto_state.get("config") if isinstance(auto_state.get("config"), dict) else {}
    state = auto_state.get("state") if isinstance(auto_state.get("state"), dict) else {}
    direction = str(config.get("direction", ""))
    if direction not in {"higher", "lower"}:
        print("auto_state.json config.direction must be higher or lower", file=sys.stderr)
        return 2

    previous_metric = coerce_float(state.get("current_metric"), "state.current_metric")
    best_metric = coerce_float(state.get("best_metric"), "state.best_metric")
    metric = args.metric if args.metric is not None else previous_metric
    delta = metric - previous_metric
    iteration = next_iteration(run_dir, int(state.get("iteration", 0)))
    primary_repo = Path(str(context.get("primary_repo") or ".")).resolve()
    commit = args.commit or git_commit(primary_repo)
    terminal_status = args.terminal_status or str(state.get("terminal_status") or "user_decision_needed")

    if args.status == "keep" and is_improved(metric, best_metric, direction):
        best_metric = metric

    append_line(
        run_dir / "results.tsv",
        "\t".join(
            [
                str(iteration),
                commit,
                format_metric(metric),
                format_metric(delta),
                args.guard,
                args.status,
                args.description.replace("\t", " "),
            ]
        ),
    )

    state["iteration"] = iteration
    state["current_metric"] = metric
    state["best_metric"] = best_metric
    state["last_status"] = args.status
    state["terminal_status"] = terminal_status
    auto_state["state"] = state
    manifest["termination"] = {
        "status": terminal_status,
        "reason": f"latest auto_harness iteration status: {args.status}",
    }
    write_json(run_dir / "auto_state.json", auto_state)
    write_json(run_dir / "manifest.json", manifest)
    write_json(
        run_dir / "metrics.json",
        {
            "metric": config.get("metric"),
            "direction": direction,
            "baseline": state.get("baseline_metric"),
            "current": metric,
            "best": best_metric,
            "iteration": iteration,
            "last_status": args.status,
        },
    )

    ts = utc_now()
    checkpoint_id = next_event_id(run_dir)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": checkpoint_id,
            "parent_id": None,
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "checkpoint",
            "status": args.status,
            "summary": args.description,
        },
    )
    metric_event_id = next_event_id(run_dir)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": metric_event_id,
            "parent_id": checkpoint_id,
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "metric",
            "status": "completed",
            "summary": f"iteration {iteration} metric",
            "metric": config.get("metric"),
            "value": metric,
        },
    )
    if args.status in {"crash", "blocked"} or args.failure_kind:
        failure_kind = args.failure_kind or args.status
        append_jsonl(
            run_dir / "failures.jsonl",
            {
                "ts": ts,
                "failure_type": failure_kind,
                "root_cause": args.description,
                "recoverable": args.status != "blocked",
                "harness_gap": None,
                "evidence": ["results.tsv", "events.jsonl"],
                "next_action": "inspect latest iteration",
            },
        )
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "event_version": 2,
                "event_id": next_event_id(run_dir),
                "parent_id": metric_event_id,
                "ts": ts,
                "source": "orchestrator",
                "agent_id": "orchestrator",
                "role": "Professor Orchestrator",
                "event_type": "failure",
                "status": "failed",
                "error_kind": failure_kind,
                "summary": args.description,
            },
        )
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": next_event_id(run_dir),
            "parent_id": metric_event_id,
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "termination",
            "status": terminal_status,
            "summary": f"recorded iteration {iteration}",
        },
    )
    append_summary(run_dir, iteration, args.status, metric, args.description)
    print(f"recorded iteration {iteration}: {args.status} metric={format_metric(metric)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

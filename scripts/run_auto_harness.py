#!/usr/bin/env python3
"""Run a foreground command-driven auto_harness loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_harness_common import (
    format_metric,
    is_improved,
    load_run_state,
    parse_metric_output,
    shell_run,
)
from record_auto_iteration import main as record_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a foreground harness-engineer auto_harness loop")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--iteration-command", required=True, help="shell command that performs one focused change")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--rollback-command", default=None, help="optional command run after discard/crash")
    parser.add_argument("--stop-after-keep", action="store_true")
    return parser.parse_args()


def call_record(argv: list[str]) -> int:
    old_argv = sys.argv
    try:
        sys.argv = ["record_auto_iteration.py", *argv]
        return int(record_main())
    finally:
        sys.argv = old_argv


def main() -> int:
    args = parse_args()
    if args.iterations < 1:
        print("--iterations must be >= 1", file=sys.stderr)
        return 2
    run_dir = args.run_dir.resolve()
    final_status = "budget_exhausted"

    for _ in range(args.iterations):
        _manifest, auto_state, context = load_run_state(run_dir)
        config = auto_state.get("config") if isinstance(auto_state.get("config"), dict) else {}
        state = auto_state.get("state") if isinstance(auto_state.get("state"), dict) else {}
        direction = str(config.get("direction", ""))
        verify = str(config.get("verify") or "")
        guard = str(config.get("guard") or "")
        verify_format = str(config.get("verify_format") or "scalar")
        primary_metric_key = config.get("primary_metric_key")
        run_mode = str(config.get("run_mode") or "foreground")
        if run_mode != "foreground":
            print("run_auto_harness.py only supports foreground runs", file=sys.stderr)
            return 2
        if direction not in {"higher", "lower"} or not verify:
            print("auto_state.json config must include direction and verify", file=sys.stderr)
            return 2

        primary_repo = Path(str(context.get("primary_repo") or ".")).resolve()
        verify_cwd = Path(str(context.get("verify_cwd") or primary_repo)).resolve()
        iteration = int(state.get("iteration", 0)) + 1
        env = {
            "HARNESS_RUN_DIR": str(run_dir),
            "HARNESS_ITERATION": str(iteration),
            "HARNESS_PRIMARY_REPO": str(primary_repo),
        }

        change_proc = shell_run(args.iteration_command, primary_repo, env=env)
        if change_proc.returncode != 0:
            description = f"iteration command failed: {first_line(change_proc.stdout)}"
            if args.rollback_command:
                shell_run(args.rollback_command, primary_repo, env=env)
            call_record(
                [
                    "--run-dir",
                    str(run_dir),
                    "--status",
                    "crash",
                    "--guard",
                    "-",
                    "--description",
                    description,
                    "--failure-kind",
                    "iteration_command_failed",
                    "--terminal-status",
                    "failed_with_evidence",
                ]
            )
            final_status = "failed_with_evidence"
            continue

        verify_proc = shell_run(verify, verify_cwd, env=env)
        if verify_proc.returncode != 0:
            description = f"verify command failed: {first_line(verify_proc.stdout)}"
            if args.rollback_command:
                shell_run(args.rollback_command, primary_repo, env=env)
            call_record(
                [
                    "--run-dir",
                    str(run_dir),
                    "--status",
                    "crash",
                    "--guard",
                    "-",
                    "--description",
                    description,
                    "--failure-kind",
                    "verify_command_failed",
                    "--terminal-status",
                    "failed_with_evidence",
                ]
            )
            final_status = "failed_with_evidence"
            continue

        try:
            metric = parse_metric_output(
                verify_proc.stdout,
                verify_format=verify_format,
                primary_metric_key=str(primary_metric_key) if primary_metric_key else None,
            )
        except Exception as exc:
            description = f"could not parse verify metric: {exc}"
            if args.rollback_command:
                shell_run(args.rollback_command, primary_repo, env=env)
            call_record(
                [
                    "--run-dir",
                    str(run_dir),
                    "--status",
                    "crash",
                    "--guard",
                    "-",
                    "--description",
                    description,
                    "--failure-kind",
                    "metric_parse_failed",
                    "--terminal-status",
                    "failed_with_evidence",
                ]
            )
            final_status = "failed_with_evidence"
            continue

        best = float(state.get("best_metric"))
        improved = is_improved(metric, best, direction)
        guard_status = "-"
        guard_passed = True
        if guard:
            guard_proc = shell_run(guard, verify_cwd, env=env)
            guard_passed = guard_proc.returncode == 0
            guard_status = "pass" if guard_passed else "fail"

        if improved and guard_passed:
            status = "keep"
            description = f"metric improved to {format_metric(metric)}"
        else:
            status = "discard"
            reason = "guard failed" if not guard_passed else f"metric did not improve: {format_metric(metric)}"
            description = reason
            if args.rollback_command:
                rollback_proc = shell_run(args.rollback_command, primary_repo, env=env)
                description += f"; rollback exit={rollback_proc.returncode}"

        terminal_status = "goal_met" if status == "keep" and args.stop_after_keep else "budget_exhausted"
        record_args = [
            "--run-dir",
            str(run_dir),
            "--status",
            status,
            "--metric",
            str(metric),
            "--guard",
            guard_status,
            "--description",
            description,
            "--terminal-status",
            terminal_status,
        ]
        result = call_record(record_args)
        if result != 0:
            return result
        final_status = terminal_status
        if args.stop_after_keep and status == "keep":
            break

    print(f"auto_harness foreground loop finished with {final_status}")
    return 0


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:200]
    return "no output"


if __name__ == "__main__":
    raise SystemExit(main())

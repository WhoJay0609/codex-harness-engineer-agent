#!/usr/bin/env python3
"""Initialize a harness-engineer auto_harness run directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from auto_harness_common import (
    AUTO_RESULTS_HEADER,
    append_jsonl,
    append_line,
    format_metric,
    git_commit,
    utc_now,
    write_json,
)


DEFAULT_ROLES = [
    "Professor Orchestrator",
    "Runner Coordinator",
    "Verifier / Evidence Auditor",
]
FORBIDDEN_SKILLS = ["codex-autoresearch", "multi-agent", "expert-debate"]
SUBAGENT_EXECUTION_MODES = ["auto", "runtime_subagents", "inline_expert_memos"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a harness-engineer auto_harness run")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default="auto-harness")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--success-criteria", action="append", default=[])
    parser.add_argument("--scope", required=True)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--direction", choices=["higher", "lower"], required=True)
    parser.add_argument("--verify", required=True)
    parser.add_argument("--guard", default="")
    parser.add_argument("--run-mode", choices=["foreground", "background"], default="foreground")
    parser.add_argument("--primary-repo", type=Path, default=Path.cwd())
    parser.add_argument("--verify-cwd", type=Path, default=None)
    parser.add_argument("--verify-format", choices=["scalar", "metrics_json"], default="scalar")
    parser.add_argument("--primary-metric-key", default=None)
    parser.add_argument("--baseline-metric", type=float, required=True)
    parser.add_argument("--baseline-commit", default=None)
    parser.add_argument("--baseline-description", default="baseline measurement")
    parser.add_argument("--terminal-status", default="user_decision_needed")
    parser.add_argument(
        "--subagent-execution-mode",
        choices=SUBAGENT_EXECUTION_MODES,
        default="auto",
        help="auto chooses runtime_subagents when --runtime-subagent is present; otherwise inline_expert_memos",
    )
    parser.add_argument(
        "--runtime-subagent",
        action="append",
        default=[],
        metavar="ROLE=RUNTIME_ID",
        help="record a real runtime subagent handle, e.g. 'Verifier / Evidence Auditor=019...' (repeatable)",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def ensure_empty_or_force(run_dir: Path, force: bool) -> None:
    if not run_dir.exists():
        return
    existing = [path for path in run_dir.iterdir()]
    if existing and not force:
        raise SystemExit(f"{run_dir} is not empty; use --force to overwrite auto_harness files")


def write_empty_files(run_dir: Path) -> None:
    for name in ["escalations.jsonl", "tool_calls.jsonl", "failures.jsonl", "harness_gap_log.jsonl"]:
        (run_dir / name).write_text("")


def role_to_agent_id(role: str) -> str:
    return role.lower().replace(" / ", "-").replace(" ", "-")


def parse_runtime_subagents(values: list[str]) -> dict[str, str]:
    specs: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("--runtime-subagent must use ROLE=RUNTIME_ID")
        role, runtime_agent_id = (part.strip() for part in value.split("=", 1))
        if not role or not runtime_agent_id:
            raise SystemExit("--runtime-subagent requires non-empty ROLE and RUNTIME_ID")
        if role in specs:
            raise SystemExit(f"duplicate --runtime-subagent role: {role}")
        specs[role] = runtime_agent_id
    return specs


def choose_subagent_execution_mode(args: argparse.Namespace, runtime_specs: dict[str, str]) -> str:
    if args.subagent_execution_mode == "auto":
        return "runtime_subagents" if runtime_specs else "inline_expert_memos"
    if args.subagent_execution_mode == "runtime_subagents" and not runtime_specs:
        raise SystemExit("--subagent-execution-mode runtime_subagents requires at least one --runtime-subagent")
    if args.subagent_execution_mode == "inline_expert_memos" and runtime_specs:
        raise SystemExit("--runtime-subagent requires --subagent-execution-mode runtime_subagents or auto")
    return str(args.subagent_execution_mode)


def subagent_records(
    roles: list[str],
    execution_mode: str,
    runtime_specs: dict[str, str],
    blocked_reason: str | None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for role in roles:
        agent_id = role_to_agent_id(role)
        created = {
            "agent_id": agent_id,
            "event": "created",
            "role": role,
            "reason": "auto_harness core role initialized by helper script",
            "allowed_skills": ["harness-engineer"],
            "forbidden_skills": FORBIDDEN_SKILLS,
            "required_skill_check": True,
            "runtime_agent_id": runtime_specs.get(role),
            "thread_id": None,
            "runtime_blocked_reason": None if execution_mode == "runtime_subagents" else blocked_reason,
        }
        if execution_mode == "runtime_subagents":
            created["status"] = "active"
        records.append(created)
        records.append(
            {
                "agent_id": agent_id,
                "event": "stopped",
                "status": "completed" if execution_mode == "runtime_subagents" else "stopped",
                "role": role,
                "stop_reason": (
                    "runtime subagent completed assigned verification scope"
                    if execution_mode == "runtime_subagents"
                    else "initial helper records inline expert fallback; live execution stays in current session"
                ),
            }
        )
    return records


def main() -> int:
    args = parse_args()
    if args.terminal_status not in {
        "goal_met",
        "budget_exhausted",
        "policy_blocked",
        "environment_blocked",
        "user_decision_needed",
        "failed_with_evidence",
    }:
        print("terminal status must be a valid harness terminal status", file=sys.stderr)
        return 2

    run_dir = args.run_dir.resolve()
    primary_repo = args.primary_repo.resolve()
    verify_cwd = (args.verify_cwd or primary_repo).resolve()
    ensure_empty_or_force(run_dir, args.force)
    run_dir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or run_dir.name
    baseline_commit = args.baseline_commit or git_commit(primary_repo)
    blocked_reason = "auto_harness helper initialized without live runtime subagent handles"
    runtime_specs = parse_runtime_subagents(args.runtime_subagent)
    subagent_execution_mode = choose_subagent_execution_mode(args, runtime_specs)
    initial_roles = list(runtime_specs.keys()) if subagent_execution_mode == "runtime_subagents" else DEFAULT_ROLES

    manifest = {
        "schema_version": 2,
        "experiment_id": args.experiment_id,
        "run_id": run_id,
        "mode": "auto_harness",
        "goal": args.goal,
        "success_criteria": args.success_criteria or ["auto_harness artifacts validate"],
        "team_policy": {
            "mode": "internal_team",
            "task_class": "execution",
            "expert_library_version": "harness-experts.v3",
            "reason": "auto_harness loop needs execution and verification roles",
            "initial_roles": initial_roles,
            "single_agent_exception": False,
            "subagent_execution_mode": subagent_execution_mode,
            "subagent_runtime_blocked_reason": None if subagent_execution_mode == "runtime_subagents" else blocked_reason,
            "skill_policy": "external_domain_allowed_by_allowlist",
            "reserved_orchestration_policy": "explicit_user_request_only",
        },
        "startup_cleanup": {
            "summary": "no runtime cleanup performed by init helper",
            "closed_count": 0,
            "skipped_count": 0,
            "unavailable_count": 0,
        },
        "termination": {
            "status": args.terminal_status,
            "reason": "initialized auto_harness run state",
        },
    }
    auto_state = {
        "version": 1,
        "mode": "auto_harness",
        "config": {
            "goal": args.goal,
            "scope": args.scope,
            "metric": args.metric,
            "direction": args.direction,
            "verify": args.verify,
            "guard": args.guard,
            "run_mode": args.run_mode,
            "verify_format": args.verify_format,
            "primary_metric_key": args.primary_metric_key,
        },
        "state": {
            "iteration": 0,
            "baseline_metric": args.baseline_metric,
            "current_metric": args.baseline_metric,
            "best_metric": args.baseline_metric,
            "last_status": "baseline",
            "terminal_status": args.terminal_status,
        },
    }
    context = {
        "version": 1,
        "artifact_root": str(run_dir),
        "primary_repo": str(primary_repo),
        "scope": args.scope,
        "verify_cwd": str(verify_cwd),
        "run_mode": args.run_mode,
    }
    metrics = {
        "metric": args.metric,
        "direction": args.direction,
        "baseline": args.baseline_metric,
        "current": args.baseline_metric,
        "best": args.baseline_metric,
        "iteration": 0,
        "last_status": "baseline",
    }

    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "auto_state.json", auto_state)
    write_json(run_dir / "context.json", context)
    write_json(run_dir / "metrics.json", metrics)
    write_empty_files(run_dir)

    for record in subagent_records(initial_roles, subagent_execution_mode, runtime_specs, blocked_reason):
        append_jsonl(run_dir / "subagents.jsonl", record)
    for role in initial_roles:
        agent_id = role_to_agent_id(role)
        append_jsonl(
            run_dir / "skill_invocations.jsonl",
            {
                "agent_id": agent_id,
                "skill": "harness-engineer",
                "reason": "initialize auto_harness artifact contract",
                "allowed": True,
                "used": True,
                "output_artifact": "auto_state.json",
                "blocked_reason": None,
            },
        )

    append_line(run_dir / "results.tsv", "\t".join(AUTO_RESULTS_HEADER))
    append_line(
        run_dir / "results.tsv",
        "\t".join(
            [
                "0",
                baseline_commit,
                format_metric(args.baseline_metric),
                "0",
                "-",
                "baseline",
                args.baseline_description.replace("\t", " "),
            ]
        ),
    )
    ts = utc_now()
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": "evt-0001",
            "parent_id": None,
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "plan",
            "status": "completed",
            "summary": "initialized auto_harness run",
        },
    )
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": "evt-0002",
            "parent_id": "evt-0001",
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "metric",
            "status": "completed",
            "summary": "recorded baseline metric",
            "metric": args.metric,
            "value": args.baseline_metric,
        },
    )
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "event_version": 2,
            "event_id": "evt-0003",
            "parent_id": "evt-0002",
            "ts": ts,
            "source": "orchestrator",
            "agent_id": "orchestrator",
            "role": "Professor Orchestrator",
            "event_type": "termination",
            "status": args.terminal_status,
            "summary": "initial run state written",
        },
    )
    (run_dir / "summary.md").write_text(f"# Auto Harness Run\n\nInitialized `{run_id}`.\n", encoding="utf-8")
    (run_dir / "replay.md").write_text(
        f"# Replay\n\n- Initialized auto_harness run `{run_id}` with baseline {format_metric(args.baseline_metric)}.\n",
        encoding="utf-8",
    )
    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

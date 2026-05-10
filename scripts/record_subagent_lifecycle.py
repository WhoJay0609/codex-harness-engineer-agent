#!/usr/bin/env python3
"""Append direct runtime subagent lifecycle records to a harness run."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from auto_harness_common import append_jsonl, next_event_id, utc_now


FORBIDDEN_SKILLS = ["codex-autoresearch", "multi-agent", "expert-debate"]
TERMINAL_EVENTS = {"completed", "stopped", "blocked", "replaced", "failed"}


def role_to_agent_id(role: str) -> str:
    return role.lower().replace(" / ", "-").replace(" ", "-")


def is_placeholder_runtime_handle(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        return True
    if "<" in stripped or ">" in stripped:
        return True
    return lowered in {
        "todo",
        "tbd",
        "none",
        "null",
        "placeholder",
        "runtime_agent_id",
        "thread_id",
        "agent-abc123",
        "rt-placeholder",
    } or lowered.startswith(("placeholder-", "todo-", "fake-"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record runtime subagent lifecycle events")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--event", choices=["created", "completed", "stopped", "blocked", "replaced", "failed"], required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--runtime-agent-id", default=None)
    parser.add_argument("--thread-id", default=None)
    parser.add_argument("--reason", default=None)
    parser.add_argument("--stop-reason", default=None)
    parser.add_argument("--scope", default=None)
    parser.add_argument("--allowed-skill", action="append", default=[])
    parser.add_argument("--forbidden-skill", action="append", default=[])
    parser.add_argument("--replacement-agent-id", default=None)
    parser.add_argument("--replacement-runtime-agent-id", default=None)
    parser.add_argument("--replacement-thread-id", default=None)
    return parser.parse_args()


def ensure_run_dir(run_dir: Path) -> None:
    if not run_dir.exists():
        raise SystemExit(f"{run_dir} does not exist")
    if not run_dir.is_dir():
        raise SystemExit(f"{run_dir} is not a directory")


def require_concrete_handle(runtime_agent_id: str | None, thread_id: str | None) -> None:
    if is_placeholder_runtime_handle(runtime_agent_id) or is_placeholder_runtime_handle(thread_id):
        raise SystemExit("runtime_agent_id/thread_id must be concrete spawn_agent return values, not placeholders")
    if not runtime_agent_id and not thread_id:
        raise SystemExit("--event created requires --runtime-agent-id or --thread-id returned by spawn_agent")


def created_record(args: argparse.Namespace, agent_id: str, ts: str) -> dict[str, Any]:
    require_concrete_handle(args.runtime_agent_id, args.thread_id)
    allowed = ["harness-engineer"]
    allowed.extend(skill for skill in args.allowed_skill if skill not in allowed)
    forbidden = list(FORBIDDEN_SKILLS)
    forbidden.extend(skill for skill in args.forbidden_skill if skill not in forbidden)
    return {
        "ts": ts,
        "agent_id": agent_id,
        "event": "created",
        "status": "active",
        "role": args.role,
        "scope": args.scope,
        "creation_api": "spawn_agent",
        "reason": args.reason or "direct runtime team member created by main Codex orchestrator",
        "allowed_skills": allowed,
        "forbidden_skills": forbidden,
        "required_skill_check": True,
        "runtime_agent_id": args.runtime_agent_id,
        "thread_id": args.thread_id,
        "runtime_blocked_reason": None,
        "runtime_blocked_category": None,
    }


def terminal_record(args: argparse.Namespace, agent_id: str, ts: str) -> dict[str, Any]:
    if not args.stop_reason:
        raise SystemExit(f"--event {args.event} requires --stop-reason")
    record: dict[str, Any] = {
        "ts": ts,
        "agent_id": agent_id,
        "event": args.event,
        "status": args.event,
        "role": args.role,
        "stop_reason": args.stop_reason,
    }
    if args.event == "replaced":
        if args.replacement_runtime_agent_id and is_placeholder_runtime_handle(args.replacement_runtime_agent_id):
            raise SystemExit("--replacement-runtime-agent-id must be concrete, not a placeholder")
        if args.replacement_thread_id and is_placeholder_runtime_handle(args.replacement_thread_id):
            raise SystemExit("--replacement-thread-id must be concrete, not a placeholder")
        if args.replacement_agent_id:
            record["replacement_agent_id"] = args.replacement_agent_id
        if args.replacement_runtime_agent_id:
            record["replacement_runtime_agent_id"] = args.replacement_runtime_agent_id
        if args.replacement_thread_id:
            record["replacement_thread_id"] = args.replacement_thread_id
    return record


def event_record(args: argparse.Namespace, agent_id: str, lifecycle_record: dict[str, Any], ts: str) -> dict[str, Any]:
    event_id = next_event_id(args.run_dir)
    if args.event == "created":
        return {
            "event_version": 2,
            "event_id": event_id,
            "parent_id": None,
            "ts": ts,
            "source": "runtime",
            "agent_id": agent_id,
            "role": args.role,
            "event_type": "subagent_created",
            "status": "active",
            "summary": "spawn_agent created runtime subagent",
            "runtime_agent_id": lifecycle_record.get("runtime_agent_id"),
            "thread_id": lifecycle_record.get("thread_id"),
        }
    return {
        "event_version": 2,
        "event_id": event_id,
        "parent_id": None,
        "ts": ts,
        "source": "runtime",
        "agent_id": agent_id,
        "role": args.role,
        "event_type": "subagent_terminal",
        "status": args.event,
        "summary": f"runtime subagent {args.event}",
        "reason": lifecycle_record.get("stop_reason"),
    }


def main() -> int:
    args = parse_args()
    args.run_dir = args.run_dir.resolve()
    ensure_run_dir(args.run_dir)
    agent_id = args.agent_id or role_to_agent_id(args.role)
    ts = utc_now()

    if args.event == "created":
        record = created_record(args, agent_id, ts)
    else:
        record = terminal_record(args, agent_id, ts)

    append_jsonl(args.run_dir / "subagents.jsonl", record)
    append_jsonl(args.run_dir / "events.jsonl", event_record(args, agent_id, record, ts))
    if args.event == "created":
        append_jsonl(
            args.run_dir / "skill_invocations.jsonl",
            {
                "agent_id": agent_id,
                "skill": "harness-engineer",
                "reason": "direct runtime team lifecycle record",
                "allowed": True,
                "used": True,
                "output_artifact": "subagents.jsonl",
                "blocked_reason": None,
            },
        )
    print(str(args.run_dir / "subagents.jsonl"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

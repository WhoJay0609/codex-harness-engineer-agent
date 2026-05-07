#!/usr/bin/env python3
"""Detached runtime controller for harness-engineer auto_harness runs."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from auto_harness_common import read_json, utc_now, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Control a detached harness-engineer auto_harness runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-launch", help="write launch.json")
    add_launch_args(create)

    launch = subparsers.add_parser("launch", help="write launch.json and start detached runtime")
    add_launch_args(launch)

    start = subparsers.add_parser("start", help="start detached runtime from existing launch.json")
    start.add_argument("--run-dir", type=Path, required=True)
    start.add_argument("--launch-path", type=Path, default=None)

    run = subparsers.add_parser("run", help="internal runtime loop")
    run.add_argument("--run-dir", type=Path, required=True)
    run.add_argument("--launch-path", type=Path, default=None)

    status = subparsers.add_parser("status", help="inspect runtime status")
    status.add_argument("--run-dir", type=Path, required=True)

    stop = subparsers.add_parser("stop", help="request stop and terminate detached runtime if active")
    stop.add_argument("--run-dir", type=Path, required=True)
    stop.add_argument("--grace-seconds", type=float, default=5.0)

    return parser.parse_args()


def add_launch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--iteration-command", required=True)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--rollback-command", default=None)
    parser.add_argument("--stop-after-keep", action="store_true")
    parser.add_argument("--launch-path", type=Path, default=None)
    parser.add_argument("--log-path", type=Path, default=None)
    parser.add_argument("--force", action="store_true")


def launch_path(run_dir: Path, explicit: Path | None = None) -> Path:
    return (explicit or run_dir / "launch.json").resolve()


def runtime_path(run_dir: Path) -> Path:
    return (run_dir / "runtime.json").resolve()


def runtime_log_path(run_dir: Path, explicit: Path | None = None) -> Path:
    return (explicit or run_dir / "runtime.log").resolve()


def create_launch(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1")
    path = launch_path(run_dir, args.launch_path)
    if path.exists() and not args.force:
        raise SystemExit(f"{path} already exists; use --force to overwrite")
    payload = {
        "version": 1,
        "created_at": utc_now(),
        "run_dir": str(run_dir),
        "iteration_command": args.iteration_command,
        "iterations": args.iterations,
        "sleep_seconds": args.sleep_seconds,
        "rollback_command": args.rollback_command,
        "stop_after_keep": bool(args.stop_after_keep),
        "log_path": str(runtime_log_path(run_dir, args.log_path)),
    }
    write_json(path, payload)
    return payload | {"launch_path": str(path)}


def load_launch(run_dir: Path, explicit: Path | None = None) -> dict[str, Any]:
    path = launch_path(run_dir, explicit)
    payload = read_json(path)
    payload["launch_path"] = str(path)
    return payload


def read_runtime(run_dir: Path) -> dict[str, Any]:
    path = runtime_path(run_dir)
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {"status": "corrupt", "runtime_path": str(path)}


def write_runtime(run_dir: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = utc_now()
    write_json(runtime_path(run_dir), payload)


def pid_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def start_runtime(args: argparse.Namespace, *, runner_path: Path) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    launch = load_launch(run_dir, args.launch_path)
    current = read_runtime(run_dir)
    if pid_alive(current.get("pid")):
        return runtime_summary(run_dir) | {"action": "already_running"}

    log_path = Path(str(launch.get("log_path") or runtime_log_path(run_dir))).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(runner_path),
        "run",
        "--run-dir",
        str(run_dir),
        "--launch-path",
        str(launch["launch_path"]),
    ]
    log_handle = log_path.open("a", encoding="utf-8")
    proc = subprocess.Popen(
        command,
        cwd=str(run_dir),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    write_runtime(
        run_dir,
        {
            "version": 1,
            "status": "running",
            "active": True,
            "pid": proc.pid,
            "started_at": utc_now(),
            "run_dir": str(run_dir),
            "launch_path": str(launch["launch_path"]),
            "log_path": str(log_path),
            "stop_requested": False,
            "iterations_completed": 0,
        },
    )
    write_hook_context(run_dir, active=True, session_mode="background")
    return runtime_summary(run_dir) | {"action": "start"}


def run_runtime(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.resolve()
    launch = load_launch(run_dir, args.launch_path)
    total = int(launch.get("iterations") or 1)
    sleep_seconds = float(launch.get("sleep_seconds") or 0)
    completed = 0
    status = "completed"
    returncode = 0

    for _ in range(total):
        current = read_runtime(run_dir)
        if current.get("stop_requested") is True:
            status = "stopped"
            break
        command = [
            sys.executable,
            str(Path(__file__).resolve().with_name("run_auto_harness.py")),
            "--run-dir",
            str(run_dir),
            "--iteration-command",
            str(launch["iteration_command"]),
            "--iterations",
            "1",
            "--allow-background",
            "--default-terminal-status",
            "user_decision_needed",
        ]
        if launch.get("rollback_command"):
            command.extend(["--rollback-command", str(launch["rollback_command"])])
        if launch.get("stop_after_keep"):
            command.append("--stop-after-keep")
        proc = subprocess.run(command, text=True, check=False)
        completed += 1
        write_runtime(
            run_dir,
            read_runtime(run_dir)
            | {
                "status": "running",
                "active": True,
                "pid": os.getpid(),
                "iterations_completed": completed,
                "last_returncode": proc.returncode,
            },
        )
        if proc.returncode != 0:
            status = "failed"
            returncode = proc.returncode
            break
        auto_state = read_json(run_dir / "auto_state.json")
        terminal = ((auto_state.get("state") or {}).get("terminal_status"))
        if terminal in {"goal_met", "failed_with_evidence", "policy_blocked", "environment_blocked"}:
            status = "completed" if terminal == "goal_met" else "failed"
            break
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if status == "completed":
        finalize_terminal_status(run_dir, "budget_exhausted")
    write_runtime(
        run_dir,
        read_runtime(run_dir)
        | {
            "status": status,
            "active": False,
            "pid": os.getpid(),
            "iterations_completed": completed,
            "finished_at": utc_now(),
            "returncode": returncode,
            "stop_requested": status == "stopped",
        },
    )
    write_hook_context(run_dir, active=False, session_mode="background")
    return returncode


def finalize_terminal_status(run_dir: Path, status: str) -> None:
    manifest = read_json(run_dir / "manifest.json")
    auto_state = read_json(run_dir / "auto_state.json")
    state = auto_state.get("state")
    if isinstance(state, dict) and state.get("terminal_status") == "goal_met":
        return
    if isinstance(state, dict):
        state["terminal_status"] = status
    manifest["termination"] = {
        "status": status,
        "reason": "background runtime reached configured iteration boundary",
    }
    write_json(run_dir / "auto_state.json", auto_state)
    write_json(run_dir / "manifest.json", manifest)


def stop_runtime(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    current = read_runtime(run_dir)
    current["stop_requested"] = True
    current["status"] = "stopping"
    write_runtime(run_dir, current)
    pid = current.get("pid")
    if pid_alive(pid):
        os.kill(int(pid), signal.SIGTERM)
        deadline = time.time() + args.grace_seconds
        while time.time() < deadline and pid_alive(pid):
            time.sleep(0.1)
    current = read_runtime(run_dir)
    current["active"] = False
    current["status"] = "stopped"
    current["stop_requested"] = True
    write_runtime(run_dir, current)
    write_hook_context(run_dir, active=False, session_mode="background")
    return runtime_summary(run_dir) | {"action": "stop"}


def runtime_summary(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    runtime = read_runtime(run_dir)
    launch_exists = (run_dir / "launch.json").exists()
    active = pid_alive(runtime.get("pid")) if runtime else False
    summary = {
        "run_dir": str(run_dir),
        "launch_path": str(run_dir / "launch.json"),
        "runtime_path": str(runtime_path(run_dir)),
        "launch_exists": launch_exists,
        "runtime_exists": bool(runtime),
        "active": active,
    }
    if runtime:
        summary.update(runtime)
        summary["active"] = active and runtime.get("active") is not False
    if (run_dir / "auto_state.json").exists():
        auto_state = read_json(run_dir / "auto_state.json")
        state = auto_state.get("state") if isinstance(auto_state.get("state"), dict) else {}
        summary["iteration"] = state.get("iteration")
        summary["last_status"] = state.get("last_status")
        summary["terminal_status"] = state.get("terminal_status")
    return summary


def write_hook_context(run_dir: Path, *, active: bool, session_mode: str) -> None:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    context_path = codex_home / "harness-engineer-hooks" / "context.json"
    context = {
        "version": 1,
        "updated_at": utc_now(),
        "active": active,
        "session_mode": session_mode,
        "run_dir": str(run_dir.resolve()),
        "runtime_path": str(runtime_path(run_dir.resolve())),
    }
    write_json(context_path, context)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()
    runner_path = Path(__file__).resolve()
    if args.command == "create-launch":
        print_json(create_launch(args))
        return 0
    if args.command == "launch":
        create_launch(args)
        print_json(start_runtime(args, runner_path=runner_path))
        return 0
    if args.command == "start":
        print_json(start_runtime(args, runner_path=runner_path))
        return 0
    if args.command == "run":
        return run_runtime(args)
    if args.command == "status":
        print_json(runtime_summary(args.run_dir))
        return 0
    if args.command == "stop":
        print_json(stop_runtime(args))
        return 0
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

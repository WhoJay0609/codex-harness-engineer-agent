#!/usr/bin/env python3
"""Install, inspect, or remove user-level Codex hooks for harness-engineer."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from auto_harness_common import utc_now


FEATURE_SECTION = "features"
FEATURE_KEY = "codex_hooks"
MANAGED_DIR_NAME = "harness-engineer-hooks"
SESSION_SCRIPT_NAME = "session_start.py"
STOP_SCRIPT_NAME = "stop.py"
MANIFEST_FILE_NAME = "manifest.json"
SESSION_STATUS_MESSAGE = "harness-engineer SessionStart hook"
STOP_STATUS_MESSAGE = "harness-engineer Stop hook"


class HookCtlError(RuntimeError):
    pass


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()


def managed_dir() -> Path:
    return codex_home() / MANAGED_DIR_NAME


def config_path() -> Path:
    return codex_home() / "config.toml"


def hooks_path() -> Path:
    return codex_home() / "hooks.json"


def manifest_path() -> Path:
    return managed_dir() / MANIFEST_FILE_NAME


def session_script_path() -> Path:
    return managed_dir() / SESSION_SCRIPT_NAME


def stop_script_path() -> Path:
    return managed_dir() / STOP_SCRIPT_NAME


def source_session_script() -> Path:
    return Path(__file__).resolve().with_name("harness_hook_session_start.py")


def source_stop_script() -> Path:
    return Path(__file__).resolve().with_name("harness_hook_stop.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage harness-engineer user-level Codex hooks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="inspect hook installation")
    subparsers.add_parser("install", help="install or update managed hooks")
    subparsers.add_parser("uninstall", help="remove managed hooks")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def backup_path(path: Path) -> Path:
    stamp = utc_now().replace(":", "").replace("-", "")
    return path.with_name(f"{path.name}.bak.{stamp}")


def write_text_with_backup(path: Path, content: str) -> str | None:
    existing = read_text(path)
    if existing == content:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = backup_path(path)
        shutil.copy2(path, backup)
    path.write_text(content, encoding="utf-8")
    return str(backup) if backup else None


def parse_feature_value(text: str) -> bool | None:
    section = re.search(rf"(?ms)^\[{FEATURE_SECTION}\]\s*$\n(?P<body>.*?)(?=^\[|\Z)", text)
    if section is None:
        return None
    match = re.search(rf"(?m)^\s*{FEATURE_KEY}\s*=\s*(true|false)\s*(?:#.*)?$", section.group("body"))
    if match is None:
        return None
    return match.group(1) == "true"


def set_toml_boolean(text: str, value: bool) -> str:
    lines = text.splitlines()
    section_header = f"[{FEATURE_SECTION}]"
    value_text = "true" if value else "false"
    section_start = None
    section_end = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == section_header:
            section_start = index
            for probe in range(index + 1, len(lines)):
                stripped = lines[probe].strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    section_end = probe
                    break
            break
    key_pattern = re.compile(rf"^\s*{FEATURE_KEY}\s*=")
    if section_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([section_header, f"{FEATURE_KEY} = {value_text}"])
    else:
        for index in range(section_start + 1, section_end):
            if key_pattern.match(lines[index]):
                lines[index] = f"{FEATURE_KEY} = {value_text}"
                break
        else:
            lines.insert(section_end, f"{FEATURE_KEY} = {value_text}")
    return "\n".join(lines).rstrip() + "\n"


def load_hooks_payload() -> dict[str, Any]:
    if not hooks_path().exists():
        return {"hooks": {}}
    try:
        payload = json.loads(hooks_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HookCtlError(f"invalid hooks.json: {hooks_path()}") from exc
    if not isinstance(payload, dict):
        raise HookCtlError("hooks.json must contain a JSON object")
    hooks = payload.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise HookCtlError("hooks.json key 'hooks' must be an object")
    return payload


def installed_command(script_path: Path) -> str:
    return f"python3 {shlex.quote(str(script_path))}"


def hook_group(command: str, status_message: str, timeout: int, matcher: str | None = None) -> dict[str, Any]:
    group: dict[str, Any] = {
        "hooks": [{"type": "command", "command": command, "timeout": timeout, "statusMessage": status_message}]
    }
    if matcher:
        group["matcher"] = matcher
    return group


def group_matches(group: Any, commands: set[str]) -> bool:
    if not isinstance(group, dict):
        return False
    hooks = group.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != 1:
        return False
    hook = hooks[0]
    return isinstance(hook, dict) and hook.get("command") in commands and hook.get("type") == "command"


def count_hook_groups(payload: dict[str, Any]) -> int:
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        return 0
    return sum(len(groups) for groups in hooks.values() if isinstance(groups, list))


def read_manifest() -> dict[str, Any]:
    if not manifest_path().exists():
        return {}
    try:
        payload = json.loads(manifest_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_manifest(feature_enabled_by_installer: bool) -> None:
    payload = {
        "version": 1,
        "installed_at": utc_now(),
        "feature_enabled_by_installer": feature_enabled_by_installer,
        "managed_scripts": {
            "session_start": str(session_script_path()),
            "stop": str(stop_script_path()),
        },
    }
    manifest_path().parent.mkdir(parents=True, exist_ok=True)
    manifest_path().write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_scripts() -> None:
    if os.name == "nt":
        raise HookCtlError("Codex lifecycle hooks are not supported on Windows by this helper")
    managed_dir().mkdir(parents=True, exist_ok=True)
    for source, dest in (
        (source_session_script(), session_script_path()),
        (source_stop_script(), stop_script_path()),
    ):
        shutil.copy2(source, dest)
        dest.chmod(0o755)


def status() -> dict[str, Any]:
    config_text = read_text(config_path())
    payload = load_hooks_payload()
    hooks = payload.get("hooks", {})
    session_command = installed_command(session_script_path())
    stop_command = installed_command(stop_script_path())
    session_groups = hooks.get("SessionStart", []) if isinstance(hooks, dict) else []
    stop_groups = hooks.get("Stop", []) if isinstance(hooks, dict) else []
    managed_session = any(group_matches(group, {session_command}) for group in session_groups)
    managed_stop = any(group_matches(group, {stop_command}) for group in stop_groups)
    return {
        "supported": os.name != "nt",
        "codex_home": str(codex_home()),
        "config_path": str(config_path()),
        "hooks_path": str(hooks_path()),
        "managed_dir": str(managed_dir()),
        "feature_enabled": parse_feature_value(config_text) is True,
        "managed_session_start_installed": managed_session and session_script_path().exists(),
        "managed_stop_installed": managed_stop and stop_script_path().exists(),
        "manifest_present": manifest_path().exists(),
        "other_hook_groups_present": count_hook_groups(payload) - int(managed_session) - int(managed_stop),
        "ready_for_future_sessions": (
            parse_feature_value(config_text) is True
            and managed_session
            and managed_stop
            and session_script_path().exists()
            and stop_script_path().exists()
        ),
    }


def install() -> dict[str, Any]:
    config_before = read_text(config_path())
    feature_enabled_by_installer = parse_feature_value(config_before) is not True
    install_scripts()
    config_backup = write_text_with_backup(config_path(), set_toml_boolean(config_before, True))
    payload = load_hooks_payload()
    hooks = payload.setdefault("hooks", {})
    session_command = installed_command(session_script_path())
    stop_command = installed_command(stop_script_path())
    managed_commands = {session_command, stop_command}
    for name, group in (
        ("SessionStart", hook_group(session_command, SESSION_STATUS_MESSAGE, 5, matcher="startup|resume")),
        ("Stop", hook_group(stop_command, STOP_STATUS_MESSAGE, 10)),
    ):
        groups = hooks.get(name, [])
        if not isinstance(groups, list):
            raise HookCtlError(f"hooks.{name} must be a list")
        hooks[name] = [item for item in groups if not group_matches(item, managed_commands)] + [group]
    hooks_backup = write_text_with_backup(hooks_path(), json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_manifest(feature_enabled_by_installer)
    return status() | {"action": "install", "config_backup": config_backup, "hooks_backup": hooks_backup}


def uninstall() -> dict[str, Any]:
    manifest = read_manifest()
    feature_enabled_by_installer = bool(manifest.get("feature_enabled_by_installer"))
    payload = load_hooks_payload()
    hooks = payload.setdefault("hooks", {})
    managed_commands = {installed_command(session_script_path()), installed_command(stop_script_path())}
    removed = 0
    for name in ("SessionStart", "Stop"):
        groups = hooks.get(name, [])
        if not isinstance(groups, list):
            raise HookCtlError(f"hooks.{name} must be a list")
        kept = [item for item in groups if not group_matches(item, managed_commands)]
        removed += len(groups) - len(kept)
        if kept:
            hooks[name] = kept
        else:
            hooks.pop(name, None)
    hooks_backup = write_text_with_backup(hooks_path(), json.dumps(payload, indent=2, sort_keys=True) + "\n")
    config_backup = None
    if feature_enabled_by_installer and count_hook_groups(payload) == 0:
        config_backup = write_text_with_backup(config_path(), set_toml_boolean(read_text(config_path()), False))
    for path in (session_script_path(), stop_script_path(), manifest_path()):
        if path.exists():
            path.unlink()
    if managed_dir().exists():
        try:
            managed_dir().rmdir()
        except OSError:
            pass
    return status() | {
        "action": "uninstall",
        "managed_groups_removed": removed,
        "config_backup": config_backup,
        "hooks_backup": hooks_backup,
    }


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()
    if args.command == "status":
        print_json(status())
    elif args.command == "install":
        print_json(install())
    elif args.command == "uninstall":
        print_json(uninstall())
    else:
        raise SystemExit(f"unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HookCtlError as exc:
        raise SystemExit(f"error: {exc}")

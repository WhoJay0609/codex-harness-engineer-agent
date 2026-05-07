#!/usr/bin/env python3
"""Validate a harness-engineer run directory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "manifest.json",
    "subagents.jsonl",
    "skill_invocations.jsonl",
    "escalations.jsonl",
    "events.jsonl",
    "tool_calls.jsonl",
    "failures.jsonl",
    "metrics.json",
    "summary.md",
    "replay.md",
]

AUTO_REQUIRED_FILES = [
    "auto_state.json",
    "results.tsv",
    "context.json",
]

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
TERMINAL_STATUSES = {"completed", "stopped", "replaced", "failed", "blocked"}
TERMINAL_EVENTS = {"completed", "stopped", "replaced", "failed", "blocked"}
TRACE_V2_EVENT_TYPES = {
    "message",
    "thought",
    "plan",
    "action",
    "observation",
    "tool_call",
    "tool_observation",
    "skill_check",
    "skill_invocation",
    "subagent_created",
    "subagent_terminal",
    "escalation",
    "metric",
    "failure",
    "checkpoint",
    "decision",
    "state_snapshot",
    "termination",
}
TRACE_V2_SOURCES = {
    "user",
    "orchestrator",
    "subagent",
    "tool",
    "skill",
    "runtime",
    "environment",
    "validator",
    "system",
}
TRACE_V2_TOOL_OBSERVATION_TYPES = {"tool_observation", "observation"}
EXPERT_LIBRARY_VERSION = "harness-experts.v3"
ALLOWED_EXPERT_LIBRARY_VERSIONS = {"harness-experts.v1", "harness-experts.v2", "harness-experts.v3"}
RESERVED_ORCHESTRATION_SKILLS = {"codex-autoresearch", "multi-agent", "expert-debate"}
EXPERT_ROLES = {
    "Professor Orchestrator",
    "Intent Router",
    "Context Curator",
    "Task Decomposer",
    "Debate Moderator",
    "Red Team Critic",
    "Harness Architect",
    "Runner Coordinator",
    "Verifier / Evidence Auditor",
    "Environment Builder",
    "Runner",
    "Verifier",
    "Failure Analyst",
    "Mechanical Gatekeeper",
    "Entropy Gardener",
    "Evidence Auditor",
    "Trace Auditor",
    "Research Novelty Expert",
    "Method / Theory Expert",
    "Theory Derivation Expert",
    "Paper-to-Code Expert",
    "Experiment Designer",
    "Reproducibility Expert",
    "Paper Figure Expert",
    "Paper / Writing Expert",
    "Reviewer / Critic",
    "Algorithm Diagnostician",
    "Algorithm Inventor",
    "Benchmark Designer",
    "Metric Auditor",
    "Ablation Planner",
    "Engineering Architect",
    "Frontend Expert",
    "Backend / API Expert",
    "Data / Integration Expert",
    "QA / Test Expert",
    "Security / Reliability Expert",
    "Deploy / Release Expert",
    "Problem Framer",
    "Industry Project Delivery Expert",
    "Product / UX Expert",
    "Cost-Benefit Expert",
    "Risk Reviewer",
    "Research Material Organizer",
    "Proposal / Grant Expert",
    "Documentation Steward",
    "Operations Expert",
    "Research Ideation Expert",
    "Literature / Novelty Expert",
    "Research Pipeline Expert",
    "Theory Expert",
    "Paper Writing Expert",
    "Paper Figures / Talks Expert",
    "Experiment / Metrics Expert",
    "Algorithm Expert",
    "ML Training Expert",
    "LLM Fine-Tuning Expert",
    "LLM Serving Expert",
    "Compression Expert",
    "Model Architecture Expert",
    "Interpretability Expert",
    "Evaluation / Benchmark Expert",
    "RAG / Agents Expert",
    "Retrieval / Vector DB Expert",
    "Tokenizer / Data Expert",
    "Multimodal / Vision Expert",
    "Robotics / Embodied Expert",
    "Audio / Speech Expert",
    "Safety / Guardrails Expert",
    "Frontend / Design Expert",
    "Game / Desktop Expert",
    "CI / PR Expert",
    "Deploy Expert",
    "Documents / Materials Expert",
    "Knowledge / Notion Expert",
    "Project Delivery Expert",
    "Notification / Ops Expert",
}


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON at line {exc.lineno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"{path.name}: cannot read file: {exc}")
    return None


def load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{lineno}: invalid JSONL: {exc.msg}")
                continue
            if not isinstance(row, dict):
                errors.append(f"{path.name}:{lineno}: record must be a JSON object")
                continue
            row["_line"] = lineno
            rows.append(row)
    except OSError as exc:
        errors.append(f"{path.name}: cannot read file: {exc}")
    return rows


def is_trace_v2_row(row: dict[str, Any]) -> bool:
    return any(
        key in row
        for key in [
            "event_version",
            "event_id",
            "parent_id",
            "event_type",
            "source",
            "tool_call_id",
            "command_hash",
        ]
    )


def check_typed_event_log(
    events: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    errors: list[str],
) -> None:
    v2_events = [row for row in events if is_trace_v2_row(row)]
    if not v2_events:
        return

    seen_ids: set[str] = set()
    tool_call_events: dict[str, dict[str, Any]] = {}
    observed_tool_calls: set[str] = set()
    terminal_seen = False

    for row in v2_events:
        line = row.get("_line")
        prefix = f"events.jsonl:{line}"
        event_version = row.get("event_version")
        if event_version not in {None, 2}:
            errors.append(f"{prefix}: event_version must be 2 when present")
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            errors.append(f"{prefix}: trace v2 event must include non-empty event_id")
        elif event_id in seen_ids:
            errors.append(f"{prefix}: duplicate event_id {event_id}")
        else:
            seen_ids.add(event_id)

        parent_id = row.get("parent_id")
        if parent_id not in {None, ""} and parent_id not in seen_ids:
            errors.append(f"{prefix}: parent_id {parent_id} must reference an earlier event_id")

        event_type = row.get("event_type")
        if event_type not in TRACE_V2_EVENT_TYPES:
            errors.append(f"{prefix}: unknown trace v2 event_type {event_type!r}")

        source = row.get("source")
        if source not in TRACE_V2_SOURCES:
            errors.append(f"{prefix}: unknown trace v2 source {source!r}")

        if not row.get("ts"):
            errors.append(f"{prefix}: trace v2 event must include ts")

        if event_type in {"action", "tool_call"} and not row.get("action") and not row.get("tool"):
            errors.append(f"{prefix}: {event_type} event must include action or tool")
        if event_type in TRACE_V2_TOOL_OBSERVATION_TYPES and not row.get("observation"):
            errors.append(f"{prefix}: {event_type} event must include observation")
        if event_type == "tool_call":
            tool_call_id = row.get("tool_call_id")
            if not isinstance(tool_call_id, str) or not tool_call_id:
                errors.append(f"{prefix}: tool_call event must include tool_call_id")
            else:
                tool_call_events[tool_call_id] = row
        if event_type in TRACE_V2_TOOL_OBSERVATION_TYPES:
            tool_call_id = row.get("tool_call_id")
            if isinstance(tool_call_id, str) and tool_call_id:
                observed_tool_calls.add(tool_call_id)
        if event_type == "failure" and not row.get("error_kind"):
            errors.append(f"{prefix}: failure event must include error_kind")
        if event_type == "termination":
            terminal_seen = True
            status = row.get("status")
            if status not in RUN_TERMINAL_STATUSES:
                errors.append(f"{prefix}: termination event status must be a harness terminal status")

    for tool_call_id, row in sorted(tool_call_events.items()):
        if tool_call_id not in observed_tool_calls:
            errors.append(
                f"events.jsonl:{row.get('_line')}: tool_call {tool_call_id} has no matching observation event"
            )

    if v2_events and not terminal_seen:
        errors.append("events.jsonl: trace v2 runs must include a termination event")

    for row in tool_calls:
        if not is_trace_v2_row(row):
            continue
        line = row.get("_line")
        if not row.get("tool_call_id"):
            errors.append(f"tool_calls.jsonl:{line}: trace v2 tool call must include tool_call_id")
        if not row.get("tool") and not row.get("action"):
            errors.append(f"tool_calls.jsonl:{line}: trace v2 tool call must include tool or action")
        status = row.get("status")
        if status and status not in {"pending", "running", "completed", "failed", "blocked"}:
            errors.append(f"tool_calls.jsonl:{line}: unknown trace v2 tool call status {status!r}")

    for row in failures:
        if not is_trace_v2_row(row):
            continue
        line = row.get("_line")
        if not row.get("error_kind") and not row.get("failure_kind"):
            errors.append(f"failures.jsonl:{line}: trace v2 failure must include error_kind or failure_kind")


def load_skill_inventory(errors: list[str]) -> tuple[set[str], set[str]]:
    """Return installed skill ids/names and the reserved orchestration subset."""
    inventory_path = Path(__file__).resolve().parents[1] / "references" / "skill-inventory.json"
    data = load_json(inventory_path, errors)
    installed: set[str] = set()
    reserved: set[str] = set(RESERVED_ORCHESTRATION_SKILLS)

    if not isinstance(data, dict):
        errors.append("skill-inventory.json: must be a JSON object")
        return installed, reserved

    for key in ["core_harness_skills", "reserved_orchestration_skills"]:
        values = data.get(key, [])
        if isinstance(values, list):
            installed.update(str(value) for value in values if value)
            if key == "reserved_orchestration_skills":
                reserved.update(str(value) for value in values if value)

    skills = data.get("skills")
    if not isinstance(skills, list):
        errors.append("skill-inventory.json: skills must be a list")
        return installed, reserved

    for index, entry in enumerate(skills, start=1):
        if not isinstance(entry, dict):
            errors.append(f"skill-inventory.json: skills[{index}] must be an object")
            continue
        labels = {
            str(entry.get(key))
            for key in ["id", "name"]
            if isinstance(entry.get(key), str) and entry.get(key)
        }
        installed.update(labels)
        if entry.get("reserved") is True or entry.get("category") == "reserved_orchestration_skill":
            reserved.update(labels)

    return installed, reserved


def load_expert_roles(errors: list[str]) -> set[str]:
    """Return known expert roles from the generated library plus legacy roles."""
    expert_library_path = Path(__file__).resolve().parents[1] / "references" / "expert-capability-library.json"
    roles = set(EXPERT_ROLES)
    if not expert_library_path.exists():
        errors.append("expert-capability-library.json: missing generated expert library")
        return roles
    data = load_json(expert_library_path, errors)
    if not isinstance(data, dict):
        errors.append("expert-capability-library.json: must be a JSON object")
        return roles
    role_records = data.get("roles")
    if not isinstance(role_records, list):
        errors.append("expert-capability-library.json: roles must be a list")
        return roles
    for record in role_records:
        if not isinstance(record, dict):
            continue
        role = record.get("role")
        if isinstance(role, str) and role:
            roles.add(role)
    return roles


def check_required_files(run_dir: Path, errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (run_dir / name).exists():
            errors.append(f"missing required artifact: {name}")


def check_manifest(manifest: Any, expert_roles: set[str], errors: list[str]) -> None:
    if not isinstance(manifest, dict):
        errors.append("manifest.json: must be a JSON object")
        return
    for key in ["schema_version", "experiment_id", "run_id", "goal", "success_criteria", "termination"]:
        if key not in manifest:
            errors.append(f"manifest.json: missing key '{key}'")
    termination = manifest.get("termination")
    if not isinstance(termination, dict) or "status" not in termination:
        errors.append("manifest.json: termination.status is required")
    team_policy = manifest.get("team_policy")
    if not isinstance(team_policy, dict):
        errors.append("manifest.json: team_policy is required")
        return
    mode = team_policy.get("mode")
    if mode not in {"internal_team", "single_agent"}:
        errors.append("manifest.json: team_policy.mode must be internal_team or single_agent")
    if not team_policy.get("reason"):
        errors.append("manifest.json: team_policy.reason is required")
    initial_roles = team_policy.get("initial_roles")
    if not isinstance(initial_roles, list):
        errors.append("manifest.json: team_policy.initial_roles must be a list")
    else:
        for role in initial_roles:
            if role not in expert_roles:
                errors.append(f"manifest.json: unknown initial role '{role}'")
    expert_library_version = team_policy.get("expert_library_version")
    if expert_library_version not in ALLOWED_EXPERT_LIBRARY_VERSIONS:
        allowed_versions = ", ".join(sorted(ALLOWED_EXPERT_LIBRARY_VERSIONS))
        errors.append(f"manifest.json: team_policy.expert_library_version must be one of: {allowed_versions}")

    if expert_library_version == EXPERT_LIBRARY_VERSION:
        if team_policy.get("skill_policy") != "external_domain_allowed_by_allowlist":
            errors.append("manifest.json: team_policy.skill_policy must be external_domain_allowed_by_allowlist")
        if team_policy.get("reserved_orchestration_policy") != "explicit_user_request_only":
            errors.append("manifest.json: team_policy.reserved_orchestration_policy must be explicit_user_request_only")
    elif team_policy.get("external_skills_policy") != "explicit_user_request_only":
        errors.append("manifest.json: team_policy.external_skills_policy must be explicit_user_request_only for harness-experts.v1")
    if mode == "single_agent" and team_policy.get("single_agent_exception") is not True:
        errors.append("manifest.json: single_agent mode requires single_agent_exception=true")
    if mode == "internal_team" and not initial_roles:
        errors.append("manifest.json: internal_team mode requires non-empty initial_roles")


def validate_skill_reference(source: str, skill: Any, installed_skills: set[str], errors: list[str]) -> str | None:
    if not isinstance(skill, str) or not skill:
        errors.append(f"{source}: skill name must be a non-empty string")
        return None
    if skill not in installed_skills:
        errors.append(f"{source}: unknown or uninstalled skill '{skill}'")
    return skill


def build_agent_allowlists(subagents: list[dict[str, Any]]) -> dict[str, set[str]]:
    allowlists: dict[str, set[str]] = {}
    for row in subagents:
        agent_id = row.get("agent_id")
        if not agent_id:
            continue
        allowed_skills = row.get("allowed_skills")
        if isinstance(allowed_skills, list):
            allowlists.setdefault(str(agent_id), set()).update(
                str(skill) for skill in allowed_skills if isinstance(skill, str) and skill
            )
        needed_skill = row.get("needed_skill")
        if (
            isinstance(needed_skill, str)
            and needed_skill
            and row.get("skill_route_decision") == "expand_allowlist"
            and row.get("allowlist_expanded_by")
        ):
            allowlists.setdefault(str(agent_id), set()).add(needed_skill)
    return allowlists


def check_subagents(
    subagents: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    escalations: list[dict[str, Any]],
    installed_skills: set[str],
    reserved_skills: set[str],
    expert_roles: set[str],
    errors: list[str],
) -> None:
    created: dict[str, dict[str, Any]] = {}
    terminal: dict[str, dict[str, Any]] = {}

    for row in subagents:
        agent_id = row.get("agent_id")
        if not agent_id:
            errors.append(f"subagents.jsonl:{row.get('_line')}: missing agent_id")
            continue

        event = row.get("event")
        status = row.get("status")
        role = row.get("role")
        if role and role not in expert_roles:
            errors.append(f"subagents.jsonl:{row.get('_line')}: unknown expert role '{role}'")
        if event == "created":
            created[agent_id] = row
            if not row.get("reason"):
                errors.append(f"subagents.jsonl:{row.get('_line')}: created subagent {agent_id} must include reason")
            allowed_skills = row.get("allowed_skills")
            if not isinstance(allowed_skills, list):
                errors.append(f"subagents.jsonl:{row.get('_line')}: created subagent {agent_id} must include allowed_skills list")
            else:
                for skill in allowed_skills:
                    normalized_skill = validate_skill_reference(
                        f"subagents.jsonl:{row.get('_line')}: allowed_skills",
                        skill,
                        installed_skills,
                        errors,
                    )
                    if normalized_skill in reserved_skills and row.get("user_explicit_request") is not True:
                        errors.append(
                            f"subagents.jsonl:{row.get('_line')}: reserved orchestration skill {normalized_skill} in allowed_skills requires user_explicit_request=true"
                        )
            forbidden_skills = row.get("forbidden_skills")
            if forbidden_skills is not None and not isinstance(forbidden_skills, list):
                errors.append(f"subagents.jsonl:{row.get('_line')}: forbidden_skills must be a list when present")
            elif isinstance(forbidden_skills, list):
                for skill in forbidden_skills:
                    validate_skill_reference(
                        f"subagents.jsonl:{row.get('_line')}: forbidden_skills",
                        skill,
                        installed_skills,
                        errors,
                    )
            if "required_skill_check" not in row:
                errors.append(f"subagents.jsonl:{row.get('_line')}: created subagent {agent_id} must include required_skill_check")

        if status in TERMINAL_STATUSES or event in TERMINAL_EVENTS:
            terminal[agent_id] = row
            if not row.get("stop_reason"):
                errors.append(f"subagents.jsonl:{row.get('_line')}: terminal subagent {agent_id} is missing stop_reason")

        needed_role = row.get("needed_internal_expert")
        if needed_role:
            if needed_role not in expert_roles:
                errors.append(f"subagents.jsonl:{row.get('_line')}: unknown needed_internal_expert '{needed_role}'")
            has_decision = any(
                esc.get("triggered_by") == agent_id or esc.get("agent_id") == agent_id
                for esc in escalations
            )
            if not has_decision:
                errors.append(f"subagents.jsonl:{row.get('_line')}: {agent_id} requested internal expert without escalations.jsonl decision")

        needed_skill = row.get("needed_skill")
        if needed_skill:
            normalized_needed_skill = validate_skill_reference(
                f"subagents.jsonl:{row.get('_line')}: needed_skill",
                needed_skill,
                installed_skills,
                errors,
            )
            decision = row.get("skill_route_decision")
            if decision not in {"expand_allowlist", "deny_reserved", "deny_uninstalled", "deny_scope", "continue_without_skill"}:
                errors.append(
                    f"subagents.jsonl:{row.get('_line')}: needed_skill requires skill_route_decision"
                )
            if (
                decision == "expand_allowlist"
                and normalized_needed_skill in reserved_skills
                and row.get("user_explicit_request") is not True
            ):
                errors.append(
                    f"subagents.jsonl:{row.get('_line')}: reserved orchestration skill {normalized_needed_skill} requires user_explicit_request=true"
                )
            if decision == "expand_allowlist":
                if not row.get("allowlist_expanded_by"):
                    errors.append(f"subagents.jsonl:{row.get('_line')}: allowlist expansion requires allowlist_expanded_by")
                has_route_record = any(
                    (esc.get("triggered_by") == agent_id or esc.get("agent_id") == agent_id)
                    and (
                        esc.get("event") == "skill_route_decision"
                        or esc.get("needed_skill") == normalized_needed_skill
                        or esc.get("skill_route_decision") == "expand_allowlist"
                    )
                    for esc in escalations
                )
                if not has_route_record:
                    errors.append(
                        f"subagents.jsonl:{row.get('_line')}: allowlist expansion for {agent_id} requires escalations.jsonl route decision"
                    )

    for agent_id, row in created.items():
        if agent_id not in terminal:
            errors.append(f"subagents.jsonl:{row.get('_line')}: subagent {agent_id} was created but has no terminal event")
        if row.get("required_skill_check") is True:
            has_skill_record = any(skill.get("agent_id") == agent_id for skill in skills)
            if not has_skill_record:
                errors.append(f"skill_invocations.jsonl: missing required skill check for subagent {agent_id}")


def check_team_policy(manifest: Any, subagents: list[dict[str, Any]], errors: list[str]) -> None:
    if not isinstance(manifest, dict):
        return
    team_policy = manifest.get("team_policy")
    if not isinstance(team_policy, dict):
        return
    if team_policy.get("mode") != "internal_team":
        return
    created_roles = {
        str(row.get("role"))
        for row in subagents
        if row.get("event") == "created" and row.get("role")
    }
    if not created_roles:
        errors.append("subagents.jsonl: internal_team mode requires at least one created subagent")
    for role in team_policy.get("initial_roles", []):
        if role not in created_roles:
            errors.append(f"subagents.jsonl: initial role '{role}' was not created")


def check_skill_invocations(
    skills: list[dict[str, Any]],
    subagents: list[dict[str, Any]],
    installed_skills: set[str],
    reserved_skills: set[str],
    errors: list[str],
) -> None:
    agent_allowlists = build_agent_allowlists(subagents)
    for row in skills:
        line = row.get("_line")
        skill = row.get("skill")
        agent_id = row.get("agent_id")
        if not agent_id:
            errors.append(f"skill_invocations.jsonl:{line}: missing agent_id")
        if "allowed" not in row:
            errors.append(f"skill_invocations.jsonl:{line}: missing allowed")
        if "used" not in row:
            errors.append(f"skill_invocations.jsonl:{line}: missing used")
        if row.get("allowed") is False and not row.get("blocked_reason"):
            errors.append(f"skill_invocations.jsonl:{line}: disallowed skill record must include blocked_reason")
        normalized_skill = validate_skill_reference(
            f"skill_invocations.jsonl:{line}",
            skill,
            installed_skills,
            errors,
        )
        if not normalized_skill:
            continue
        if row.get("used") is True and agent_id:
            allowed = agent_allowlists.get(str(agent_id), set())
            if normalized_skill not in allowed:
                errors.append(
                    f"skill_invocations.jsonl:{line}: skill {normalized_skill} is not in allowed_skills for subagent {agent_id}"
                )
        if normalized_skill in reserved_skills and row.get("used") is True and row.get("user_explicit_request") is not True:
            errors.append(
                f"skill_invocations.jsonl:{line}: reserved orchestration skill {normalized_skill} requires user_explicit_request=true"
            )


def check_escalations(
    escalations: list[dict[str, Any]],
    installed_skills: set[str],
    reserved_skills: set[str],
    expert_roles: set[str],
    errors: list[str],
) -> None:
    for row in escalations:
        line = row.get("_line")
        event = row.get("event")
        external_skill = row.get("external_skill")
        internal_action = row.get("internal_expert_action")

        if event == "external_skill_used" or external_skill in reserved_skills:
            normalized_skill = validate_skill_reference(
                f"escalations.jsonl:{line}: external_skill",
                external_skill,
                installed_skills,
                errors,
            )
            if normalized_skill in reserved_skills and row.get("user_explicit_request") is not True:
                errors.append(
                    f"escalations.jsonl:{line}: reserved orchestration skill use requires user_explicit_request=true"
                )
            for key in ["reason", "summary", "decision"]:
                if not row.get(key):
                    errors.append(f"escalations.jsonl:{line}: external skill record missing {key}")
            continue

        if event == "skill_route_decision":
            needed_skill = row.get("needed_skill")
            decision = row.get("decision")
            normalized_skill = validate_skill_reference(
                f"escalations.jsonl:{line}: needed_skill",
                needed_skill,
                installed_skills,
                errors,
            )
            if normalized_skill in reserved_skills and decision == "expand_allowlist" and row.get("user_explicit_request") is not True:
                errors.append(
                    f"escalations.jsonl:{line}: reserved orchestration skill route requires user_explicit_request=true"
                )
            for key in ["reason", "decision"]:
                if not row.get(key):
                    errors.append(f"escalations.jsonl:{line}: skill route decision missing {key}")
            continue

        if internal_action:
            if internal_action not in {"add", "stop", "replace"}:
                errors.append(f"escalations.jsonl:{line}: internal_expert_action must be add, stop, or replace")
            role = row.get("role")
            if role not in expert_roles:
                errors.append(f"escalations.jsonl:{line}: unknown internal expert role '{role}'")
            for key in ["reason", "decision"]:
                if not row.get(key):
                    errors.append(f"escalations.jsonl:{line}: internal expert action missing {key}")
            continue

        if row:
            errors.append(f"escalations.jsonl:{line}: record must be internal_expert_action, skill_route_decision, or external_skill use")


def coerce_number(value: Any, field: str, errors: list[str]) -> float | None:
    if isinstance(value, bool):
        errors.append(f"{field}: must be numeric, not boolean")
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            errors.append(f"{field}: must be numeric")
            return None
    errors.append(f"{field}: must be numeric")
    return None


def parse_auto_results(path: Path, errors: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header_seen = False
    try:
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip() or line.startswith("#"):
                continue
            cells = line.split("\t")
            if not header_seen:
                header_seen = True
                if cells != AUTO_RESULTS_HEADER:
                    errors.append(f"results.tsv:{lineno}: header must be {'/'.join(AUTO_RESULTS_HEADER)}")
                    return rows
                continue
            if len(cells) != len(AUTO_RESULTS_HEADER):
                errors.append(f"results.tsv:{lineno}: expected {len(AUTO_RESULTS_HEADER)} tab-separated columns")
                continue
            row = dict(zip(AUTO_RESULTS_HEADER, cells))
            row["_line"] = str(lineno)
            rows.append(row)
    except OSError as exc:
        errors.append(f"results.tsv: cannot read file: {exc}")
        return rows

    if not header_seen:
        errors.append("results.tsv: missing header")
    if not rows:
        errors.append("results.tsv: missing iteration rows")
    return rows


def is_main_iteration(value: str) -> bool:
    return re.fullmatch(r"\d+", value) is not None


def check_auto_results(rows: list[dict[str, str]], errors: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"highest_iteration": None, "latest_main_status": None, "baseline_metric": None}
    if not rows:
        return result

    for row in rows:
        line = row.get("_line")
        iteration = row.get("iteration", "")
        status = row.get("status", "")
        guard = row.get("guard", "")
        description = row.get("description", "")

        if status not in AUTO_ROW_STATUSES:
            errors.append(f"results.tsv:{line}: unknown status '{status}'")
        if iteration == "0" and status != "baseline":
            errors.append(f"results.tsv:{line}: iteration 0 must use status baseline")
        if iteration != "0" and status == "baseline":
            errors.append(f"results.tsv:{line}: baseline status is only valid for iteration 0")
        if iteration != "0" and status not in AUTO_NON_BASELINE_STATUSES:
            errors.append(f"results.tsv:{line}: iteration status must record keep/discard/crash/refine/pivot or another auto outcome")
        if guard not in {"pass", "fail", "-"}:
            errors.append(f"results.tsv:{line}: guard must be pass, fail, or -")
        if not description.strip():
            errors.append(f"results.tsv:{line}: description is required")
        coerce_number(row.get("metric"), f"results.tsv:{line}: metric", errors)
        coerce_number(row.get("delta"), f"results.tsv:{line}: delta", errors)

    baseline_rows = [row for row in rows if row.get("iteration") == "0" and row.get("status") == "baseline"]
    if not baseline_rows:
        errors.append("results.tsv: missing baseline row at iteration 0")
    else:
        result["baseline_metric"] = coerce_number(baseline_rows[0].get("metric"), "results.tsv: baseline metric", errors)
        if rows[0] is not baseline_rows[0]:
            errors.append("results.tsv: first iteration row must be the baseline row")
        if len(baseline_rows) > 1:
            errors.append("results.tsv: multiple baseline rows found")

    main_rows = [row for row in rows if is_main_iteration(row.get("iteration", ""))]
    if not main_rows:
        errors.append("results.tsv: missing integer main iteration rows")
        return result
    highest_iteration = max(int(row["iteration"]) for row in main_rows)
    latest_main_rows = [row for row in main_rows if int(row["iteration"]) == highest_iteration]
    result["highest_iteration"] = highest_iteration
    result["latest_main_status"] = latest_main_rows[-1].get("status")
    return result


def check_auto_state(auto_state: Any, manifest: dict[str, Any], result_summary: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(auto_state, dict):
        errors.append("auto_state.json: must be a JSON object")
        return
    for key in ["version", "mode", "config", "state"]:
        if key not in auto_state:
            errors.append(f"auto_state.json: missing key '{key}'")
    if auto_state.get("mode") != "auto_harness":
        errors.append("auto_state.json: mode must be auto_harness")

    config = auto_state.get("config")
    if not isinstance(config, dict):
        errors.append("auto_state.json: config must be an object")
        config = {}
    for key in ["goal", "scope", "metric", "direction", "verify", "run_mode"]:
        if not config.get(key):
            errors.append(f"auto_state.json: config.{key} is required")
    if config.get("direction") not in {"higher", "lower"}:
        errors.append("auto_state.json: config.direction must be higher or lower")
    if config.get("run_mode") not in {"foreground", "background"}:
        errors.append("auto_state.json: config.run_mode must be foreground or background")

    state = auto_state.get("state")
    if not isinstance(state, dict):
        errors.append("auto_state.json: state must be an object")
        state = {}
    for key in ["iteration", "baseline_metric", "current_metric", "best_metric", "last_status", "terminal_status"]:
        if key not in state:
            errors.append(f"auto_state.json: state.{key} is required")

    state_iteration = state.get("iteration")
    if not isinstance(state_iteration, int) or state_iteration < 0:
        errors.append("auto_state.json: state.iteration must be a non-negative integer")
    elif result_summary.get("highest_iteration") is not None and state_iteration != result_summary["highest_iteration"]:
        errors.append("auto_state.json: state.iteration must match the highest integer iteration in results.tsv")

    for key in ["baseline_metric", "current_metric", "best_metric"]:
        coerce_number(state.get(key), f"auto_state.json: state.{key}", errors)
    baseline_metric = coerce_number(state.get("baseline_metric"), "auto_state.json: state.baseline_metric", [])
    if baseline_metric is not None and result_summary.get("baseline_metric") is not None:
        if baseline_metric != result_summary["baseline_metric"]:
            errors.append("auto_state.json: state.baseline_metric must match results.tsv baseline metric")

    if state.get("last_status") not in AUTO_ROW_STATUSES:
        errors.append("auto_state.json: state.last_status must be a valid auto row status")
    elif result_summary.get("latest_main_status") is not None and state.get("last_status") != result_summary["latest_main_status"]:
        errors.append("auto_state.json: state.last_status must match the latest integer row in results.tsv")

    terminal_status = state.get("terminal_status")
    if terminal_status not in RUN_TERMINAL_STATUSES:
        errors.append("auto_state.json: state.terminal_status must be a valid harness terminal status")
    manifest_termination = manifest.get("termination")
    if isinstance(manifest_termination, dict):
        manifest_status = manifest_termination.get("status")
        if manifest_status not in RUN_TERMINAL_STATUSES:
            errors.append("manifest.json: termination.status must be a valid harness terminal status for auto_harness")
        elif terminal_status in RUN_TERMINAL_STATUSES and terminal_status != manifest_status:
            errors.append("auto_state.json: state.terminal_status must match manifest.json termination.status")


def check_auto_context(context: Any, run_mode: str | None, errors: list[str]) -> None:
    if not isinstance(context, dict):
        errors.append("context.json: must be a JSON object")
        return
    for key in ["version", "artifact_root", "primary_repo", "run_mode"]:
        if key not in context:
            errors.append(f"context.json: missing key '{key}'")
    if context.get("run_mode") not in {"foreground", "background"}:
        errors.append("context.json: run_mode must be foreground or background")
    if run_mode in {"foreground", "background"} and context.get("run_mode") != run_mode:
        errors.append("context.json: run_mode must match auto_state.json config.run_mode")


def check_auto_harness(run_dir: Path, manifest: Any, errors: list[str]) -> None:
    if not isinstance(manifest, dict) or manifest.get("mode") != "auto_harness":
        return

    for name in AUTO_REQUIRED_FILES:
        if not (run_dir / name).exists():
            errors.append(f"missing required auto_harness artifact: {name}")

    auto_state = load_json(run_dir / "auto_state.json", errors) if (run_dir / "auto_state.json").exists() else None
    context = load_json(run_dir / "context.json", errors) if (run_dir / "context.json").exists() else None
    rows = parse_auto_results(run_dir / "results.tsv", errors) if (run_dir / "results.tsv").exists() else []
    result_summary = check_auto_results(rows, errors)

    if auto_state is not None:
        check_auto_state(auto_state, manifest, result_summary, errors)
        config = auto_state.get("config") if isinstance(auto_state, dict) else None
        run_mode = config.get("run_mode") if isinstance(config, dict) else None
    else:
        run_mode = None
    if context is not None:
        check_auto_context(context, run_mode, errors)


def validate(run_dir: Path) -> list[str]:
    errors: list[str] = []
    installed_skills, reserved_skills = load_skill_inventory(errors)
    expert_roles = load_expert_roles(errors)
    check_required_files(run_dir, errors)

    manifest_path = run_dir / "manifest.json"
    manifest = None
    if manifest_path.exists():
        manifest = load_json(manifest_path, errors)
        check_manifest(manifest, expert_roles, errors)

    subagents = load_jsonl(run_dir / "subagents.jsonl", errors) if (run_dir / "subagents.jsonl").exists() else []
    skills = load_jsonl(run_dir / "skill_invocations.jsonl", errors) if (run_dir / "skill_invocations.jsonl").exists() else []
    escalations = load_jsonl(run_dir / "escalations.jsonl", errors) if (run_dir / "escalations.jsonl").exists() else []
    events = load_jsonl(run_dir / "events.jsonl", errors) if (run_dir / "events.jsonl").exists() else []
    tool_calls = load_jsonl(run_dir / "tool_calls.jsonl", errors) if (run_dir / "tool_calls.jsonl").exists() else []
    failures = load_jsonl(run_dir / "failures.jsonl", errors) if (run_dir / "failures.jsonl").exists() else []

    check_skill_invocations(skills, subagents, installed_skills, reserved_skills, errors)
    check_escalations(escalations, installed_skills, reserved_skills, expert_roles, errors)
    check_subagents(subagents, skills, escalations, installed_skills, reserved_skills, expert_roles, errors)
    check_team_policy(manifest, subagents, errors)
    check_auto_harness(run_dir, manifest, errors)
    check_typed_event_log(events, tool_calls, failures, errors)

    for name in ["metrics.json"]:
        path = run_dir / name
        if path.exists():
            data = load_json(path, errors)
            if data is not None and not isinstance(data, dict):
                errors.append(f"{name}: must be a JSON object")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a harness-engineer run directory")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.exists():
        print(f"FAIL: {run_dir} does not exist")
        return 1
    errors = validate(run_dir)
    if errors:
        print("FAIL: harness trace is invalid")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: harness trace is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Select a direct runtime subagent team and emit spawn task cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERT_LIBRARY = ROOT / "references" / "expert-capability-library.json"
FORBIDDEN_SKILLS = ["codex-autoresearch", "multi-agent", "expert-debate"]

TEAM_PRESETS = {
    "execution": [
        "Context Curator",
        "Runner Coordinator",
        "Verifier / Evidence Auditor",
    ],
    "standard_harness": [
        "Context Curator",
        "Harness Architect",
        "Verifier / Evidence Auditor",
    ],
    "algorithm_optimization": [
        "Algorithm Expert",
        "Experiment / Metrics Expert",
        "Verifier / Evidence Auditor",
    ],
    "failure_repair": [
        "Failure Analyst",
        "Mechanical Gatekeeper",
        "Verifier / Evidence Auditor",
    ],
    "high_risk_delivery": [
        "Red Team Critic",
        "Security / Reliability Expert",
        "Verifier / Evidence Auditor",
    ],
}

EXPLORER_ROLES = {
    "Context Curator",
    "Verifier / Evidence Auditor",
    "Failure Analyst",
    "Mechanical Gatekeeper",
    "Red Team Critic",
    "Security / Reliability Expert",
}


def role_to_agent_id(role: str) -> str:
    return role.lower().replace(" / ", "-").replace(" ", "-")


def load_library() -> dict[str, dict[str, Any]]:
    data = json.loads(EXPERT_LIBRARY.read_text(encoding="utf-8"))
    roles = data.get("roles", [])
    if not isinstance(roles, list):
        raise SystemExit("expert-capability-library.json roles must be a list")
    result: dict[str, dict[str, Any]] = {}
    for record in roles:
        if isinstance(record, dict) and isinstance(record.get("role"), str):
            result[record["role"]] = record
    return result


def build_message(role: str, goal: str, scope: str, profile: dict[str, Any]) -> str:
    capability = profile.get("capability_profile") if isinstance(profile, dict) else {}
    deliverables = capability.get("deliverables") if isinstance(capability, dict) else []
    focus = capability.get("verification_focus") if isinstance(capability, dict) else []
    deliverable_text = "; ".join(str(item) for item in deliverables[:2]) if isinstance(deliverables, list) else ""
    focus_text = "; ".join(str(item) for item in focus[:2]) if isinstance(focus, list) else ""
    return (
        f"You are the {role} for a harness-engineer direct runtime team. "
        f"Goal: {goal}. Scope: {scope or 'current task scope'}. "
        "Work in parallel with the main Codex orchestrator; do not own the critical path. "
        "Return concise findings, evidence paths, risks, and a terminal status. "
        f"Expected deliverable: {deliverable_text or 'role-specific report'}. "
        f"Verification focus: {focus_text or 'evidence-backed conclusions'}."
    )


def build_task_cards(task_class: str, goal: str, scope: str, risk_level: str, max_agents: int | None) -> dict[str, Any]:
    if task_class not in TEAM_PRESETS:
        allowed = ", ".join(sorted(TEAM_PRESETS))
        raise SystemExit(f"--task-class must be one of: {allowed}")
    roles = list(TEAM_PRESETS[task_class])
    if max_agents is not None:
        if max_agents < 2:
            raise SystemExit("--max-agents must be at least 2 for non-trivial runtime teams")
        roles = roles[:max_agents]
    library = load_library()
    cards: list[dict[str, Any]] = []
    for role in roles:
        profile = library.get(role, {})
        capability = profile.get("capability_profile") if isinstance(profile, dict) else {}
        allowed_skills = profile.get("allowed_skills") if isinstance(profile, dict) else []
        if not isinstance(allowed_skills, list):
            allowed_skills = []
        allowed = ["harness-engineer"]
        allowed.extend(str(skill) for skill in allowed_skills if isinstance(skill, str) and skill != "harness-engineer")
        cards.append(
            {
                "agent_id": role_to_agent_id(role),
                "role": role,
                "agent_type": "explorer" if role in EXPLORER_ROLES else "worker",
                "spawn_api": "spawn_agent",
                "spawn_timing": "before_implementation",
                "message": build_message(role, goal, scope, profile),
                "activation_criteria": capability.get("activation_criteria", []),
                "input_contract": capability.get("input_contract", []),
                "deliverables": capability.get("deliverables", []),
                "verification_focus": capability.get("verification_focus", []),
                "risk_flags": capability.get("risk_flags", []),
                "allowed_skills": allowed,
                "forbidden_skills": FORBIDDEN_SKILLS,
                "required_skill_check": True,
                "expected_lifecycle": [
                    "record_subagent_lifecycle.py --event created after spawn_agent returns",
                    "record_subagent_lifecycle.py --event completed|blocked|replaced after wait/close",
                ],
            }
        )
    return {
        "version": 1,
        "task_class": task_class,
        "goal": goal,
        "scope": scope,
        "risk_level": risk_level,
        "subagent_execution_mode": "runtime_subagents",
        "roles": roles,
        "task_cards": cards,
        "orchestrator_actions": [
            "Call spawn_agent once per task card before implementation.",
            "Record each returned runtime_agent_id or thread_id with record_subagent_lifecycle.py --event created.",
            "Keep goal decomposition, context trimming, integration, and final verification in the main thread.",
            "Call close_agent after each terminal result and record completed, blocked, stopped, or replaced.",
            "Create and record a replacement when a subagent is blocked, out of scope, stale, or unverifiable.",
        ],
    }


def format_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# Direct Runtime Team: {plan['task_class']}",
        "",
        f"- Goal: {plan['goal']}",
        f"- Scope: {plan['scope'] or 'current task scope'}",
        f"- Risk level: {plan['risk_level']}",
        f"- Execution mode: {plan['subagent_execution_mode']}",
        "",
        "## Task Cards",
    ]
    for card in plan["task_cards"]:
        lines.extend(
            [
                "",
                f"### {card['role']}",
                f"- agent_type: `{card['agent_type']}`",
                f"- spawn_api: `{card['spawn_api']}`",
                f"- agent_id: `{card['agent_id']}`",
                f"- message: {card['message']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a harness-engineer direct runtime subagent team")
    parser.add_argument("--task-class", choices=sorted(TEAM_PRESETS), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--scope", default="")
    parser.add_argument("--risk-level", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--max-agents", type=int, default=None)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    plan = build_task_cards(args.task_class, args.goal, args.scope, args.risk_level, args.max_agents)
    if args.format == "markdown":
        print(format_markdown(plan), end="")
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Subagent Runtime

Use this reference when the harness needs a dynamic internal agent team.

## Startup Runtime Hygiene

Run startup cleanup before creating new subagents, opening long-running terminal sessions, or launching harness subprocesses.

1. Inventory known runtime handles from the current conversation, previous harness state, `state_snapshots/`, terminal/session IDs, and any available agent/thread management APIs.
2. Classify each handle as `active`, `inactive`, `completed`, `failed`, `blocked`, `superseded`, `orphaned`, or `unknown`.
3. Close only safe inactive work: completed, failed, blocked with no pending user decision, superseded, over-budget, orphaned, or heartbeat-stale work. Never close a foreground command, a user-owned process, or a handle with uncertain ownership.
4. If a thread/process cap is reached, run this cleanup, retry the requested start once, then reduce team size or escalate with `environment_blocked` evidence.
5. Record every decision. The default record target is `runtime_cleanup.jsonl`; also append a compact `startup_cleanup` summary to `manifest.json` and an event to `events.jsonl`.

Use this JSONL shape for cleanup records:

```json
{
  "ts": "2026-05-06T10:00:00Z",
  "event": "startup_cleanup",
  "handle_id": "agent-123",
  "handle_type": "subagent",
  "previous_status": "blocked",
  "classification": "inactive",
  "action": "closed",
  "reason": "blocked over budget with no pending user decision",
  "evidence": ["subagents.jsonl", "state_snapshots/startup.json"]
}
```

Allowed `action` values are `kept`, `closed`, `skipped_uncertain`, `skipped_user_owned`, and `not_available`. If cleanup cannot be performed because the runtime exposes no handles, record `not_available` rather than silently skipping.

## Default Pattern

The main agent is the orchestrator. It owns final judgment, context selection, artifact integrity, and escalation decisions.

For non-trivial harness work, proactively form a small internal team at the start. Use multiple real runtime subagents by default for context isolation, parallel evidence, independent verification, or specialized failure analysis. Do not create subagents just to make simple work look sophisticated, but do not wait until failure to add basic context and verification roles.

The usual minimum runtime team is `Context Curator` plus `Verifier / Evidence Auditor`. Add `Harness Architect`, `Runner Coordinator`, `Failure Analyst`, or `Mechanical Gatekeeper` as soon as the task involves design, execution, repair, or enforceable rules. Expert roles must come from the generated `references/expert-capability-library.json`, with the readable view in `references/expert-capability-library.md`.

## Runtime Execution Modes

Internal experts should be real runtime subagents when possible. Before work begins, set `team_policy.subagent_execution_mode`:

- `runtime_subagents`: runtime agent/thread creation is available and permitted. This is the default for non-trivial work. Each created subagent record must include `runtime_agent_id`, `thread_id`, or an equivalent handle.
- `inline_expert_memos`: runtime agent/thread creation is unavailable, blocked by platform policy, blocked by the current user request, or still impossible after startup cleanup. Each created subagent record must include `runtime_blocked_category` and `runtime_blocked_reason`, and the run must log the fallback as an `events.jsonl` escalation.
- `single_agent_exception`: task is trivial enough that a team would be process overhead. Use only with `team_policy.single_agent_exception: true`.

Inline expert memos can preserve role discipline, but they are not a substitute for real subagent execution. Treat repeated `inline_expert_memos` on non-trivial work as a harness gap unless the user or platform policy blocks delegation.

## Task Card

Every subagent gets a task card:

```json
{
  "agent_id": "verifier-1",
  "role": "Verifier / Evidence Auditor",
  "scope": "verify candidate run against acceptance criteria",
  "activation_criteria": [
    "Use before claiming success on any non-trivial change, result, or document update."
  ],
  "input_contract": [
    "Acceptance criteria, changed files, command logs, metrics, generated artifacts, and source references."
  ],
  "deliverables": [
    "A verification report listing passed checks, failed checks, skipped checks, and residual risk."
  ],
  "verification_focus": [
    "Every success claim maps to a command, file, metric, or cited source."
  ],
  "risk_flags": [
    "Freshness gap between source data and written claims."
  ],
  "allowed_skills": ["software-engineer", "run-experiment", "analyze-results"],
  "forbidden_skills": ["codex-autoresearch", "multi-agent", "expert-debate"],
  "required_skill_check": true,
  "runtime_agent_id": "agent-abc123",
  "thread_id": null,
  "runtime_blocked_reason": null,
  "runtime_blocked_category": null,
  "needed_skill": null,
  "skill_route_decision": null,
  "allowlist_expanded_by": null,
  "inputs": ["manifest.json", "metrics.json", "summary.md"],
  "expected_output_schema": "verification_report.schema.json",
  "budget": {"max_minutes": 30, "max_tool_calls": 20},
  "stop_conditions": ["output_valid", "budget_exhausted", "blocked", "superseded"],
  "escalation_triggers": ["unclear_root_cause", "conflicting_agent_findings"]
}
```

Copy these capability fields from
`references/expert-capability-library.json` when creating a task card. They are
the role contract: `activation_criteria` explains why the role exists,
`input_contract` states what context the role needs, `deliverables` names the
expected output, `verification_focus` defines what the role must check, and
`risk_flags` identify conditions that should trigger escalation or replacement.

## Role Templates

- `Professor Orchestrator`: owns final synthesis, pipeline choice, and expert lifecycle.
- `Intent Router`: classifies task intent, required domains, and approval boundaries.
- `Context Curator`: builds the repo map, task context, doc index, and stale-context warnings.
- `Harness Architect`: designs run layout, tool contracts, state schema, and mechanical gates.
- `Runner Coordinator`: executes baseline or candidate runs within budget and records command evidence.
- `Verifier / Evidence Auditor`: checks acceptance criteria and refuses success without evidence.
- `Failure Analyst`: classifies failures and identifies missing context, tools, constraints, metrics, or environment support.
- `Mechanical Gatekeeper`: turns recurring guidance into executable checks.
- `Entropy Gardener`: scans drift, stale docs, duplicate helpers, bad fallbacks, and low-readability patterns.

## Lifecycle Rules

- Form the initial team before implementation for any non-trivial run.
- Create a subagent when the task is parallel, context-heavy, high-risk, or needs independent verification.
- Stop a subagent when its output is valid, stale, blocked, superseded, or over budget.
- At startup, stop or close inactive subagent threads before forming the new team.
- Replace a subagent when it exceeds scope, misuses skills, returns unverifiable output, or duplicates another role.
- Add a subagent when a new failure class, new metric, new runtime surface, or missing capability appears.
- Pause a subagent when it needs user input, external service recovery, or an escalation decision.

## Trace Fields

Record lifecycle events in `subagents.jsonl`:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "event": "created",
  "agent_id": "failure-analyst-1",
  "role": "Failure Analyst",
  "scope": "classify failed candidate run",
  "allowed_skills": ["analyze-results", "software-engineer"],
  "forbidden_skills": ["codex-autoresearch", "multi-agent", "expert-debate"],
  "required_skill_check": true,
  "runtime_agent_id": "agent-failure-1",
  "thread_id": null,
  "runtime_blocked_reason": null,
  "runtime_blocked_category": null,
  "status": "active",
  "reason": "candidate run failed with unclear root cause"
}
```

Every created subagent must later have a terminal event with `status` equal to `completed`, `stopped`, `replaced`, `failed`, or `blocked`, and a `stop_reason`.

Startup cleanup actions that close a prior subagent thread should also be reflected as a terminal lifecycle event in `subagents.jsonl` when the prior `agent_id` is known.

## Output Envelope

Subagents return concise structured output:

```json
{
  "status": "completed",
  "findings": [],
  "evidence": [],
  "artifacts_read": [],
  "artifacts_written": [],
  "skills_checked": [],
  "skills_used": [],
  "needed_skill": null,
  "skill_route_decision": null,
  "allowlist_expanded_by": null,
  "next_recommendation": "",
  "needed_escalation": null
}
```

The orchestrator should synthesize evidence, not votes.

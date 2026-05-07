# Skill Activation Policy

Use this reference when assigning work to internal subagents.

## Required Behavior

Each subagent must proactively check its `allowed_skills` before doing substantive work. Domain specialists may call external domain skills when those skills are in their task-card allowlist.

Required sequence:

1. Read the task card.
2. Inspect `allowed_skills`.
3. Decide which allowed skills match the task.
4. Load and follow matching skill instructions when available.
5. Record each decision in `skill_invocations.jsonl`.
6. If a needed skill is outside the allowlist, report `needed_skill` to the orchestrator instead of using it.

## Invocation Record

Append one record per skill decision:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "agent_id": "verifier-1",
  "skill": "analyze-results",
  "reason": "metrics.json must be compared against acceptance thresholds",
  "allowed": true,
  "used": true,
  "output_artifact": "subagent_outputs/verifier-1.md",
  "blocked_reason": null
}
```

If no skill applies, record:

```json
{
  "agent_id": "context-curator-1",
  "skill": null,
  "reason": "task is a small artifact indexing pass",
  "allowed": true,
  "used": false,
  "blocked_reason": "no_applicable_skill"
}
```

## Allowlist Rules

- `allowed_skills` is a hard boundary for subagents.
- `required_skill_check: true` means the run is invalid unless a skill decision is logged.
- Allowlist misses are harness gaps. Record them in `harness_gap_log.jsonl`.
- The orchestrator may expand an allowlist only after recording why the expansion is necessary.
- External domain skills are allowed when present in `allowed_skills`; they do not require `user_explicit_request=true`.
- Reserved orchestration skills (`codex-autoresearch`, `multi-agent`, `expert-debate`) require `user_explicit_request=true` even when listed.

## Common Allowlists

- Professor Orchestrator: `harness-engineer`, `planner`, `deep-interview`, `software-engineer`, `project-phase-report`
- Context Curator: `software-engineer`, `research-survey`, `doc`, `pdf`, `spreadsheet`, `jupyter-notebook`
- Harness Architect: `skill-creator`, `plugin-creator`, `software-engineer`, `repo-refactor-governance`, `waterfall-delivery`
- Runner Coordinator: `run-experiment`, `monitor-experiment`, `experiment-bridge`, `software-engineer`
- Verifier / Evidence Auditor: `analyze-results`, `playwright`, `paper-compile`, `pdf`, `spreadsheet`
- Domain specialists: use the role-specific allowlists generated in `references/expert-capability-library.json` and rendered in `references/expert-capability-library.md`.
- When installed skills change, run `scripts/update_skill_inventory.py` and `scripts/update_expert_library.py` before assigning new domain specialists.

Use only skills that are actually available in the current session. If a listed skill is unavailable, log it as blocked.

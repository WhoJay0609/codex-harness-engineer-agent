# Skill Routing Policy

Use this reference when a subagent needs to call a skill.

## Skill Classes

- `core_harness_skill`: built-in harness behavior and local harness maintenance. These are used by the Professor Orchestrator and core council.
- `external_domain_skill`: installed skills for specific domains such as paper writing, frontend, model training, RAG, deployment, documents, and security. Subagents may use these when they appear in the task-card `allowed_skills`.
- `reserved_orchestration_skill`: `codex-autoresearch`, `multi-agent`, and `expert-debate`. Their core capabilities are internalized in harness protocols. They are blocked unless the user explicitly requests that exact external skill.

Code Auto Research as a design pattern is internalized in `auto_harness`. The external `$codex-autoresearch` skill remains reserved because invoking it changes orchestration ownership.

The installed inventory lives in `references/skill-inventory.json`. A skill reference may match either a skill directory `id` or SKILL frontmatter `name`.

## Subagent Rules

1. A subagent reads its task card before substantive work.
2. It may use only skills listed in `allowed_skills`.
3. Every skill decision is recorded in `skill_invocations.jsonl`, including no-op decisions.
4. External domain skills do not require `user_explicit_request=true` when they are in `allowed_skills`.
5. Reserved orchestration skills require `user_explicit_request=true` and an `escalations.jsonl` record.
6. If a needed skill is outside the allowlist, the subagent returns `needed_skill` and stops or continues without that skill.

## Allowlist Expansion

The Professor Orchestrator may expand a task-card allowlist only when all are true:

- the requested skill exists in `skill-inventory.json`;
- the skill is not a reserved orchestration skill, or the user explicitly requested it;
- the expansion reason is recorded in `escalations.jsonl`;
- the subagent record includes `skill_route_decision` and `allowlist_expanded_by`.

Example subagent record:

```json
{
  "agent_id": "paper-writing-1",
  "event": "updated",
  "needed_skill": "academic-plotting",
  "skill_route_decision": "expand_allowlist",
  "allowlist_expanded_by": "professor-orchestrator-1"
}
```

## Validation Contract

Validators should reject:

- unknown skills in task cards or skill invocations;
- used skills that are not in the subagent's `allowed_skills`;
- reserved orchestration skills without `user_explicit_request=true`;
- `needed_skill` requests that have no routing decision;
- allowlist expansion without an orchestrator decision.

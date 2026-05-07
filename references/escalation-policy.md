# Escalation Policy

Use this reference when an internal expert hits a blocker or the orchestrator must add, replace, or stop experts.

## Default

Start with the internal harness expert team. Escalation here means an expert or run result forces the orchestrator to change the core council, add a domain specialist, expand a skill allowlist, or stop/replace a stale expert. `$codex-autoresearch`, `$multi-agent`, and `$expert-debate` are reserved orchestration skills; use them only when the user explicitly asks.

## Must Consider Internal Team Change

The orchestrator must consider adding, stopping, or replacing an internal expert when any condition is true:

- The task spans multiple domains such as architecture, experiments, paper claims, product UX, security, deployment, or operations.
- Two consecutive runs fail and the root cause is unclear or changes between runs.
- Success criteria, core metrics, baselines, fairness assumptions, or experiment protocol would change.
- Budget, tool access, external dependencies, or subagent roles would expand materially.
- The next action is high-risk: large refactor, migration, release, security-sensitive change, or irreversible git operation.
- Internal subagents disagree and artifact evidence cannot resolve the conflict.
- The user explicitly asks for a new internal expert role.

## Subagent Escalation Request

Internal experts do not independently broaden the team, expand skill access, or call `$codex-autoresearch`, `$expert-debate`, or `$multi-agent`. They return:

```json
{
  "status": "blocked",
  "needed_internal_expert": "Red Team Critic",
  "reason": "root cause conflicts across verifier and runner findings",
  "recommended_roles": ["Red Team Critic", "Verifier / Evidence Auditor"],
  "needed_skill": null
}
```

The orchestrator decides whether to add, stop, or replace experts; records the decision; and owns the final synthesis.

## Escalation Record

Append internal team changes to `escalations.jsonl`:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "triggered_by": "failure-analyst-1",
  "trigger": "unclear_root_cause",
  "internal_expert_action": "add",
  "role": "Red Team Critic",
  "reason": "failure impact and reversibility are unclear",
  "decision": "add Red Team Critic for next round",
  "accepted": true
}
```

If the user explicitly requests `$codex-autoresearch`, `$multi-agent`, or `$expert-debate`, record it as `event: external_skill_used` with `user_explicit_request: true`.

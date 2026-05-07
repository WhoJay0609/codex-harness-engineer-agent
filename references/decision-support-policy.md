# Decision Support Policy

Use this reference when the main orchestrator decides whether to use internal experts, built-in auto mode, or explicitly requested external skills.

## Default Stance

The harness orchestrator should be proactive, not passive. At each major boundary, choose core council experts and domain specialists from `harness-experts.v3` to improve evidence, risk control, or strategy quality.

Major boundaries include:

- Initial harness design.
- Choosing subagent roles and skill allowlists.
- Selecting success criteria, metrics, baselines, budgets, or stop conditions.
- Changing the plan after a failed run.
- Accepting or rejecting a subagent recommendation.
- Before high-risk, cross-domain, expensive, or irreversible work.

## Use Internal Experts First

Use the internal expert library for adversarial review, tradeoff analysis, risk pressure, broad domain coverage, and role-specialized work. Domain specialists may call external domain skills from their task-card allowlist. When runtime subagents are available and permitted, create real subagents for these roles rather than running all roles as untracked main-agent thoughts.

Good mappings:

- Need critique or red-team pressure: `Red Team Critic`, `Debate Moderator`, `Verifier / Evidence Auditor`.
- Need broad role-specialized coverage: select the task-class preset in `team-formation-policy.md`.
- Need parallel evidence: create separate internal experts with non-overlapping scopes.
- Need debate-like disagreement: ask `Debate Moderator`, `Red Team Critic`, and `Verifier / Evidence Auditor` to challenge the plan, then synthesize as orchestrator.

If runtime subagent creation is blocked, record `inline_expert_memos` and the exact reason before continuing. The fallback should be visible in `manifest.json`, `subagents.jsonl`, and `events.jsonl`.

## External Skills Policy

Do not call `$codex-autoresearch`, `$multi-agent`, or `$expert-debate` proactively. They are reserved orchestration skills for this harness and are allowed only when the user explicitly requests them in the current task. Use built-in Auto Harness Mode and internal deliberation by default.

When the user explicitly requests reserved orchestration skills, record:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "event": "external_skill_used",
  "external_skill": "multi-agent",
  "user_explicit_request": true,
  "reason": "user explicitly requested $multi-agent",
  "summary": "External expert result summarized here.",
  "decision": "accepted_or_rejected_by_orchestrator"
}
```

If there is no explicit user request, choose internal experts, domain specialists, or built-in Auto Harness Mode instead.

## Orchestrator Authority

Subagents may recommend new internal experts, but only the orchestrator decides whether to create, stop, replace, or add experts. The orchestrator owns final synthesis.

# Team Formation Policy

Use this reference at the start of a harness run.

## Default

For non-trivial harness work, the orchestrator should create a small core council and any required domain specialists from `harness-experts.v3` before main execution. The team can be lightweight, but it should exist early enough to shape context, verification, and failure handling rather than only after something breaks.

Use single-agent mode only for trivial inspection, tiny edits, or one-command checks. When using single-agent mode, record the reason in `manifest.json`.

## Manifest Policy

Every run manifest must include:

```json
{
  "team_policy": {
    "mode": "internal_team",
    "task_class": "standard_harness",
    "expert_library_version": "harness-experts.v3",
    "reason": "non-trivial harness design needs context curation and independent verification",
    "initial_roles": ["Professor Orchestrator", "Intent Router", "Context Curator", "Verifier / Evidence Auditor"],
    "single_agent_exception": false,
    "skill_policy": "external_domain_allowed_by_allowlist",
    "reserved_orchestration_policy": "explicit_user_request_only"
  }
}
```

For a single-agent exception:

```json
{
  "team_policy": {
    "mode": "single_agent",
    "task_class": "trivial",
    "expert_library_version": "harness-experts.v3",
    "reason": "tiny read-only artifact inspection with no design or verification branch",
    "initial_roles": [],
    "single_agent_exception": true,
    "skill_policy": "external_domain_allowed_by_allowlist",
    "reserved_orchestration_policy": "explicit_user_request_only"
  }
}
```

## Initial Team Presets

### `standard_harness`

Start with:

- `Professor Orchestrator`
- `Intent Router`
- `Context Curator`
- `Harness Architect`
- `Verifier / Evidence Auditor`

### Execution Or Experiment Work

Start with:

- `Professor Orchestrator`
- `Context Curator`
- `Runner Coordinator`
- `Verifier / Evidence Auditor`

### `research_idea`

Start with:

- `Professor Orchestrator`
- `Intent Router`
- `Research Ideation Expert`
- `Literature / Novelty Expert`
- `Debate Moderator`
- `Red Team Critic`

### `paper_to_code`

Start with:

- `Professor Orchestrator`
- `Paper-to-Code Expert`
- `Harness Architect`
- `Experiment / Metrics Expert`
- `Verifier / Evidence Auditor`

### `algorithm_optimization`

Start with:

- `Professor Orchestrator`
- `Algorithm Expert`
- `Experiment / Metrics Expert`
- `Verifier / Evidence Auditor`
- `Red Team Critic`

### `full_stack_feature`

Start with:

- `Professor Orchestrator`
- `Harness Architect`
- `Frontend / Design Expert`
- `Backend / API Expert`
- `Verifier / Evidence Auditor`

### `failure_repair`

Start with:

- `Failure Analyst`
- `Verifier / Evidence Auditor`
- `Mechanical Gatekeeper`

### `high_risk_delivery`

Start with:

- `Red Team Critic`
- `Security / Reliability Expert`
- `Deploy Expert`
- `Verifier / Evidence Auditor`
- `Mechanical Gatekeeper`

### `material_organization`

Start with:

- `Documents / Materials Expert`
- `Project Delivery Expert`
- `Knowledge / Notion Expert`
- `Context Curator`

For high-risk or cross-domain work, use 5-7 experts. Domain specialists may call external domain skills from their generated allowlist. Do not call `$codex-autoresearch`, `$multi-agent`, or `$expert-debate` unless the user explicitly asks for those skills.

## Formation Loop

1. Classify the task as `trivial`, `standard_harness`, `execution`, `research_idea`, `paper_to_code`, `algorithm_optimization`, `full_stack_feature`, `failure_repair`, `high_risk_delivery`, or `material_organization`.
2. Choose the smallest preset that covers the task.
3. Add domain specialists only after the core council identifies the domain, using the latest `references/expert-capability-library.json`.
4. Create task cards before implementation begins.
5. Record each creation event in `subagents.jsonl`.
6. Let subagents run early context, verification, or failure-analysis passes.
7. Stop or replace subagents quickly when they become stale, duplicate, or blocked.

## Anti-Patterns

- Waiting until the end to create a verifier.
- Creating one broad subagent that does the entire task.
- Letting the orchestrator skip team formation for a non-trivial task without a recorded reason.
- Keeping stale subagents active after their evidence has been superseded.

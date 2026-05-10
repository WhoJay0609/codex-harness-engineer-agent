# Mechanical Gates

Use this reference when converting guidance into executable checks. For required
run files and field ownership, read `references/artifact-contract.md` before
changing validators.

## Gate Types

- Artifact gates: required files exist and parse.
- Schema gates: JSON and JSONL records contain required keys; Trace v2 events follow `references/schemas/harness-event.schema.json`.
- Trace gates: event IDs are unique, `parent_id` points backward, tool calls have observations, failures have `error_kind`, and termination is explicit.
- Lifecycle gates: every created subagent terminates with a stop reason.
- Runtime-subagent gates: non-trivial `runtime_subagents` runs record multiple concrete `spawn_agent` return handles, reject placeholders, and terminally close every created subagent; `inline_expert_memos` is accepted only with a blocked category, blocked reason, per-subagent fallback fields, and an observable fallback event.
- Startup cleanup gates: `manifest.json` includes `startup_cleanup`; any startup cleanup action that closed, skipped, or could not inspect a handle has a corresponding `runtime_cleanup.jsonl` record.
- Skill gates: subagents with `required_skill_check` have skill invocation records, used skills are installed, and used skills are inside the subagent allowlist.
- Escalation gates: internal expert additions/stops/replacements are recorded; reserved `$codex-autoresearch`, `$multi-agent`, or `$expert-debate` use requires `user_explicit_request=true`; external domain skills are allowed by task-card allowlist.
- Verification gates: success requires tests, metrics, screenshots, logs, or review evidence.
- Architecture gates: dependency, layering, naming, and file-size rules are checked mechanically.
- Documentation gates: behavior changes update the repo record system.
- Self-eval gates: skill changes run `scripts/run_harness_evals.py` before publication.

## Error Message Style

Gate errors should tell the agent how to fix the harness:

```text
FAIL: subagent verifier-1 has no skill_invocations record.
Fix: append a skill check record to skill_invocations.jsonl, or set required_skill_check=false with a reason in subagents.jsonl.
```

## Minimum Valid Run

The default validator should require:

```text
manifest.json
subagents.jsonl
skill_invocations.jsonl
escalations.jsonl
events.jsonl
tool_calls.jsonl
failures.jsonl
metrics.json
summary.md
replay.md
```

Use stricter gates for production harnesses.

If a run starts subagents or long-running processes, the validator should also check that `manifest.json.startup_cleanup` exists. Require `runtime_cleanup.jsonl` when `startup_cleanup.closed_count`, `startup_cleanup.skipped_count`, or `startup_cleanup.unavailable_count` is greater than zero.

## Gate Ownership

The Mechanical Gatekeeper proposes and validates gates. The orchestrator decides whether the gate becomes required for the current run. Repeated human review comments should normally become gates.

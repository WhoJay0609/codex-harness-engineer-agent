---
name: harness-engineer
description: Build and operate agent-first harnesses for reproducible, comparable, iterative AI agent work. Use when creating or improving repo-native feedback loops, autonomous foreground-first auto harness loops, agent-readable context, mechanical gates, traces, startup cleanup of inactive agent threads, proactively formed core and domain expert teams, external domain skill allowlists, run artifacts, failure analysis, and reserved orchestration skill policy.
---

# Harness Engineer

Use this skill to design the harness around agents: environment, constraints, feedback loops, artifacts, internal expert roles, skill activation, verification gates, decision support, escalation policy, and foreground-first autonomous loops. The goal is not "more agents"; it is reliable agent execution with evidence.

## Core Principles

- Humans steer; agents execute. Convert user intent into success criteria, constraints, and feedback loops.
- The repo is the record system. Decisions, plans, validation, failures, and harness rules should become discoverable versioned artifacts.
- Use maps, not manuals. Keep entry instructions short and point to deeper references only when needed.
- Enforce invariants mechanically. Prefer schemas, linters, tests, trace validators, and CI over reminders.
- Optimize for agent readability. Make context, runtime state, logs, metrics, and UI behavior inspectable by agents.
- Treat failures as harness gaps. Ask what context, tool, constraint, metric, or feedback loop was missing.
- Iterate until the goal is met or a bounded stop condition is reached; never silently declare success without evidence.
- Bound autonomy with mechanical metrics, fast verification, explicit rollback, and traceable keep/discard decisions.

## Required Workflow

1. Define the goal, success criteria, budget, stop conditions, and expected artifacts.
2. Inspect the repo or workspace map before designing the harness.
3. For `auto_harness` work, perform a read-only launch scan and at least one confirmation round before the loop starts. Default to foreground mode; use background runtime only when the user explicitly chooses it. Read `references/auto-harness-mode.md`.
4. Before starting new agent threads, subagents, long-running commands, or harness subprocesses, perform startup runtime hygiene: identify stale or inactive threads/processes from the available runtime state, close only safe inactive work, and record what was kept, closed, skipped, or uncertain. If a runtime/thread limit is reached, clean inactive work first and retry once before reducing team size or escalating.
5. For non-trivial harness work, classify the task and proactively create a small core council and any needed domain specialists from `harness-experts.v3` before main execution. Use single-agent mode only for trivial inspection or tiny edits, and record the skip reason in `manifest.json`.
6. Give each subagent a task card with `role`, `scope`, `allowed_skills`, `forbidden_skills`, `required_skill_check`, `inputs`, `expected_output_schema`, `budget`, `stop_conditions`, and `escalation_triggers`.
7. Require every subagent to proactively check and use applicable skills from its allowlist. External domain skills are allowed when listed in `allowed_skills`. If a needed skill is outside the allowlist, the subagent reports `needed_skill` to the orchestrator.
8. Record all runs, startup cleanup actions, tool calls, skill checks, failures, escalations, metrics, auto-loop decisions, and harness gaps.
9. Verify with real evidence. If verification fails, classify whether to fix code, improve context, add a tool, add a mechanical gate, update docs, add or stop a subagent, or escalate.
10. Use the internal expert library for critique, risk review, cross-domain coverage, role-specialized work, and auto-loop hypothesis generation.
11. Treat `$codex-autoresearch`, `$multi-agent`, and `$expert-debate` as reserved orchestration skills. Do not call them unless the user explicitly requests those skills; record explicit reserved skill use in `escalations.jsonl`.
12. Prefer Trace v2 typed events in `events.jsonl` for new harness runs. Every tool call should have a matching observation, failures should include `error_kind`, and termination should be explicit.
13. End only with `goal_met`, `budget_exhausted`, `policy_blocked`, `environment_blocked`, `user_decision_needed`, or `failed_with_evidence`.

## Artifact Contract

For each run, prefer this layout:

```text
runs/<experiment_id>/<run_id>/
  manifest.json
  team_graph.json
  subagents.jsonl
  skill_invocations.jsonl
  escalations.jsonl
  events.jsonl
  tool_calls.jsonl
  runtime_cleanup.jsonl
  failures.jsonl
  metrics.json
  auto_state.json
  results.tsv
  context.json
  harness_gap_log.jsonl
  state_snapshots/
  summary.md
  replay.md
```

Minimum viable run: `manifest.json`, `subagents.jsonl`, `skill_invocations.jsonl`, `events.jsonl`, `tool_calls.jsonl`, `failures.jsonl`, `metrics.json`, `summary.md`, and `replay.md`. `manifest.json` must include `team_policy` with `expert_library_version` and a `startup_cleanup` summary. If `manifest.json` uses `mode: "auto_harness"`, the run also needs `auto_state.json`, `results.tsv`, and `context.json`. Background auto runs may add `launch.json`, `runtime.json`, and `runtime.log`, but foreground is the default. If any inactive thread, subagent, terminal session, or subprocess is closed or skipped during startup hygiene, record the detailed action in `runtime_cleanup.jsonl` and cross-reference it from `events.jsonl`.

Trace v2 events should follow `references/schemas/harness-event.schema.json`. Keep `events.jsonl` append-only and use `event_id`, `parent_id`, `source`, `event_type`, `agent_id`, `role`, `tool_call_id`, `skill`, `status`, `error_kind`, `files_changed`, and `command_hash` when applicable.

## Reference Loading

- For first principles and OpenAI-style harness framing, read `references/harness-principles.md`.
- For foreground-first autonomous improve/verify loops, read `references/auto-harness-mode.md`.
- For the generated expert capability library, read `references/expert-capability-library.md` and `references/expert-capability-library.json`.
- For installed skill classes, domain skill allowlists, and reserved orchestration skill rules, read `references/skill-routing-policy.md` and `references/skill-inventory.json`.
- For Trace v2 event structure, read `references/schemas/harness-event.schema.json`.
- When installed skills change, refresh `references/skill-inventory.json` with `scripts/update_skill_inventory.py`, then refresh the expert library with `scripts/update_expert_library.py`.
- For proactive internal team formation and single-agent exceptions, read `references/team-formation-policy.md`.
- For startup cleanup, dynamic subagent creation, stopping, replacement, and trace fields, read `references/subagent-runtime.md`.
- For proactive skill usage by subagents, read `references/skill-activation-policy.md`.
- For explicit-request-only `$codex-autoresearch`, `$expert-debate`, and `$multi-agent` policy, read `references/decision-support-policy.md`.
- For when subagent issues require external review, read `references/escalation-policy.md`.
- For iterative repair loops and run states, read `references/feedback-loop.md`.
- For schemas, validators, lint-like gates, and artifact checks, read `references/mechanical-gates.md`.
- For drift cleanup, stale docs, duplicate patterns, and quality gardening, read `references/entropy-garbage-collection.md`.

## Script Use

- Use `scripts/validate_harness_trace.py <run_dir>` before trusting a run.
- Use `scripts/replay_harness_run.py <run_dir>` to render a readable replay from artifacts.
- Use `scripts/query_harness_trace.py <run_dir> ...` to inspect events, tool calls, skill decisions, failures, and subagent records.
- Use `scripts/export_trace_table.py <run_dir>` to export artifacts as CSV or JSONL.
- Use `scripts/run_harness_evals.py` to run harness self-evals before publishing skill changes.
- Use `scripts/compare_runs.py <run_dir>...` to compare baseline and candidate runs.
- Use `scripts/summarize_failures.py <run_dir>...` to aggregate failure causes.
- Use `scripts/update_skill_inventory.py` to scan installed skills and write `references/skill-inventory.json`.
- Use `scripts/update_expert_library.py` to rebuild `references/expert-capability-library.json` and `references/expert-capability-library.md` from the current skill inventory.
- Use `scripts/check_harness_consistency.py <skill_or_harness_dir>` to check skill/reference/script consistency.

If a script reports missing artifacts, stale inventory, stale expert library output, or invalid state, fix the harness evidence before claiming the task is complete.

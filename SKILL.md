---
name: harness-engineer
description: Build and operate agent-first harnesses for reproducible, comparable, iterative AI agent work. Use when creating or improving repo-native feedback loops, autonomous foreground-first auto harness loops, agent-readable context, mechanical gates, traces, startup cleanup of inactive agent threads, proactively formed core and domain expert teams, external domain skill allowlists, run artifacts, failure analysis, and reserved orchestration skill policy.
---

# Harness Engineer

Use this skill to design the system around agent work: goal framing, context
delivery, runtime hygiene, expert roles, skill routing, feedback loops,
mechanical gates, trace artifacts, and evidence-backed termination.

The goal is not "more agents". The goal is reliable execution with inspectable
evidence.

## Mental Model

Harness engineering has seven layers:

1. Intent: goal, scope, budget, stop conditions, and success criteria.
2. Context: repo map, prior runs, constraints, local instructions, and risks.
3. Team: single-agent exception, inline expert fallback, or real runtime
   subagents when the request and platform permit delegation.
4. Tools: skill allowlists, shell/browser/runtime access, and guard commands.
5. Artifacts: manifests, traces, logs, metrics, replay, and summaries.
6. Loop: baseline, change, verify, keep/discard, recover, and terminate.
7. Maintenance: refresh skill inventory, expert library, schemas, and evals as
   the surrounding Codex skill set changes.

Read `references/framework.md` for the full architecture map.

## Operating Modes

- `standard_harness`: design or improve a reproducible agent workflow.
- `auto_harness`: run a foreground-first improve/verify loop over a measurable
  target. This is the built-in Code Auto Research style mode.
- `maintenance`: update this skill package, references, generated expert
  library, or validation scripts.
- `single_agent_exception`: trivial read-only checks, tiny edits, or one-command
  validation. Record the reason when artifacts are produced.

For codebase optimization loops, read `references/code-autoresearch-integration.md`
and `references/auto-harness-mode.md`.

## Required Workflow

1. Frame the work: state the goal, scope, primary metric, guard, budget, stop
   condition, and expected artifacts.
2. Inspect first: read the repo or skill package map before designing or
   editing the harness.
3. Choose the mode and team policy: classify the task, decide
   `team_policy.subagent_execution_mode`, and create real runtime subagents
   when the current request and platform policy permit delegation.
4. Route skills deliberately: use generated expert allowlists for domain work;
   keep `$codex-autoresearch`, `$multi-agent`, and `$expert-debate` explicit
   request only.
5. Record evidence: write Trace v2 events, tool observations, failures, metrics,
   skill decisions, runtime cleanup, and terminal status when producing a run.
6. Iterate mechanically: measure a baseline, make one focused change or
   experiment, verify, guard, keep or discard, and log the decision.
7. Maintain the harness: when rules, installed skills, or artifact contracts
   change, update references, scripts, eval fixtures, README, and generated
   expert library together.

End only with `goal_met`, `budget_exhausted`, `policy_blocked`,
`environment_blocked`, `user_decision_needed`, or `failed_with_evidence`.

## Artifact Contract

Minimum viable harness run:

```text
runs/<experiment_id>/<run_id>/
  manifest.json
  subagents.jsonl
  skill_invocations.jsonl
  events.jsonl
  tool_calls.jsonl
  failures.jsonl
  metrics.json
  summary.md
  replay.md
```

Full runs may also include `team_graph.json`, `escalations.jsonl`,
`runtime_cleanup.jsonl`, `auto_state.json`, `results.tsv`, `context.json`,
`harness_gap_log.jsonl`, and `state_snapshots/`.

`manifest.json` must include `team_policy.expert_library_version`,
`team_policy.subagent_execution_mode`, and startup cleanup summary. If the mode
is `runtime_subagents`, created subagents need `runtime_agent_id`, `thread_id`,
or an equivalent handle. If the mode is `inline_expert_memos`, the manifest and
subagent records must explain the fallback reason.

Trace v2 events follow `references/schemas/harness-event.schema.json`.

## Reference Map

Architecture:

- `references/framework.md`: skill structure, layer model, and ownership map.
- `references/harness-principles.md`: first principles and source inspiration.
- `references/auto-harness-mode.md`: foreground-first autonomous improve/verify
  loop.
- `references/code-autoresearch-integration.md`: Code Auto Research patterns and
  related projects.

Team and runtime:

- `references/expert-capability-library.md` and
  `references/expert-capability-library.json`: generated `harness-experts.v3`
  role library.
- `references/team-formation-policy.md`: proactive team selection and
  single-agent exceptions.
- `references/subagent-runtime.md`: startup cleanup, runtime subagents, fallback
  modes, stop/replace rules, and trace fields.

Skill routing and escalation:

- `references/skill-routing-policy.md` and `references/skill-inventory.json`:
  installed skill classes, allowlists, and reserved orchestration skills.
- `references/skill-activation-policy.md`: proactive skill checks by subagents.
- `references/decision-support-policy.md`: explicit-request-only policy for
  reserved orchestration skills.
- `references/escalation-policy.md`: adding, stopping, replacing, or escalating
  expert work.

Evidence and maintenance:

- `references/feedback-loop.md`: iteration states, failure records, and harness
  gap records.
- `references/mechanical-gates.md`: validators, schemas, CI gates, and artifact
  checks.
- `references/entropy-garbage-collection.md`: drift cleanup and quality
  gardening.

## Script Map

- Validate runs: `scripts/validate_harness_trace.py <run_dir>`
- Replay runs: `scripts/replay_harness_run.py <run_dir>`
- Query traces: `scripts/query_harness_trace.py <run_dir> ...`
- Export traces: `scripts/export_trace_table.py <run_dir>`
- Compare runs: `scripts/compare_runs.py <run_dir>...`
- Summarize failures: `scripts/summarize_failures.py <run_dir>...`
- Refresh skill inventory: `scripts/update_skill_inventory.py`
- Refresh expert library: `scripts/update_expert_library.py`
- Run self-evals: `scripts/run_harness_evals.py`
- Check package consistency:
  `scripts/check_harness_consistency.py <skill_or_harness_dir>`

If a script reports missing artifacts, stale generated files, or invalid state,
fix the harness evidence before claiming the task is complete.

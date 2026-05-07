# Artifact Contract

Use this reference when creating, validating, replaying, or evolving harness run
artifacts.

## Run Directory

Prefer this layout:

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

Minimum viable run:

```text
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

`auto_harness` runs also need `auto_state.json`, `results.tsv`, and
`context.json`. Background auto runs may add `launch.json`, `runtime.json`, and
`runtime.log`.

## File Responsibilities

- `manifest.json`: run identity, goal, mode, success criteria, terminal status,
  startup cleanup summary, and `team_policy`.
- `team_graph.json`: optional explicit role graph, dependencies, and ownership
  boundaries.
- `subagents.jsonl`: lifecycle events for each role or runtime subagent.
- `skill_invocations.jsonl`: skill checks, use/no-use decisions, and blocked
  skill reasons.
- `escalations.jsonl`: allowlist expansion, reserved skill use, external review,
  or user-decision boundaries.
- `events.jsonl`: Trace v2 append-only event stream.
- `tool_calls.jsonl`: material command/tool invocations and normalized outputs
  when separate from Trace v2 events.
- `runtime_cleanup.jsonl`: startup cleanup actions for stale threads,
  subprocesses, terminals, or runtime handles.
- `failures.jsonl`: failed checks, crashes, policy blocks, environment blocks,
  and harness gaps with evidence.
- `metrics.json`: baseline, current, best, and final measured values.
- `auto_state.json`: resumable state for `auto_harness`.
- `results.tsv`: iteration ledger for `auto_harness`.
- `context.json`: repo root, run cwd, scope, verify cwd, runtime mode, and
  reusable context handles.
- `harness_gap_log.jsonl`: reusable harness improvements discovered during the
  run.
- `state_snapshots/`: optional point-in-time copies of important state.
- `summary.md`: short final report.
- `replay.md`: chronological human-readable reconstruction from artifacts.

## Manifest Requirements

`manifest.json` must include run identity, goal, success criteria,
`team_policy.expert_library_version`, `team_policy.subagent_execution_mode`,
startup cleanup summary, and explicit termination status.

Terminal status must be one of:

- `goal_met`
- `budget_exhausted`
- `policy_blocked`
- `environment_blocked`
- `user_decision_needed`
- `failed_with_evidence`

## Subagent Execution Fields

When `team_policy.subagent_execution_mode` is `runtime_subagents`, every created
subagent record must include `runtime_agent_id`, `thread_id`, or an equivalent
runtime handle.

When the mode is `inline_expert_memos`, the manifest must include
`team_policy.subagent_runtime_blocked_reason`, and each created subagent record
must include `runtime_blocked_reason`.

When the mode is `single_agent_exception`, `team_policy.mode` should be
`single_agent`, `initial_roles` should be empty, and the reason should explain
why team formation would be process overhead.

## Trace V2 Requirements

`events.jsonl` should follow `references/schemas/harness-event.schema.json`.

Every material `tool_call` should have a matching `observation`. Failures should
include `error_kind`. Termination should be explicit and match `manifest.json`.

Keep `events.jsonl` append-only. Do not rewrite history to hide failed steps.

## Validation

Before trusting a run:

```bash
python scripts/validate_harness_trace.py runs/<experiment_id>/<run_id>
python scripts/replay_harness_run.py runs/<experiment_id>/<run_id>
```

Use `scripts/query_harness_trace.py` and `scripts/export_trace_table.py` for
inspection and downstream analysis.

For executable `auto_harness` runs, prefer the helper scripts:

```bash
python scripts/init_auto_harness.py --run-dir runs/<experiment_id>/<run_id> ...
python scripts/record_auto_iteration.py --run-dir runs/<experiment_id>/<run_id> ...
python scripts/run_auto_harness.py --run-dir runs/<experiment_id>/<run_id> --iteration-command '<cmd>'
python scripts/harness_runtime_ctl.py launch --run-dir runs/<experiment_id>/<run_id> --iteration-command '<cmd>'
```

Background runs add `launch.json`, `runtime.json`, and `runtime.log`.

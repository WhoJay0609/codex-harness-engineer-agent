# Artifact Tour

Harness runs are plain files. This keeps the record easy to inspect, commit,
diff, archive, or feed into downstream analysis.

## Minimal Run

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

## Auto Harness Extras

```text
auto_state.json
results.tsv
context.json
```

## File Responsibilities

| File | Purpose |
| --- | --- |
| `manifest.json` | Run identity, mode, goal, team policy, startup cleanup, termination. |
| `subagents.jsonl` | Created, completed, blocked, failed, stopped, and replaced subagent lifecycle. |
| `skill_invocations.jsonl` | Which skill each subagent checked or used, and whether it was allowed. |
| `events.jsonl` | Trace v2 stream for plans, tool calls, observations, metrics, failures, and termination. |
| `tool_calls.jsonl` | Optional extracted tool-call table for search/export. |
| `failures.jsonl` | Structured failure records and recovery hints. |
| `metrics.json` | Current metric snapshot. |
| `summary.md` | Human-readable current state. |
| `replay.md` | Ordered replay notes. |
| `results.tsv` | Auto-harness baseline and iteration decisions. |
| `auto_state.json` | Resume state for foreground/background loops. |
| `context.json` | Primary repo, scope, verify cwd, and run mode. |

## Validate

```bash
python3 scripts/validate_harness_trace.py evals/cases/valid_trace_v2
```

Expected output:

```text
PASS: harness trace is valid
```

## Replay

```bash
python3 scripts/replay_harness_run.py evals/cases/valid_trace_v2
```

## Query

```bash
python3 scripts/query_harness_trace.py evals/cases/valid_trace_v2 --event-type tool_call
```

## Export

```bash
python3 scripts/export_trace_table.py evals/cases/valid_trace_v2 --format csv
```

## Common Validator Failures

- A created subagent has no terminal lifecycle event.
- `runtime_subagents` contains a placeholder runtime ID.
- A subagent marked `required_skill_check` has no skill invocation record.
- `inline_expert_memos` lacks a runtime-blocked category, reason, or observable escalation.
- A Trace v2 `tool_call` has no matching observation.
- `auto_state.json` and `results.tsv` disagree about latest iteration.

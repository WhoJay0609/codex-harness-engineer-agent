# Feedback Loop

Use this reference to run iterative harness work.

## Run States

Use explicit terminal states:

- `goal_met`
- `budget_exhausted`
- `policy_blocked`
- `environment_blocked`
- `user_decision_needed`
- `failed_with_evidence`

Do not use vague states such as `done` or `probably_fixed`.

## Iteration Loop

1. Start from the current repo map and previous run artifacts.
2. State the hypothesis for this run.
3. Execute the smallest useful change or experiment.
4. Collect tool output, logs, metrics, screenshots, tests, and review feedback.
5. Verify against success criteria.
6. If verification fails, classify the gap:
   - missing_context
   - missing_tool
   - missing_constraint
   - missing_metric
   - missing_runtime_signal
   - unclear_goal
   - invalid_baseline
   - flaky_environment
   - skill_allowlist_gap
   - subagent_scope_gap
7. Improve the harness before retrying when the gap is harness-level.
8. Record the next hypothesis or stop reason.

## Failure Record

Append to `failures.jsonl`:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "failure_type": "test_failure",
  "root_cause": "metric threshold used candidate-only fixture",
  "recoverable": true,
  "harness_gap": "invalid_baseline",
  "evidence": ["metrics.json", "tool_calls.jsonl"],
  "next_action": "rebuild paired baseline and candidate fixtures"
}
```

## Harness Gap Record

Append to `harness_gap_log.jsonl` whenever the agent lacked a reusable capability:

```json
{
  "ts": "2026-05-01T10:00:00Z",
  "gap_type": "missing_runtime_signal",
  "description": "Verifier / Evidence Auditor could not inspect service startup latency.",
  "proposed_harness_change": "Expose startup timing metric in metrics.json.",
  "priority": "high",
  "owner_role": "Runner Coordinator"
}
```

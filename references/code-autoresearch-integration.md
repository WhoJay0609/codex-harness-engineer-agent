# Code Auto Research Integration

Use this reference when a codebase improvement task can be expressed as a
measured loop: improve a metric, verify correctness, keep good changes, discard
bad changes, and preserve an audit trail.

## Position In This Skill

`auto_harness` is the built-in Code Auto Research style mode for
`harness-engineer`. It internalizes the useful mechanics from autoresearch
systems while preserving this skill's artifact contract, Trace v2 events,
skill-routing policy, and explicit user approval boundaries.

The core executable helper set is `init_auto_harness.py`,
`record_auto_iteration.py`, and `run_auto_harness.py`. These provide foreground
initialization, iteration logging, and command-driven improve/verify loops. They
do not yet provide codex-autoresearch-style detached background runtime control
or user-level hooks.

`$codex-autoresearch` remains a reserved orchestration skill. Do not call it
unless the user explicitly requests that external skill in the current task.
When the user asks for Code Auto Research as a pattern or capability, implement
it through `auto_harness` unless they name the external skill.

## Related Projects

- `karpathy/autoresearch`: the original compact autoresearch loop for a fixed
  training script, fixed wall-clock budget, scalar validation metric, and
  keep/discard experimentation.
- `leo-lilinxiao/codex-autoresearch`: a Codex skill that generalizes
  autoresearch to codebase metrics such as tests, types, latency, lint, security,
  and release readiness.
- `TheGreenCedar/codex-autoresearch`: a Codex plugin that adds measured
  experiment packets, durable session files, ASI-style structured memory,
  dashboard inspection, and finalization workflows.
- `AutoX-AI-Labs/AutoR`: a human-centered research harness that treats every run
  as an inspectable artifact on disk with approval checkpoints.

## Pattern To Adopt

For code auto research work, prefer this shape:

1. Confirm the repo, dirty tree, target package, benchmark, metric, direction,
   guard command, safe edit scope, and run mode.
2. Measure a baseline before changing code.
3. Make one focused edit packet per iteration.
4. Run the benchmark and parse the metric mechanically.
5. Run guard checks before keeping an apparent improvement.
6. Keep only improvements that pass guards and justify added complexity.
7. Discard regressions, crashes, guard failures, flat results, and metric gains
   that weaken the benchmark or scope.
8. Log each packet before choosing the next one.
9. Resume from durable state, never from memory alone.
10. Stop with evidence when the goal, budget, policy, environment, or ambiguity
    boundary is reached.

For command-driven loops, the iteration command should be a narrow, repeatable
edit command. The verify command must print a scalar metric, or a JSON object on
the final non-empty line when `verify_format` is `metrics_json`.

## Artifact Mapping

Map external Code Auto Research concepts into the harness contract:

```text
Goal and metric        -> manifest.json, context.json
Baseline               -> results.tsv iteration 0, metrics.json
Experiment packet      -> events.jsonl, tool_calls.jsonl, results.tsv row
Keep/discard decision  -> results.tsv status, events.jsonl checkpoint
Structured memory      -> auto_state.json, harness_gap_log.jsonl, replay.md
Failure or crash       -> failures.jsonl, results.tsv status
Resume state           -> auto_state.json plus results.tsv
Final report           -> summary.md and replay.md
```

## Launch Confirmation

Before starting an auto loop, show the user:

- goal and non-goals;
- workspace root and result directory;
- editable scope;
- baseline command;
- primary metric and `higher` or `lower` direction;
- guard command and regression risks;
- iteration budget and stop condition;
- foreground/background run mode;
- rollback strategy.

Foreground is the default. Use background only after explicit user approval.

## Safety Boundaries

- Do not widen the workspace root silently.
- Do not optimize a metric by weakening the benchmark, deleting tests, muting
  errors, or expanding scope without approval.
- Do not keep changes without a passing guard when a guard is available.
- Do not bury failed experiments; failed rows are part of the audit trail.
- Do not treat dashboard status or summaries as proof without underlying logs,
  commands, and metrics.

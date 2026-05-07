# Auto Harness Mode

Use this reference when a harness should run an autonomous improve/verify loop toward a measurable or mechanically verifiable outcome. Auto Harness Mode is the built-in Code Auto Research style loop for `harness-engineer`; read `references/code-autoresearch-integration.md` for project inspiration and mapping rules. Do not call `$codex-autoresearch` unless the user explicitly requests that skill.

## Activation

Use `mode: "auto_harness"` in `manifest.json` when the task needs repeated iterations such as optimization, failing-test repair, error reduction, benchmark improvement, ship-readiness gates, or long-running research harness work.

Default run mode is `foreground`: keep the loop in the current Codex session. Use `background` only after the user explicitly chooses it during launch confirmation.

## Code Auto Research Lens

For codebase work, treat each iteration as a measured experiment packet:

- one safe edit scope;
- one primary metric and direction;
- one verify command;
- one guard command when regression risk exists;
- one keep, discard, crash, or blocked decision in `results.tsv`.

This mirrors the useful parts of Code Auto Research projects while keeping the
run inside the `harness-engineer` artifact and trace contract.

## Launch Wizard

Before a new auto run starts:

1. Scan the repo or workspace read-only: files, scripts, manifests, tests, metrics, prior runs, and dirty worktree state.
2. Ask at least one repo-grounded confirmation round. Lock the goal, scope, primary metric, direction, verify command, guard command, iteration budget, stop condition, rollback strategy, and run mode.
3. Prefer concrete defaults. Do not expose raw config field names to the user.
4. Confirm foreground/background explicitly. Foreground is the recommended default.
5. Do not ask new questions after the user approves launch. If ambiguity appears mid-loop, apply the confirmed defaults, log the decision, and continue until a terminal condition.

## Helper Scripts

Use these helpers for executable foreground loops:

```bash
python scripts/init_auto_harness.py --run-dir runs/<experiment_id>/<run_id> ...
python scripts/record_auto_iteration.py --run-dir runs/<experiment_id>/<run_id> ...
python scripts/run_auto_harness.py --run-dir runs/<experiment_id>/<run_id> --iteration-command '<cmd>'
```

`init_auto_harness.py` creates the run directory, baseline row, `auto_state.json`,
`context.json`, and normal harness trace files. `record_auto_iteration.py`
atomically appends one `results.tsv` row and synchronizes state, metrics,
manifest termination, events, summary, and replay. `run_auto_harness.py` drives a
foreground command loop: iteration command, verify command, optional guard,
keep/discard decision, optional rollback command, and iteration recording.

For detached background loops, initialize with `--run-mode background`, then use:

```bash
python scripts/harness_runtime_ctl.py launch --run-dir runs/<experiment_id>/<run_id> \
  --iteration-command '<cmd>' --iterations 10
python scripts/harness_runtime_ctl.py status --run-dir runs/<experiment_id>/<run_id>
python scripts/harness_runtime_ctl.py stop --run-dir runs/<experiment_id>/<run_id>
```

User-level Codex hooks are managed separately:

```bash
python scripts/harness_hooks_ctl.py status
python scripts/harness_hooks_ctl.py install
python scripts/harness_hooks_ctl.py uninstall
```

Hooks are optional infrastructure. They add future-session context and stop-hook
continuation hints for active runs, but they should not be installed silently.
The background runtime controller rejects foreground run directories; foreground
runs stay in the current Codex window through `run_auto_harness.py`.

## Artifacts

Auto runs live inside the normal harness run directory:

```text
runs/<experiment_id>/<run_id>/
  manifest.json
  auto_state.json
  results.tsv
  context.json
  metrics.json
  events.jsonl
  tool_calls.jsonl
  failures.jsonl
  harness_gap_log.jsonl
  summary.md
  replay.md
```

`manifest.json` must include `mode: "auto_harness"` and the usual `team_policy`. `auto_state.json` is the recovery snapshot. `results.tsv` is the iteration audit trail. `context.json` records run location, primary repo, scope, verify cwd, and run mode. Background runs may add `launch.json`, `runtime.json`, and `runtime.log`.

## Auto State

Use this minimum shape:

```json
{
  "version": 1,
  "mode": "auto_harness",
  "config": {
    "goal": "reduce failing tests",
    "scope": "tests/ src/",
    "metric": "failure_count",
    "direction": "lower",
    "verify": "pytest -q | tail -n 1",
    "guard": "python -m py_compile src/**/*.py",
    "run_mode": "foreground"
  },
  "state": {
    "iteration": 3,
    "baseline_metric": 12,
    "current_metric": 4,
    "best_metric": 4,
    "last_status": "keep",
    "terminal_status": "goal_met"
  }
}
```

`direction` must be `higher` or `lower`. `run_mode` must be `foreground` or `background`. `terminal_status` must be one of `goal_met`, `budget_exhausted`, `policy_blocked`, `environment_blocked`, `user_decision_needed`, or `failed_with_evidence`.

## Results TSV

Write the header exactly once:

```text
iteration	commit	metric	delta	guard	status	description
```

Status values are `baseline`, `keep`, `discard`, `crash`, `no-op`, `blocked`, `refine`, `pivot`, `search`, and `drift`. Iteration `0` must be the baseline row. Main rows use integer iteration IDs; parallel worker detail rows may use suffixes such as `5a`.

## Loop Protocol

1. Read all in-scope files and relevant config before the first write.
2. Measure the baseline before initializing auto artifacts.
3. Make one focused change or experiment per iteration.
4. Run `verify`; parse the final result mechanically as the metric.
5. Run `guard` after an apparent improvement to check regressions.
6. Keep only when the metric improves in the requested direction, guard passes, and complexity is justified.
7. Discard regressions, flat results, guard failures, crashes, and gains below 1 percent that add disproportionate complexity.
8. Log every completed iteration before choosing the next idea.
9. Resume from `auto_state.json` plus `results.tsv`; never guess from stale comments or repo-root artifacts.

## Stuck Recovery

- After 3 consecutive non-keep outcomes, log `refine` and adjust within the current strategy.
- After 5 consecutive non-keep outcomes, log `pivot` and switch to a fundamentally different approach.
- After repeated pivots without improvement, stop with `failed_with_evidence` or `user_decision_needed` unless the user pre-approved broader scope, web search, or background continuation.

## Internal Experts And Parallel Experiments

Use the `harness-experts.v3` internal team for auto work. Typical roles are `Professor Orchestrator`, `Context Curator`, `Runner Coordinator`, `Verifier / Evidence Auditor`, `Failure Analyst`, and `Mechanical Gatekeeper`.

Parallel experiments are optional and must be approved during launch. Each worker gets an isolated worktree, one hypothesis, the same verify/guard contract, and a bounded device/resource assignment. The orchestrator selects the best mechanically verified result and records worker rows plus one authoritative main row in `results.tsv`.

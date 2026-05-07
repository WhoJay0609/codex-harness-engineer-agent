# Codex Harness Engineer Agent

Installable Codex skill package for building and operating agent-first
harnesses: reproducible runs, typed traces, expert routing, mechanical gates,
failure analysis, replayable artifacts, and foreground-first autonomous loops.

The repository root is the skill package root. Do not nest it under an extra
`skills/harness-engineer/` directory.

## Install

Install or refresh the skill with:

```bash
mkdir -p /home/hujie/.codex/skills/harness-engineer
rsync -a --delete \
  --exclude '.git/' \
  --exclude 'README.md' \
  --exclude '.gitignore' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  ./ /home/hujie/.codex/skills/harness-engineer/
```

Use it in Codex by invoking `$harness-engineer` or by referencing the installed
skill path:

```text
/home/hujie/.codex/skills/harness-engineer/SKILL.md
```

## What It Does

- Builds repo-native harness contracts for agent work.
- Creates and validates traceable run artifacts.
- Routes work through generated internal experts from installed skills.
- Prefers real runtime subagents for non-trivial work when the current runtime
  and platform policy permit delegation, and records explicit inline fallback
  reasons when they do not.
- Keeps `$codex-autoresearch`, `$multi-agent`, and `$expert-debate` reserved
  unless the user explicitly requests them.
- Supports Trace v2 typed events for tool calls, observations, failures,
  checkpoints, metrics, and termination.
- Includes a built-in Code Auto Research style `auto_harness` mode for measured
  codebase improvement loops with initialization, iteration logging, and a
  foreground command runner.
- Provides self-evals so changes to the skill can be regression-tested.

## Layout

```text
SKILL.md
agents/openai.yaml
references/
  framework.md
  code-autoresearch-integration.md
  artifact-contract.md
  maintenance-guide.md
  schemas/harness-event.schema.json
scripts/
evals/
```

## Common Commands

Validate the skill package:

```bash
python scripts/check_harness_consistency.py .
python scripts/run_harness_evals.py
python -m py_compile scripts/*.py
```

Refresh installed skills and generated expert library:

```bash
python scripts/update_skill_inventory.py
python scripts/update_expert_library.py
```

Validate and inspect a harness run:

```bash
python scripts/validate_harness_trace.py runs/<experiment_id>/<run_id>
python scripts/replay_harness_run.py runs/<experiment_id>/<run_id>
python scripts/query_harness_trace.py runs/<experiment_id>/<run_id> --event-type tool_call
python scripts/export_trace_table.py runs/<experiment_id>/<run_id> --format csv
```

Run a foreground Code Auto Research style loop:

```bash
python scripts/init_auto_harness.py \
  --run-dir runs/demo/001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python scripts/score.py" \
  --guard "pytest -q" \
  --baseline-metric 0

python scripts/run_auto_harness.py \
  --run-dir runs/demo/001 \
  --iteration-command "python scripts/propose_one_change.py" \
  --iterations 5
```

Use `scripts/record_auto_iteration.py` directly when Codex or a custom runner
performs the edit/verify step and only needs to append a keep/discard/crash row.

For non-trivial harness tasks, create runtime subagents first and pass their
handles into initialization so the artifacts show real parallel execution:

```bash
python scripts/init_auto_harness.py \
  --run-dir runs/demo/001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python scripts/score.py" \
  --baseline-metric 0 \
  --runtime-subagent "Verifier / Evidence Auditor=<runtime_agent_id>"
```

Foreground is the default. No detached process is created unless the run is
initialized with `--run-mode background` and launched through
`scripts/harness_runtime_ctl.py`.

Run a detached background loop:

```bash
python scripts/init_auto_harness.py \
  --run-dir runs/demo/bg-001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python scripts/score.py" \
  --guard "pytest -q" \
  --run-mode background \
  --baseline-metric 0

python scripts/harness_runtime_ctl.py launch \
  --run-dir runs/demo/bg-001 \
  --iteration-command "python scripts/propose_one_change.py" \
  --iterations 10

python scripts/harness_runtime_ctl.py status --run-dir runs/demo/bg-001
python scripts/harness_runtime_ctl.py stop --run-dir runs/demo/bg-001
```

Manage optional user-level Codex hooks:

```bash
python scripts/harness_hooks_ctl.py status
python scripts/harness_hooks_ctl.py install
python scripts/harness_hooks_ctl.py uninstall
```

Hooks write future-session context and stop-hook continuation hints for active
`auto_harness` runs. They are managed explicitly and are not installed during
package validation.

## Artifact Contract

A minimum viable run records:

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

`references/artifact-contract.md` is the authoritative file and field contract.
New runs should prefer Trace v2 typed events in `events.jsonl`, following
`references/schemas/harness-event.schema.json`. Every material tool call should
have a matching observation, failures should include `error_kind`, and the run
should end with an explicit terminal status. Non-trivial runs must declare
`team_policy.subagent_execution_mode`.

Full auto-harness runs also include `auto_state.json`, `results.tsv`, and
`context.json`. See `SKILL.md` and `references/` for the full contract.

For local skill maintenance, sync, validation, and publish steps, see
`references/maintenance-guide.md`.

## Related GitHub Projects

- [leo-lilinxiao/codex-autoresearch](https://github.com/leo-lilinxiao/codex-autoresearch):
  Codex Autoresearch Skill for goal-driven modify, verify, keep or discard
  loops over mechanically verifiable codebase metrics. This repository borrows
  the measured loop pattern while keeping `$codex-autoresearch` as an
  explicit-request-only external orchestration skill.
- [TheGreenCedar/codex-autoresearch](https://github.com/TheGreenCedar/codex-autoresearch):
  Codex plugin for benchmark-contract-driven experiment packets, durable
  session files, structured packet memory, and dashboard-backed review.

## Implementation References

This skill remains Codex-native and file-based, but its harness mechanics were
informed by these open-source projects and docs:

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch): fixed-budget
  autonomous research loop with scalar metric comparison and keep/discard
  experimentation.
- [OpenHands Events](https://docs.openhands.dev/sdk/arch/events): append-only,
  typed event logs with source-aware event records.
- [OpenHands Runtime](https://github.com/OpenHands/OpenHands/blob/main/openhands/runtime/README.md):
  controlled runtime interfaces for shell, browser, filesystem, environment,
  and plugin actions.
- [SWE-agent trajectories](https://swe-agent.com/latest/usage/trajectories/):
  thought/action/observation trajectory files for coding-agent replay.
- [SWE-bench harness](https://www.swebench.com/SWE-bench/api/harness/):
  reproducible evaluation harnesses, logs, patches, and environment setup.
- [LangGraph](https://github.com/langchain-ai/langgraph): durable execution
  and human-in-the-loop concepts for long-running agent workflows.
- [Inspect AI analysis](https://inspect.aisi.org.uk/reference/inspect_ai.analysis.html):
  dataframe-style analysis over eval logs, samples, messages, and events.
- [OpenAI Evals](https://github.com/openai/evals): reusable eval registry and
  local eval development pattern.
- [AgentOps](https://github.com/agentops-ai/agentops): session replay,
  nested spans, cost/error tracking, and agent observability patterns.
- [agentevals](https://github.com/agentevals-dev/agentevals): local-first
  evaluation over pre-recorded traces without re-running expensive agents.

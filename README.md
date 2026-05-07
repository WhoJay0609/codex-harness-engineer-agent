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
- Provides self-evals so changes to the skill can be regression-tested.

## Layout

```text
SKILL.md
agents/openai.yaml
references/
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

New runs should prefer Trace v2 typed events in `events.jsonl`, following
`references/schemas/harness-event.schema.json`. Every material tool call should
have a matching observation, failures should include `error_kind`, and the run
should end with an explicit terminal status. Non-trivial runs must declare
`team_policy.subagent_execution_mode`: use `runtime_subagents` when real
subagent/thread handles were created, `inline_expert_memos` only when delegation
is unavailable or blocked and the reason is recorded, or
`single_agent_exception` for trivial work.

Full auto-harness runs also include `auto_state.json`, `results.tsv`, and
`context.json`. See `SKILL.md` and `references/` for the full contract.

## Implementation References

This skill remains Codex-native and file-based, but its harness mechanics were
informed by these open-source projects and docs:

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

# Codex Harness Engineer Agent

Installable Codex skill package for building and operating agent-first harnesses.
The skill focuses on reproducible agent work, evidence-backed feedback loops,
mechanical gates, trace artifacts, startup cleanup, expert routing policy, and
foreground-first autonomous harness loops.

## Layout

```text
SKILL.md
agents/openai.yaml
references/
scripts/
```

The repository root is the skill package root. Do not nest the skill under an
extra `skills/harness-engineer/` directory when installing from this repo.

## Install

Copy or sync this repository into:

```text
/home/hujie/.codex/skills/harness-engineer
```

## Validate

Run these checks from the repository root:

```bash
python scripts/check_harness_consistency.py .
python -m py_compile scripts/*.py
```

For a concrete harness run, validate the trace before trusting the result:

```bash
python scripts/validate_harness_trace.py runs/<experiment_id>/<run_id>
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

Full auto-harness runs also include `auto_state.json`, `results.tsv`, and
`context.json`. See `SKILL.md` and `references/` for the full contract.

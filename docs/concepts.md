# Concepts

Harness Engineer is a small operating model for Codex work. It makes agent
execution observable enough that future agents and humans can replay what
happened, compare results, and decide whether a change should be kept.

## Seven Layers

1. **Intent**: goal, scope, budget, metric, guard, stop condition.
2. **Context**: repo map, source-of-truth files, constraints, dirty tree state.
3. **Team**: runtime subagents, role contracts, replacement and stop rules.
4. **Tools**: shell/browser/runtime capabilities, skill allowlists, guards.
5. **Artifacts**: manifests, traces, metrics, failures, summaries, replay.
6. **Loop**: baseline, change, verify, keep/discard, recover, terminate.
7. **Maintenance**: refresh inventory, expert library, validators, evals.

## Runtime Subagents

For non-trivial work, the main Codex orchestrator directly creates a small team
with `spawn_agent`.

Typical execution team:

- `Context Curator`
- `Runner Coordinator`
- `Verifier / Evidence Auditor`

The main thread keeps the critical path. Subagents handle bounded parallel work
and return concise findings with evidence. Each created runtime subagent must
later receive a terminal lifecycle event: `completed`, `stopped`, `blocked`,
`failed`, or `replaced`.

`inline_expert_memos` are allowed only when runtime creation is unavailable,
blocked by platform or policy, over thread limits after cleanup, or failed after
an attempted creation. Missing user authorization is not a fallback reason when
the user invoked `$harness-engineer`.

## Trace V2

Trace v2 is an append-only JSONL event stream. It records:

- plans and decisions;
- tool calls and observations;
- subagent creation and terminal lifecycle;
- metrics and checkpoints;
- failures and termination.

The validator rejects missing observations, unknown event types, missing
terminal status, placeholder runtime IDs, missing skill checks, and invalid
inline fallback.

## Auto Harness

`auto_harness` is the built-in foreground-first improve/verify loop:

1. Measure baseline.
2. Try one focused change.
3. Run verify command.
4. Run guard command if needed.
5. Keep, discard, crash, block, refine, or pivot.
6. Record the decision in `results.tsv` and synchronized state files.

Detached background mode exists, but must be explicitly selected with
`--run-mode background`.

## Reserved Orchestration Skills

`$codex-autoresearch`, `$multi-agent`, and `$expert-debate` remain
explicit-request-only. Harness Engineer borrows ideas from these patterns but
does not proactively call those external orchestration skills.

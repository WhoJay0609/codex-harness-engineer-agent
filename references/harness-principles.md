# Harness Principles

Use this reference when deciding what kind of harness a project needs.

## Definition

Harness engineering is the work of designing the surrounding system that lets agents act reliably: context delivery, repo records, tool access, validation, feedback loops, subagent roles, mechanical gates, and recovery.

The engineer's primary output is a constraint and feedback system, not a pile of ad hoc prompts.

## Operating Principles

- Repo as record system: if an agent cannot discover it in the workspace, it should not be treated as operational truth.
- Map, not manual: keep entry files short; link to deeper docs and executable checks.
- Mechanical enforcement: convert repeated review comments into tests, validators, lint rules, schemas, or CI checks.
- Agent readability: prefer stable, inspectable, boring technology and explicit artifacts over hidden state.
- Worktree-local operation: when possible, make apps, logs, metrics, traces, screenshots, and test fixtures isolated per working tree or run.
- Feedback flywheel: every failure should improve context, tools, gates, docs, or examples.
- Entropy management: agents repeat existing patterns, including bad ones; schedule small cleanup passes instead of waiting for large rewrites.

## Design Questions

Before building a harness, answer:

```text
What exact goal should the agent reach?
How will success be measured?
What artifacts prove success?
What context must be repo-local?
What tool or runtime signals must be visible to agents?
What invalid states must fail loudly?
What repeated human feedback can become a mechanical gate?
What subagent roles need isolated context?
When should work escalate to external expert review?
```

## Source Inspiration

This skill follows the practical framing from OpenAI's Harness Engineering article and the `deusyu/harness-engineering` learning archive: human direction, agent execution, repo-local knowledge, progressive disclosure, mechanical checks, and continuous garbage collection.

Trace, replay, and evaluation mechanics are also informed by open-source agent harness patterns: OpenHands typed append-only events and controlled runtime boundaries, SWE-agent trajectory files, SWE-bench reproducible harness logs, LangGraph durable execution and human-in-the-loop concepts, Inspect AI log analysis, OpenAI Evals registry patterns, local-first trace evaluation ideas from AgentOps/agentevals, and Code Auto Research loops from `karpathy/autoresearch` and Codex-oriented `codex-autoresearch` projects.

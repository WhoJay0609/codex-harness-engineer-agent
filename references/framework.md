# Harness Framework

Use this reference when changing the structure of the `harness-engineer` skill
or when deciding where a new rule belongs.

## Purpose

`harness-engineer` is a Codex skill for building repo-native systems that let
agents work reliably. It should stay understandable as the skill grows:

- `SKILL.md` is the entry map.
- `references/` owns durable policies and design details.
- `scripts/` owns executable checks and generated-file maintenance.
- `evals/` owns regression cases for artifact contracts.
- `README.md` in the publish repo owns installation, usage, and upstream
  project references.

Do not place long policy text in `SKILL.md` unless it is required for safe
first-step execution.

## Layer Model

Every harness decision should fit one layer:

1. Intent layer: goal, scope, budget, stop condition, success metric, and human
   confirmation.
2. Context layer: repo map, local instructions, prior run artifacts, dirty tree,
   and constraints.
3. Team layer: core council, domain specialists, runtime subagent handles,
   inline fallback, and single-agent exceptions.
4. Tool layer: skill allowlists, reserved orchestration policy, shell commands,
   browser/runtime access, and guard commands.
5. Artifact layer: manifest, event trace, tool observations, failures, metrics,
   replay, and summary.
6. Feedback layer: baseline, hypothesis, focused change, verify, guard,
   keep/discard, repair, and terminal state.
7. Maintenance layer: inventory refresh, expert library generation, schema
   validation, eval fixtures, README, and publish sync.

If a new rule cannot be assigned to one layer, the rule is probably too vague.

## Reference Ownership

Keep related concepts together:

- First principles: `harness-principles.md`
- Mode architecture: `framework.md`, `auto-harness-mode.md`,
  `code-autoresearch-integration.md`
- Team behavior: `team-formation-policy.md`, `subagent-runtime.md`
- Skill behavior: `skill-routing-policy.md`, `skill-activation-policy.md`,
  `decision-support-policy.md`, `escalation-policy.md`
- Evidence behavior: `feedback-loop.md`, `mechanical-gates.md`,
  `schemas/harness-event.schema.json`
- Maintenance behavior: `entropy-garbage-collection.md`,
  `skill-inventory.json`, `expert-capability-library.json`,
  `expert-capability-library.md`

## Change Protocol

When changing the skill framework:

1. Update `SKILL.md` only as a short entry map.
2. Add or update the specific reference that owns the detailed rule.
3. Update validators when the rule is enforceable.
4. Update eval fixtures when validator behavior changes.
5. Update README when users need install, usage, or related-project context.
6. Run the consistency check, self-evals, and Python syntax check before
   publishing.

## Maintenance Smells

- `SKILL.md` repeats detailed policy already present in `references/`.
- A reference mixes unrelated layers such as team formation and trace schema.
- A new artifact field is documented but not validated.
- Generated expert library output is manually edited instead of regenerated.
- Reserved orchestration skill policy differs across references, validators, and
  evals.
- README describes behavior not present in the installed skill.

## Minimal Publish Gate

Run from the skill root or publish repo:

```bash
python scripts/check_harness_consistency.py .
python scripts/run_harness_evals.py
python -m py_compile scripts/*.py
```

Remove generated `__pycache__/` directories before committing.

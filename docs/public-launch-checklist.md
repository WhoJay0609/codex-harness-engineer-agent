# Public Launch Checklist

Use this before presenting the repository publicly.

## Repository Surface

- [ ] README has a short value proposition above the fold.
- [ ] Quickstart works in a fresh clone.
- [ ] CI badge points to a real workflow.
- [ ] Examples are copy-pasteable and do not rely on ignored `runs/` outputs.
- [ ] Related projects are credited.
- [ ] No private paths are required for the public CI path.
- [ ] Generated caches and run outputs are ignored.

## Trust Signals

- [ ] `python3 scripts/check_harness_consistency.py .` passes locally.
- [ ] `python3 scripts/check_harness_consistency.py . --skip-environment-freshness` passes in CI.
- [ ] `python3 scripts/run_harness_evals.py` passes.
- [ ] `python3 -m py_compile scripts/*.py` passes.
- [ ] At least one valid direct runtime team fixture is committed.
- [ ] At least one invalid placeholder runtime ID fixture is committed.
- [ ] At least one invalid inline fallback fixture is committed.

## GitHub Settings

Suggested description:

```text
Codex skill for reproducible agent harnesses: typed traces, subagent lifecycle records, eval fixtures, replayable runs, and auto-harness loops.
```

Suggested topics:

```text
codex, agents, ai-agents, agent-harness, evals, trace, automation, developer-tools
```

## Release Notes

Before tagging a release, include:

- headline capability;
- install command;
- validation commands;
- notable artifact-contract changes;
- migration notes for existing local installs.

## License

No license file is currently present. Choose and add a license before broad
public promotion if external reuse is intended.

# Harness Engineer Evals

Regression packs for the `harness-engineer` skill itself.

Run from the skill root:

```bash
python scripts/run_harness_evals.py
```

Each case is a minimal run directory plus `expected.json`. The runner executes
`scripts/validate_harness_trace.py` and checks whether the case should pass or
fail. These cases guard Trace v2 structure, reserved orchestration policy, and
basic artifact contracts. Direct runtime team cases also verify that
`runtime_subagents` use concrete `spawn_agent` return IDs, reject placeholder
handles, justify inline fallback with an observable runtime escalation, and
record replacement lifecycles.

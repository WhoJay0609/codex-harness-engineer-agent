# Example: Auto Harness Foreground

Use a committed auto-harness fixture to inspect the baseline-plus-iteration
record format.

```bash
python3 scripts/validate_harness_trace.py evals/cases/valid_auto_harness
```

Inspect iteration decisions:

```bash
sed -n '1,8p' evals/cases/valid_auto_harness/results.tsv
```

Inspect synchronized state:

```bash
python3 -m json.tool evals/cases/valid_auto_harness/auto_state.json
python3 -m json.tool evals/cases/valid_auto_harness/metrics.json
```

The foreground loop records:

- iteration `0` as baseline;
- later rows as `keep`, `discard`, `crash`, `blocked`, `refine`, `pivot`, or
  related auto outcomes;
- metric and guard evidence for every decision.

For a live run, use `run_auto_harness.py` only after initializing with concrete
runtime subagent IDs.

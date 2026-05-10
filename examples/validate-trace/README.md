# Example: Validate A Trace

Use the committed `valid_trace_v2` fixture to exercise the trace tooling.

```bash
python3 scripts/validate_harness_trace.py evals/cases/valid_trace_v2
```

Expected output:

```text
PASS: harness trace is valid
```

Replay the same fixture:

```bash
python3 scripts/replay_harness_run.py evals/cases/valid_trace_v2
```

Query tool-call events:

```bash
python3 scripts/query_harness_trace.py evals/cases/valid_trace_v2 --event-type tool_call
```

Export a CSV table:

```bash
python3 scripts/export_trace_table.py evals/cases/valid_trace_v2 --format csv
```

The exported table is written to stdout by default.

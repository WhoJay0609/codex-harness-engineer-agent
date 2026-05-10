# Harness Engineer Evals

Regression packs for the `harness-engineer` skill itself. Each case is a
minimal run directory plus `expected.json`.

Run all cases:

```bash
python3 scripts/run_harness_evals.py
```

Run one case directly:

```bash
python3 scripts/validate_harness_trace.py evals/cases/valid_direct_runtime_team
```

## Case Matrix

| Case | Expected | Contract Covered |
| --- | --- | --- |
| `valid_trace_v2` | pass | Trace v2 event shape, tool observation linkage, termination. |
| `valid_auto_harness` | pass | Auto state, results TSV, runtime team artifacts. |
| `valid_background_auto_harness` | pass | Background run metadata and runtime files. |
| `valid_runtime_subagent_auto_harness` | pass | Auto harness with concrete runtime subagent handles. |
| `valid_direct_runtime_team` | pass | Direct `spawn_agent` lifecycle with terminal records. |
| `valid_subagent_replacement` | pass | Replacement lifecycle and internal expert decision record. |
| `invalid_missing_observation` | fail | Tool calls require matching observations. |
| `invalid_missing_subagent_execution_mode` | fail | Non-trivial team policy must declare execution mode. |
| `invalid_reserved_skill` | fail | Reserved orchestration skills need explicit user request. |
| `invalid_generic_inline_fallback` | fail | Missing-handle fallback is not a valid inline reason. |
| `invalid_placeholder_runtime_id` | fail | Placeholder runtime IDs are rejected. |
| `invalid_unjustified_inline_fallback` | fail | Inline fallback needs observable runtime-blocked escalation. |

Invalid cases are intentionally committed. They make sure validators fail for
the exact failure modes that previously let weak harness traces look valid.

## Adding A Case

1. Create `evals/cases/<name>/`.
2. Add the minimal artifact files required by `validate_harness_trace.py`.
3. Add `expected.json`:

   ```json
   {"expect": "pass"}
   ```

   or:

   ```json
   {"expect": "fail", "contains": "expected error substring"}
   ```

4. Run:

   ```bash
   python3 scripts/run_harness_evals.py
   ```

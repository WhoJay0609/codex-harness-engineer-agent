# Example: Direct Runtime Team

This example uses committed fixtures to show the runtime subagent lifecycle
contract. It does not require a live Codex runtime.

Validate a good direct-runtime fixture:

```bash
python3 scripts/validate_harness_trace.py evals/cases/valid_direct_runtime_team
```

Inspect the lifecycle records:

```bash
sed -n '1,12p' evals/cases/valid_direct_runtime_team/subagents.jsonl
```

Validate a bad placeholder fixture:

```bash
python3 scripts/validate_harness_trace.py evals/cases/invalid_placeholder_runtime_id
```

Expected failure includes:

```text
not a placeholder
```

## Live Runtime Shape

In a live Codex session:

1. Run `scripts/select_subagent_team.py` to produce task cards.
2. The main Codex orchestrator calls `spawn_agent` once per card.
3. The returned runtime IDs are passed into `init_auto_harness.py`.
4. The main Codex calls `close_agent` when each subagent is done.
5. `record_subagent_lifecycle.py` records terminal events.

Invented or copied placeholder handles are invalid.

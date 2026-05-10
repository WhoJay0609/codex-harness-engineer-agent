# Contributing

Thanks for improving Codex Harness Engineer. This repository is an installable
Codex skill, so changes should preserve both the public GitHub surface and the
local skill package contract.

## Local Validation

Run these before opening a pull request:

```bash
python3 scripts/check_harness_consistency.py .
python3 scripts/run_harness_evals.py
python3 -m py_compile scripts/*.py
```

For portable CI-like validation:

```bash
python3 scripts/check_harness_consistency.py . --skip-environment-freshness
```

## Adding Or Changing Scripts

- Keep scripts dependency-light and Python 3.8+ compatible.
- Use plain JSON/JSONL/TSV files for artifacts.
- Update `scripts/check_harness_consistency.py` when a script becomes part of
  the required package surface.
- Add or update eval fixtures when validator behavior changes.
- Avoid hard-coded private paths in public examples or CI.

## Adding An Eval Fixture

1. Add a directory under `evals/cases/<case-name>/`.
2. Include `expected.json` with `{"expect": "pass"}` or
   `{"expect": "fail", "contains": "..."}`.
3. Keep fixtures minimal and readable.
4. Run `python3 scripts/run_harness_evals.py`.
5. Update `evals/README.md` if the case covers a new contract.

## Documentation Style

- Put public onboarding in `README.md`, `docs/`, and `examples/`.
- Keep installable skill behavior in `SKILL.md` and `references/`.
- Prefer copy-pasteable commands.
- Mention when a command requires a live Codex runtime.
- Keep invalid examples clearly marked as intentional failure fixtures.

## Pull Requests

Every PR should say:

- what behavior changed;
- which artifact contract changed, if any;
- which evals were added or updated;
- exact validation commands run;
- whether installed skill sync is needed.

## License

No license file is currently present. Do not add one casually in a drive-by PR;
it should be an explicit maintainer decision.

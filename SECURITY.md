# Security Policy

Harness Engineer is a local Codex skill package. Most security issues are likely
to involve unsafe command examples, trace files containing secrets, or hooks that
run in unintended contexts.

## Reporting

Please open a GitHub issue for non-sensitive security concerns. For sensitive
reports, avoid posting secrets, private run artifacts, tokens, or proprietary
trace logs publicly.

## Guidance

- Do not commit real API keys, tokens, or private run artifacts.
- Treat `runs/` and `state_snapshots/` as local generated state.
- Review hook configuration before installing user-level hooks.
- Prefer redacted validator output when reporting trace failures.

## Supported Versions

The current `main` branch is the supported development target.

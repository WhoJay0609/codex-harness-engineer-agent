# Changelog

All notable changes to this repository should be recorded here.

## Unreleased

- Reworked the public README into a GitHub landing page.
- Added public docs for quickstart, concepts, artifact tour, Chinese overview,
  and launch checklist.
- Added example recipes for trace validation, direct runtime teams, and
  foreground auto-harness fixtures.
- Added contributor, security, conduct, issue-template, PR-template, and CI
  metadata.
- Added portable CI mode for `check_harness_consistency.py` with
  `--skip-environment-freshness`.

## 2026-05-10

- Enabled direct runtime subagent teams with `spawn_agent` lifecycle records.
- Added `select_subagent_team.py` and `record_subagent_lifecycle.py`.
- Tightened validation for placeholder runtime IDs and unjustified inline
  fallback.
- Added direct runtime team and replacement eval fixtures.

# Maintenance Guide

Use this reference when modifying, packaging, or publishing the
`harness-engineer` skill.

## Source Of Truth

The installed local skill is the source of truth:

```text
/home/hujie/.codex/skills/harness-engineer
```

The publish repo mirrors the installable skill package at its repository root:

```text
/home/hujie/paper/tools/codex-harness-engineer-agent
```

Do not edit generated caches or run outputs into either tree.

## Change Types

- Entry-map change: edit `SKILL.md` and keep it short.
- Policy change: edit the owning file under `references/`.
- Artifact-contract change: edit `references/artifact-contract.md`, update
  validators when enforceable, and add eval fixtures when behavior changes.
- Skill-inventory change: run `scripts/update_skill_inventory.py` and then
  `scripts/update_expert_library.py`.
- Script or validator change: update or add eval cases under `evals/cases/`.
- User-facing packaging change: update publish-repo `README.md`.

## Local Validation

Run from the skill root after local edits:

```bash
python scripts/check_harness_consistency.py .
python scripts/run_harness_evals.py
python -m py_compile scripts/*.py
rm -rf scripts/__pycache__
```

The consistency check verifies required references, scripts, generated inventory
freshness, expert library freshness, and eval case presence.

## Sync To Publish Repo

From any directory:

```bash
rsync -a --delete \
  --exclude '/.git/' \
  --exclude '/README.md' \
  --exclude '/.gitignore' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  /home/hujie/.codex/skills/harness-engineer/ \
  /home/hujie/paper/tools/codex-harness-engineer-agent/
```

The root `README.md` and `.gitignore` belong to the publish repo and should not
be overwritten by this sync.

## Publish Gate

Run from the publish repo:

```bash
python scripts/check_harness_consistency.py .
python scripts/run_harness_evals.py
python -m py_compile scripts/*.py
rm -rf scripts/__pycache__
git diff --check
find . -name '__pycache__' -o -name '*.pyc'
git status --short
```

Commit only after the checks pass and generated caches are absent.

## Push

```bash
git add .
git commit -m "<type>: <summary>"
git push origin main
git ls-remote --heads origin main
```

Use concise commit messages such as:

- `docs: clarify harness framework`
- `fix: enforce harness trace contract`
- `feat: add harness eval coverage`

## Common Pitfalls

- Updating `SKILL.md` without linking the owning reference.
- Adding a required reference without updating
  `scripts/check_harness_consistency.py`.
- Editing generated expert library files by hand instead of regenerating them.
- Publishing stale `skill-inventory.json` after installed skills changed.
- Forgetting to preserve the publish repo's root `README.md`.
- Leaving `__pycache__/` or `*.pyc` files after Python validation.

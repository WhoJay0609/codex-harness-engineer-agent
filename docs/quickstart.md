# Quickstart

This guide gets the skill installed and validates the repo without requiring a
live Codex runtime.

## 1. Clone

```bash
git clone https://github.com/WhoJay0609/codex-harness-engineer-agent.git
cd codex-harness-engineer-agent
```

## 2. Validate The Package

```bash
python3 scripts/check_harness_consistency.py .
python3 scripts/run_harness_evals.py
python3 -m py_compile scripts/*.py
```

For portable CI environments that do not have the same local skill roots:

```bash
python3 scripts/check_harness_consistency.py . --skip-environment-freshness
```

## 3. Install As A Codex Skill

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills/harness-engineer"
rsync -a --delete \
  --exclude '.git/' \
  --exclude 'README.md' \
  --exclude '.gitignore' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  ./ "$CODEX_HOME/skills/harness-engineer/"
```

Use it inside Codex:

```text
$harness-engineer
```

## 4. Select A Team

```bash
python3 scripts/select_subagent_team.py \
  --task-class execution \
  --goal "improve a mechanically verified score" \
  --scope src/
```

The output is a role plan and task cards. In a live Codex session, the main
orchestrator uses those task cards with `spawn_agent`.

## 5. Initialize A Run

Use concrete runtime IDs returned by `spawn_agent`; placeholders are rejected.

```bash
python3 scripts/init_auto_harness.py \
  --run-dir runs/demo/001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python3 scripts/score.py" \
  --guard "pytest -q" \
  --baseline-metric 0 \
  --runtime-subagent "Context Curator=<runtime_agent_id>" \
  --runtime-subagent "Verifier / Evidence Auditor=<runtime_agent_id>"
```

## 6. Record Iterations

```bash
python3 scripts/record_auto_iteration.py \
  --run-dir runs/demo/001 \
  --status keep \
  --metric 1.2 \
  --guard pass \
  --description "candidate improved the primary metric"
```

## 7. Close Runtime Subagents

```bash
python3 scripts/record_subagent_lifecycle.py \
  --run-dir runs/demo/001 \
  --event completed \
  --role "Verifier / Evidence Auditor" \
  --agent-id verifier-evidence-auditor \
  --stop-reason "artifact verification completed"
```

## 8. Validate The Run

```bash
python3 scripts/validate_harness_trace.py runs/demo/001
python3 scripts/replay_harness_run.py runs/demo/001
```

## 中文快速说明

1. 先运行 `check_harness_consistency.py`、`run_harness_evals.py` 和
   `py_compile` 确认包健康。
2. 用 `rsync` 把仓库根目录同步到
   `$CODEX_HOME/skills/harness-engineer`。
3. 在 Codex 中调用 `$harness-engineer`。
4. 非平凡任务先用 `select_subagent_team.py` 选角色，再由主 Codex 调用
   `spawn_agent` 创建真实 runtime 子智能体。
5. 每轮运行都写 artifact，并在结束前运行 `validate_harness_trace.py`。

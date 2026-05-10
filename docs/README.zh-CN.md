# Codex Harness Engineer 中文说明

Codex Harness Engineer 是一个可安装的 Codex skill，用来把复杂工程任务组织成
可复现、可验证、可回放的 agent harness。

它解决的问题不是“创建更多智能体”，而是让 Codex 的工作过程有清晰证据：

- 目标、范围、指标和终止条件明确；
- 子智能体有角色、输入、输出和生命周期；
- 每次运行都有 JSON/JSONL artifacts；
- 每轮改动都记录 baseline、metric、guard、keep/discard；
- 失败、替换、阻塞和 fallback 都能被 validator 检查。

## 快速安装

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

在 Codex 中使用：

```text
$harness-engineer
```

## 非平凡任务如何运行

1. 主 Codex 先拆解目标、指标、guard 和预算。
2. 用 `select_subagent_team.py` 选择最小 runtime team。
3. 主 Codex 调用 `spawn_agent` 创建真实子智能体。
4. `subagents.jsonl` 记录 `spawn_agent` 返回的 runtime ID。
5. 主线程保留关键路径：集成、最终验证和 artifact 完整性。
6. 子智能体只处理并行分支：上下文、局部实现、验证、失败分析、风险审查。
7. 子智能体完成后调用 `close_agent`，并用
   `record_subagent_lifecycle.py` 写 terminal event。

## 本地验证

```bash
python3 scripts/check_harness_consistency.py .
python3 scripts/run_harness_evals.py
python3 -m py_compile scripts/*.py
```

## 进一步阅读

- [Quickstart](quickstart.md)
- [Concepts](concepts.md)
- [Artifact Tour](artifact-tour.md)
- [Team Formation Policy](../references/team-formation-policy.md)
- [Subagent Runtime](../references/subagent-runtime.md)

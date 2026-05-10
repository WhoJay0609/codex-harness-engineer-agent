# Codex Harness Engineer Agent / Codex Harness 工程师技能

Installable Codex skill package for building and operating agent-first
harnesses: reproducible runs, typed traces, expert routing, mechanical gates,
failure analysis, replayable artifacts, and foreground-first autonomous loops.

这是一个可安装的 Codex 技能包，用于构建和运行面向智能体工作的
harness：可复现运行、类型化 trace、专家路由、机械门禁、失败分析、
可回放 artifacts，以及默认在前台窗口执行的自动迭代循环。

The repository root is the skill package root. Do not nest it under an extra
`skills/harness-engineer/` directory.

仓库根目录就是技能包根目录。安装时不要再额外嵌套
`skills/harness-engineer/` 目录。

## Install / 安装

Install or refresh the skill with:

使用下面的命令安装或刷新技能：

```bash
mkdir -p /home/hujie/.codex/skills/harness-engineer
rsync -a --delete \
  --exclude '.git/' \
  --exclude 'README.md' \
  --exclude '.gitignore' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  ./ /home/hujie/.codex/skills/harness-engineer/
```

Use it in Codex by invoking `$harness-engineer` or by referencing the installed
skill path:

在 Codex 中可以通过 `$harness-engineer` 调用，或直接引用已安装的技能路径：

```text
/home/hujie/.codex/skills/harness-engineer/SKILL.md
```

## What It Does / 功能说明

- Builds repo-native harness contracts for agent work.
  为代码仓库内的智能体工作建立可复现的 harness 契约。
- Creates and validates traceable run artifacts.
  创建并验证可追踪的运行 artifacts。
- Routes work through generated internal experts from installed skills.
  基于已安装 skills 生成内部专家库，并按任务路由工作。
- For non-trivial work, the main Codex orchestrator directly calls
  `spawn_agent` to create the runtime team and records the returned runtime IDs.
  Inline fallback is only valid when `spawn_agent` is unavailable, blocked, over
  thread limits after cleanup, or fails.
  对非平凡任务，主 Codex orchestrator 直接调用 `spawn_agent` 创建 runtime
  团队，并记录返回的 runtime ID。只有 `spawn_agent` 不可用、被阻塞、清理后仍达
  线程上限或创建失败时，才允许 inline fallback。
- Keeps `$codex-autoresearch`, `$multi-agent`, and `$expert-debate` reserved
  unless the user explicitly requests them.
  除非用户明确要求，否则保留 `$codex-autoresearch`、`$multi-agent` 和
  `$expert-debate` 为显式请求技能。
- Supports Trace v2 typed events for tool calls, observations, failures,
  checkpoints, metrics, and termination.
  支持 Trace v2 类型化事件，覆盖工具调用、观察结果、失败、检查点、指标和终止。
- Includes a built-in Code Auto Research style `auto_harness` mode for measured
  codebase improvement loops with initialization, iteration logging, and a
  foreground command runner.
  内置 Code Auto Research 风格的 `auto_harness` 模式，用于有指标的代码改进循环：
  初始化、迭代记录、前台命令 runner。
- Provides self-evals so changes to the skill can be regression-tested.
  提供自测 evals，便于对 skill 变更做回归验证。

## Layout / 目录结构

```text
SKILL.md
agents/openai.yaml
references/
  framework.md
  code-autoresearch-integration.md
  artifact-contract.md
  maintenance-guide.md
  schemas/harness-event.schema.json
scripts/
evals/
```

## Common Commands / 常用命令

The examples use `python3` because some Codex environments do not expose a
`python` executable.

下面示例使用 `python3`，因为部分 Codex 环境没有 `python` 命令。

Validate the skill package:

验证技能包：

```bash
python3 scripts/check_harness_consistency.py .
python3 scripts/run_harness_evals.py
python3 -m py_compile scripts/*.py
```

Refresh installed skills and generated expert library:

刷新已安装技能清单和生成的专家库：

```bash
python3 scripts/update_skill_inventory.py
python3 scripts/update_expert_library.py
```

Validate and inspect a harness run:

验证并检查一次 harness 运行：

```bash
python3 scripts/validate_harness_trace.py runs/<experiment_id>/<run_id>
python3 scripts/replay_harness_run.py runs/<experiment_id>/<run_id>
python3 scripts/query_harness_trace.py runs/<experiment_id>/<run_id> --event-type tool_call
python3 scripts/export_trace_table.py runs/<experiment_id>/<run_id> --format csv
```

Select a direct runtime subagent team:

选择直接 runtime 子智能体团队：

```bash
python3 scripts/select_subagent_team.py \
  --task-class execution \
  --goal "improve the measured score" \
  --scope src/
```

Run a foreground Code Auto Research style loop:

运行默认的前台 Code Auto Research 风格循环：

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

python3 scripts/run_auto_harness.py \
  --run-dir runs/demo/001 \
  --iteration-command "python3 scripts/propose_one_change.py" \
  --iterations 5
```

Use `scripts/record_auto_iteration.py` directly when Codex or a custom runner
performs the edit/verify step and only needs to append a keep/discard/crash row.

当 Codex 或自定义 runner 已经完成编辑和验证，只需要追加 keep/discard/crash
记录时，可以直接使用 `scripts/record_auto_iteration.py`。

For non-trivial harness tasks, call `spawn_agent` from the main Codex session
for each required role, then pass the returned `runtime_agent_id` or `thread_id`
into initialization so artifacts show real parallel execution:

对于非平凡 harness 任务，先由主 Codex 会话为每个必需角色调用 `spawn_agent`，
再把返回的 `runtime_agent_id` 或 `thread_id` 传给初始化脚本，这样 artifacts
会记录真实并行执行：

Replace every `<runtime_agent_id>` below with a concrete ID returned by
`spawn_agent`; placeholders are intentionally rejected by the helpers and
validator.

下面的每个 `<runtime_agent_id>` 都必须替换为 `spawn_agent` 返回的真实 ID；
helper 和 validator 会故意拒绝占位符。

```bash
python3 scripts/init_auto_harness.py \
  --run-dir runs/demo/001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python3 scripts/score.py" \
  --baseline-metric 0 \
  --runtime-subagent "Context Curator=<runtime_agent_id>" \
  --runtime-subagent "Verifier / Evidence Auditor=<runtime_agent_id>"
```

After each runtime subagent completes or is closed, record the terminal event:

每个 runtime 子智能体完成或被关闭后，记录 terminal lifecycle：

```bash
python3 scripts/record_subagent_lifecycle.py \
  --run-dir runs/demo/001 \
  --event completed \
  --role "Verifier / Evidence Auditor" \
  --agent-id verifier-evidence-auditor \
  --stop-reason "verification completed with evidence"
```

Foreground is the default. No detached process is created unless the run is
initialized with `--run-mode background` and launched through
`scripts/harness_runtime_ctl.py`.

前台是默认模式。除非用 `--run-mode background` 初始化并通过
`scripts/harness_runtime_ctl.py` 启动，否则不会创建 detached 后台进程。

Run a detached background loop:

运行显式 opt-in 的 detached 后台循环：

```bash
python3 scripts/init_auto_harness.py \
  --run-dir runs/demo/bg-001 \
  --goal "improve the measured score" \
  --scope src/ \
  --metric score \
  --direction higher \
  --verify "python3 scripts/score.py" \
  --guard "pytest -q" \
  --run-mode background \
  --baseline-metric 0 \
  --runtime-subagent "Context Curator=<runtime_agent_id>" \
  --runtime-subagent "Verifier / Evidence Auditor=<runtime_agent_id>"

python3 scripts/harness_runtime_ctl.py launch \
  --run-dir runs/demo/bg-001 \
  --iteration-command "python3 scripts/propose_one_change.py" \
  --iterations 10

python3 scripts/harness_runtime_ctl.py status --run-dir runs/demo/bg-001
python3 scripts/harness_runtime_ctl.py stop --run-dir runs/demo/bg-001
```

Manage optional user-level Codex hooks:

管理可选的用户级 Codex hooks：

```bash
python3 scripts/harness_hooks_ctl.py status
python3 scripts/harness_hooks_ctl.py install
python3 scripts/harness_hooks_ctl.py uninstall
```

Hooks write future-session context and stop-hook continuation hints for active
`auto_harness` runs. They are managed explicitly and are not installed during
package validation.

hooks 会为 active `auto_harness` 运行写入未来会话上下文和 stop-hook 继续提示。
它们必须显式管理，包验证时不会自动安装。

## Artifact Contract / Artifact 契约

A minimum viable run records:

一次最小可用运行会记录：

```text
manifest.json
subagents.jsonl
skill_invocations.jsonl
events.jsonl
tool_calls.jsonl
failures.jsonl
metrics.json
summary.md
replay.md
```

`references/artifact-contract.md` is the authoritative file and field contract.
New runs should prefer Trace v2 typed events in `events.jsonl`, following
`references/schemas/harness-event.schema.json`. Every material tool call should
have a matching observation, failures should include `error_kind`, and the run
should end with an explicit terminal status. Non-trivial runs must declare
`team_policy.subagent_execution_mode`.

`references/artifact-contract.md` 是权威的文件与字段契约。新的运行应优先在
`events.jsonl` 中使用 Trace v2 类型化事件，并遵循
`references/schemas/harness-event.schema.json`。每个重要工具调用都应有匹配的
observation；失败应包含 `error_kind`；运行必须以明确的终止状态结束。
非平凡运行必须声明 `team_policy.subagent_execution_mode`。

Full auto-harness runs also include `auto_state.json`, `results.tsv`, and
`context.json`. See `SKILL.md` and `references/` for the full contract.

完整的 auto-harness 运行还会包含 `auto_state.json`、`results.tsv` 和
`context.json`。完整契约见 `SKILL.md` 和 `references/`。

For local skill maintenance, sync, validation, and publish steps, see
`references/maintenance-guide.md`.

本地 skill 维护、同步、验证和发布步骤见 `references/maintenance-guide.md`。

## Related GitHub Projects / 关联 GitHub 项目

- [leo-lilinxiao/codex-autoresearch](https://github.com/leo-lilinxiao/codex-autoresearch):
  Codex Autoresearch Skill for goal-driven modify, verify, keep or discard
  loops over mechanically verifiable codebase metrics. This repository borrows
  the measured loop pattern while keeping `$codex-autoresearch` as an
  explicit-request-only external orchestration skill.
  该项目提供目标驱动的修改、验证、保留或丢弃循环；本仓库借鉴其可度量循环模式，
  但仍把 `$codex-autoresearch` 作为显式请求才可使用的外部编排技能。
- [TheGreenCedar/codex-autoresearch](https://github.com/TheGreenCedar/codex-autoresearch):
  Codex plugin for benchmark-contract-driven experiment packets, durable
  session files, structured packet memory, and dashboard-backed review.
  该项目提供 benchmark contract 驱动的实验包、持久化会话文件、结构化 packet
  memory 和 dashboard review 思路。

## Implementation References / 实现参考

This skill remains Codex-native and file-based, but its harness mechanics were
informed by these open-source projects and docs:

本 skill 保持 Codex 原生、文件驱动，但 harness 机制参考了以下开源项目和文档：

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch): fixed-budget
  autonomous research loop with scalar metric comparison and keep/discard
  experimentation.
- [OpenHands Events](https://docs.openhands.dev/sdk/arch/events): append-only,
  typed event logs with source-aware event records.
- [OpenHands Runtime](https://github.com/OpenHands/OpenHands/blob/main/openhands/runtime/README.md):
  controlled runtime interfaces for shell, browser, filesystem, environment,
  and plugin actions.
- [SWE-agent trajectories](https://swe-agent.com/latest/usage/trajectories/):
  thought/action/observation trajectory files for coding-agent replay.
- [SWE-bench harness](https://www.swebench.com/SWE-bench/api/harness/):
  reproducible evaluation harnesses, logs, patches, and environment setup.
- [LangGraph](https://github.com/langchain-ai/langgraph): durable execution
  and human-in-the-loop concepts for long-running agent workflows.
- [Inspect AI analysis](https://inspect.aisi.org.uk/reference/inspect_ai.analysis.html):
  dataframe-style analysis over eval logs, samples, messages, and events.
- [OpenAI Evals](https://github.com/openai/evals): reusable eval registry and
  local eval development pattern.
- [AgentOps](https://github.com/agentops-ai/agentops): session replay,
  nested spans, cost/error tracking, and agent observability patterns.
- [agentevals](https://github.com/agentevals-dev/agentevals): local-first
  evaluation over pre-recorded traces without re-running expensive agents.

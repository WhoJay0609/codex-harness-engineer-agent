---
name: harness-engineer
description: Build and operate agent-first harnesses for reproducible, comparable, iterative AI agent work. Use when creating or improving repo-native feedback loops, autonomous foreground-first auto harness loops, agent-readable context, mechanical gates, traces, startup cleanup of inactive agent threads, proactively formed core and domain expert teams, external domain skill allowlists, run artifacts, failure analysis, and reserved orchestration skill policy.
---

# Harness Engineer

Use this skill to design the system around agent work: goal framing, context
delivery, runtime hygiene, expert roles, skill routing, feedback loops,
mechanical gates, trace artifacts, and evidence-backed termination.

The goal is not "more agents". The goal is reliable execution with inspectable
evidence.

## 中文速览 / Chinese Quick Reference

这个 skill 用来把 Codex 工作组织成可复现、可验证、可回放的 harness。核心目标
不是“多开智能体”，而是让目标、上下文、子智能体、工具、指标、失败和终止状态
都有可审计证据。

- 调用 `$harness-engineer` 即表示允许主 Codex orchestrator 为非平凡任务直接
  调用 `spawn_agent` 创建 runtime 子智能体；把返回的 `runtime_agent_id` 或
  `thread_id` 写入 `subagents.jsonl`。
- 如果 `spawn_agent` 被平台、策略、线程上限或创建失败阻塞，才使用
  `inline_expert_memos`，并记录 blocked category、reason 和 fallback event。
- `auto_harness` 默认在当前 Codex 前台窗口迭代；只有显式 `--run-mode background`
  才允许 detached 后台 runtime。
- 每轮迭代都要先测 baseline，再做一个聚焦修改，运行 guard，记录 keep/discard，
  最后用 `scripts/validate_harness_trace.py <run_dir>` 验证 artifacts。
- `$codex-autoresearch`、`$multi-agent`、`$expert-debate` 仍是显式请求技能；
  不要在用户没要求时主动调用它们。

## Mental Model

Harness engineering has seven layers:

1. Intent: goal, scope, budget, stop conditions, and success criteria.
2. Context: repo map, prior runs, constraints, local instructions, and risks.
3. Team: role capability profiles, real runtime subagents by default for
   non-trivial work, explicit blocked fallback, or single-agent exception for
   trivial work.
4. Tools: skill allowlists, shell/browser/runtime access, and guard commands.
5. Artifacts: manifests, traces, logs, metrics, replay, and summaries.
6. Loop: baseline, change, verify, keep/discard, recover, and terminate.
7. Maintenance: refresh skill inventory, expert library, schemas, and evals as
   the surrounding Codex skill set changes.

Read `references/framework.md` for the full architecture map.

## Operating Modes

- `standard_harness`: design or improve a reproducible agent workflow.
- `auto_harness`: run a foreground-first improve/verify loop over a measurable
  target. This is the built-in Code Auto Research style mode.
- `maintenance`: update this skill package, references, generated expert
  library, or validation scripts.
- `single_agent_exception`: trivial read-only checks, tiny edits, or one-command
  validation. Record the reason when artifacts are produced.

For codebase optimization loops, read `references/code-autoresearch-integration.md`
and `references/auto-harness-mode.md`.

## Required Workflow

1. Frame the work: state the goal, scope, primary metric, guard, budget, stop
   condition, and expected artifacts.
2. Inspect first: read the repo or skill package map before designing or
   editing the harness.
3. Choose the mode and team policy: classify the task, then the main Codex
   orchestrator directly calls `spawn_agent` for the selected roles on
   non-trivial work. Treat `$harness-engineer` invocation as delegation consent
   for this harness task. Use inline expert memos only when `spawn_agent` is
   unavailable, platform/policy blocked, over thread limits after cleanup, or
   creation fails; record the blocked category, reason, and observable fallback
   event.
4. Route skills deliberately: before loading or invoking any skill, send a
   concise user-visible note naming the skill(s) and why they apply; use
   generated expert allowlists for domain work; keep `$codex-autoresearch`,
   `$multi-agent`, and `$expert-debate` explicit request only.
5. Record evidence: write Trace v2 events, tool observations, failures, metrics,
   skill decisions, runtime cleanup, and terminal status when producing a run.
6. Iterate mechanically: measure a baseline, make one focused change or
   experiment, verify, guard, keep or discard, and log the decision.
7. Maintain the harness: when rules, installed skills, or artifact contracts
   change, update references, scripts, eval fixtures, README, and generated
   expert library together.

End only with `goal_met`, `budget_exhausted`, `policy_blocked`,
`environment_blocked`, `user_decision_needed`, or `failed_with_evidence`.

## Artifact Contract

Use `references/artifact-contract.md` as the authoritative run layout and field
contract. Minimum viable runs include `manifest.json`, `subagents.jsonl`,
`skill_invocations.jsonl`, `events.jsonl`, `tool_calls.jsonl`,
`failures.jsonl`, `metrics.json`, `summary.md`, and `replay.md`.

Trace v2 events follow `references/schemas/harness-event.schema.json`. Run
`scripts/validate_harness_trace.py <run_dir>` before trusting a run.

## Reference Map

Architecture:

- `references/framework.md`: skill structure, layer model, and ownership map.
- `references/harness-principles.md`: first principles and source inspiration.
- `references/auto-harness-mode.md`: foreground-first autonomous improve/verify
  loop.
- `references/code-autoresearch-integration.md`: Code Auto Research patterns and
  related projects.
- `references/artifact-contract.md`: run directory layout, file
  responsibilities, and required fields.

Team and runtime:

- `references/expert-capability-library.md` and
  `references/expert-capability-library.json`: generated `harness-experts.v4`
  role library with capability profiles, skill allowlists, and selection
  fields.
- `references/team-formation-policy.md`: proactive team selection and
  single-agent exceptions.
- `references/subagent-runtime.md`: startup cleanup, runtime subagents, fallback
  modes, stop/replace rules, and trace fields.

Direct runtime team protocol:

1. Select the smallest task-class preset with
   `scripts/select_subagent_team.py --task-class <class> --goal <goal>`.
2. Call `spawn_agent` once per selected task card before implementation.
3. Record each returned `agent_id` with
   `scripts/record_subagent_lifecycle.py --event created --runtime-agent-id <id>`.
4. Keep decomposition, context trimming, integration, final verification, and
   artifact integrity in the main thread.
5. Use subagents only for parallel branches: reconnaissance, local
   implementation, independent verification, failure analysis, and risk review.
6. After `wait_agent`/result review, call `close_agent`, then record
   `completed`, `blocked`, `stopped`, or `replaced`. If a subagent is blocked,
   stale, out of scope, or unverifiable, create a replacement with `spawn_agent`
   and record the replacement lifecycle.

Skill routing and escalation:

- `references/skill-routing-policy.md` and `references/skill-inventory.json`:
  installed skill classes, allowlists, and reserved orchestration skills.
- `references/skill-activation-policy.md`: proactive skill checks by subagents.
- `references/decision-support-policy.md`: explicit-request-only policy for
  reserved orchestration skills.
- `references/escalation-policy.md`: adding, stopping, replacing, or escalating
  expert work.

Evidence and maintenance:

- `references/feedback-loop.md`: iteration states, failure records, and harness
  gap records.
- `references/mechanical-gates.md`: validators, schemas, CI gates, and artifact
  checks.
- `references/entropy-garbage-collection.md`: drift cleanup and quality
  gardening.
- `references/maintenance-guide.md`: local validation, sync, publish, and common
  packaging pitfalls.

## Script Map

- Select a runtime team and task cards:
  `scripts/select_subagent_team.py --task-class execution --goal "..."`
- Initialize auto runs: `scripts/init_auto_harness.py --run-dir <run_dir> ...`
  Before running it, the main Codex orchestrator calls `spawn_agent` once per
  required role, then passes repeated
  `--runtime-subagent "Role=<spawn_agent runtime_agent_id>"` arguments. The
  helper records created handles only; terminal lifecycle is recorded after the
  actual subagents finish.
- Record runtime subagent lifecycle:
  `scripts/record_subagent_lifecycle.py --run-dir <run_dir> --event created|completed|blocked|replaced ...`
- Record auto iterations: `scripts/record_auto_iteration.py --run-dir <run_dir> ...`
- Run foreground auto loops:
  `scripts/run_auto_harness.py --run-dir <run_dir> --iteration-command <cmd>`
- Control opt-in background auto loops only after initializing with
  `--run-mode background`:
  `scripts/harness_runtime_ctl.py launch|status|stop --run-dir <run_dir> ...`
- Manage user-level hooks: `scripts/harness_hooks_ctl.py status|install|uninstall`
- Validate runs: `scripts/validate_harness_trace.py <run_dir>`
- Replay runs: `scripts/replay_harness_run.py <run_dir>`
- Query traces: `scripts/query_harness_trace.py <run_dir> ...`
- Export traces: `scripts/export_trace_table.py <run_dir>`
- Compare runs: `scripts/compare_runs.py <run_dir>...`
- Summarize failures: `scripts/summarize_failures.py <run_dir>...`
- Refresh skill inventory: `scripts/update_skill_inventory.py`
- Refresh expert library: `scripts/update_expert_library.py`
- Run self-evals: `scripts/run_harness_evals.py`
- Check package consistency:
  `scripts/check_harness_consistency.py <skill_or_harness_dir>`

If a script reports missing artifacts, stale generated files, or invalid state,
fix the harness evidence before claiming the task is complete.

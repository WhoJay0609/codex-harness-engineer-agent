#!/usr/bin/env python3
"""Generate the harness-engineer expert library from installed skills."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPERT_LIBRARY_VERSION = "harness-experts.v4"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = DEFAULT_ROOT / "references" / "skill-inventory.json"
DEFAULT_JSON_OUTPUT = DEFAULT_ROOT / "references" / "expert-capability-library.json"
DEFAULT_MD_OUTPUT = DEFAULT_ROOT / "references" / "expert-capability-library.md"


@dataclass(frozen=True)
class RoleDefinition:
    role: str
    capability: str
    output_schema: str
    keywords: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    role_type: str = "domain_specialist"


@dataclass(frozen=True)
class CapabilityProfile:
    activation_criteria: tuple[str, ...] = ()
    input_contract: tuple[str, ...] = ()
    deliverables: tuple[str, ...] = ()
    verification_focus: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    collaboration: tuple[str, ...] = ()


CORE_ROLE_CAPABILITIES: dict[str, CapabilityProfile] = {
    "Professor Orchestrator": CapabilityProfile(
        activation_criteria=(
            "Use for every non-trivial harness run that needs final judgment, team lifecycle control, or closeout.",
            "Use when multiple specialists produce conflicting findings or when stop/continue decisions affect scope.",
        ),
        input_contract=(
            "User goal, scope, constraints, acceptance criteria, and budget.",
            "Current team state, task cards, trace artifacts, and open escalations.",
        ),
        deliverables=(
            "A final orchestrator decision with selected path, rationale, accepted evidence, and terminal status.",
            "Team additions, stops, replacements, and reserved-skill decisions recorded in harness artifacts.",
        ),
        verification_focus=(
            "Success is backed by artifacts rather than consensus or intent.",
            "The chosen terminal status matches the evidence and remaining blockers.",
        ),
        risk_flags=(
            "Unresolved specialist disagreement.",
            "A claim of completion without verifier evidence.",
            "Implicit use of reserved orchestration skills.",
        ),
        collaboration=(
            "Receives context packets and verifier reports.",
            "Assigns or updates specialist task cards and owns the final synthesis.",
        ),
    ),
    "Intent Router": CapabilityProfile(
        activation_criteria=(
            "Use at startup when task class, success criteria, domains, or approval boundaries are unclear.",
            "Use again when new evidence changes the domain or risk profile.",
        ),
        input_contract=(
            "Latest user request, local guidance, project constraints, and available skill inventory.",
            "Known budget, risk tolerance, and whether the user explicitly requested external orchestration skills.",
        ),
        deliverables=(
            "A task classification with required roles, explicit assumptions, and approval boundaries.",
            "A routing note that explains which domain specialists should be added or skipped.",
        ),
        verification_focus=(
            "The route is specific enough to create task cards.",
            "Reserved orchestration skills remain blocked unless explicitly requested.",
        ),
        risk_flags=(
            "Ambiguous user intent that would make implementation risky.",
            "Task treated as trivial despite behavior, data, or workflow impact.",
        ),
        collaboration=(
            "Feeds Task Decomposer and Professor Orchestrator.",
            "Receives stale-context warnings from Context Curator.",
        ),
    ),
    "Context Curator": CapabilityProfile(
        activation_criteria=(
            "Use when repo, paper, artifact, or prior-run context must be summarized before execution.",
            "Use when a dirty tree, stale docs, or generated outputs may affect the task.",
        ),
        input_contract=(
            "Repo map, relevant files, memory notes, prior run artifacts, and local instructions.",
            "Known source-of-truth files and any artifacts that must not be modified.",
        ),
        deliverables=(
            "A compact context packet with authoritative files, risks, stale areas, and unknowns.",
            "Pointers to evidence paths that downstream specialists should read first.",
        ),
        verification_focus=(
            "Context cites current files or explicitly marks memory-derived facts as stale-risk.",
            "Unrelated user work is identified and preserved.",
        ),
        risk_flags=(
            "Relying on old summaries when current files are cheap to inspect.",
            "Confusing generated artifacts with source-of-truth files.",
        ),
        collaboration=(
            "Hands context packets to all specialists.",
            "Asks Entropy Gardener or Verifier to inspect drift when needed.",
        ),
    ),
    "Task Decomposer": CapabilityProfile(
        activation_criteria=(
            "Use when the goal needs multiple tasks, dependencies, budgets, or acceptance checks.",
            "Use before creating runtime subagents or long-running loops.",
        ),
        input_contract=(
            "Goal, scope, role set, known dependencies, constraints, and stop conditions.",
            "Available commands, expected artifacts, and validation gates.",
        ),
        deliverables=(
            "Task cards with scope, inputs, outputs, allowed skills, budgets, and escalation triggers.",
            "A dependency order that separates blocking and parallel work.",
        ),
        verification_focus=(
            "Each task card has a measurable output and a stop condition.",
            "No two specialists own the same write scope unless coordination is explicit.",
        ),
        risk_flags=(
            "Duplicated work across specialists.",
            "A task card that cannot be verified mechanically or by artifact review.",
        ),
        collaboration=(
            "Uses Intent Router classification and expert library profiles.",
            "Hands task cards to Professor Orchestrator for creation decisions.",
        ),
    ),
    "Debate Moderator": CapabilityProfile(
        activation_criteria=(
            "Use when there are credible alternative approaches or high-risk assumptions.",
            "Use when the user requested adversarial or expert-style deliberation inside the harness.",
        ),
        input_contract=(
            "Candidate approaches, evidence constraints, decision criteria, and debate mode.",
            "Independent specialist findings when available.",
        ),
        deliverables=(
            "A structured deliberation summary with positions, critiques, revisions, and moderator conclusion.",
            "A decision-ready shortlist with reasons to accept or reject each option.",
        ),
        verification_focus=(
            "Critiques target assumptions and evidence, not personalities or preferences.",
            "Moderator synthesis preserves unresolved uncertainty.",
        ),
        risk_flags=(
            "False consensus.",
            "Unbounded debate that delays a measurable next step.",
        ),
        collaboration=(
            "Coordinates Red Team Critic and domain specialists.",
            "Returns the synthesized decision to Professor Orchestrator.",
        ),
    ),
    "Red Team Critic": CapabilityProfile(
        activation_criteria=(
            "Use for high-risk changes, paper claims, irreversible operations, or weak evidence.",
            "Use when the apparent solution may hide simpler alternatives or invalid assumptions.",
        ),
        input_contract=(
            "Proposed plan, evidence, assumptions, constraints, and rollback path.",
            "Known failure modes and acceptance criteria.",
        ),
        deliverables=(
            "A risk report with blocking issues, non-blocking caveats, and safer alternatives.",
            "Specific checks or edits needed before claiming success.",
        ),
        verification_focus=(
            "Every blocking concern ties to concrete evidence or plausible failure impact.",
            "Recommendations are actionable within current scope.",
        ),
        risk_flags=(
            "Overclaiming beyond measured evidence.",
            "Hidden destructive action or undocumented behavior change.",
        ),
        collaboration=(
            "Reviews plans from Professor Orchestrator and domain specialists.",
            "Hands concrete guard suggestions to Verifier or Mechanical Gatekeeper.",
        ),
    ),
    "Harness Architect": CapabilityProfile(
        activation_criteria=(
            "Use when artifact contracts, schemas, validators, run layout, or team protocols change.",
            "Use when the harness needs a new repeatable workflow rather than a one-off fix.",
        ),
        input_contract=(
            "Current references, scripts, schema contracts, validation failures, and target behavior.",
            "Compatibility constraints for existing run artifacts.",
        ),
        deliverables=(
            "A harness design with artifact ownership, schema changes, and validation strategy.",
            "Updated references or scripts when the design is implemented.",
        ),
        verification_focus=(
            "New behavior is documented in the owning reference.",
            "Generated files are regenerated rather than hand-edited.",
        ),
        risk_flags=(
            "New required field without validator support.",
            "Policy duplicated across references with divergent wording.",
        ),
        collaboration=(
            "Works with Mechanical Gatekeeper on enforceable checks.",
            "Uses Verifier to confirm generated artifacts and evals.",
        ),
    ),
    "Runner Coordinator": CapabilityProfile(
        activation_criteria=(
            "Use when baseline, candidate, guard, or background execution must be coordinated.",
            "Use when command provenance and runtime state determine the decision.",
        ),
        input_contract=(
            "Run command, verify command, guard command, working directory, budget, and metric direction.",
            "Current dirty-tree state and isolation requirements.",
        ),
        deliverables=(
            "Run coordination report with commands, outputs, metrics, and keep/discard recommendation.",
            "Updated run artifacts for baseline and candidate iterations.",
        ),
        verification_focus=(
            "Commands ran in the intended environment and directory.",
            "Metrics and guard results are recorded before any keep decision.",
        ),
        risk_flags=(
            "Comparing runs from different environments or datasets.",
            "Leaving long-running sessions active after closeout.",
        ),
        collaboration=(
            "Receives task cards from Task Decomposer.",
            "Hands logs and metrics to Verifier and Failure Analyst.",
        ),
    ),
    "Verifier / Evidence Auditor": CapabilityProfile(
        activation_criteria=(
            "Use before claiming success on any non-trivial change, result, or document update.",
            "Use when evidence freshness, metric validity, or source alignment matters.",
        ),
        input_contract=(
            "Acceptance criteria, changed files, command logs, metrics, generated artifacts, and source references.",
            "Known skipped checks and reasons.",
        ),
        deliverables=(
            "A verification report listing passed checks, failed checks, skipped checks, and residual risk.",
            "Concrete evidence paths or command summaries that support the final claim.",
        ),
        verification_focus=(
            "Every success claim maps to a command, file, metric, or cited source.",
            "Skipped validation is explicit and not silently treated as pass.",
        ),
        risk_flags=(
            "Freshness gap between source data and written claims.",
            "Passing smoke check used as proof of broad behavior.",
        ),
        collaboration=(
            "Audits Runner Coordinator outputs and domain specialist claims.",
            "Reports blockers to Professor Orchestrator before closeout.",
        ),
    ),
    "Failure Analyst": CapabilityProfile(
        activation_criteria=(
            "Use after failed commands, inconsistent metrics, blocked tools, or repeated recovery attempts.",
            "Use when the root cause may be code, environment, data, context, policy, or metric design.",
        ),
        input_contract=(
            "Failure logs, commands, expected behavior, recent changes, environment details, and retry history.",
            "Any partial outputs or artifacts produced before failure.",
        ),
        deliverables=(
            "A failure classification with root-cause hypothesis, evidence, and next recovery action.",
            "A record of environment or policy blockers when recovery is not possible.",
        ),
        verification_focus=(
            "Hypotheses are tied to observed logs or reproduced behavior.",
            "Recovery actions are bounded and do not hide invalid state.",
        ),
        risk_flags=(
            "Retrying without changing evidence or hypothesis.",
            "Adding fallback paths that make invalid state appear valid.",
        ),
        collaboration=(
            "Receives logs from Runner Coordinator and Verifier.",
            "Hands recurrent gaps to Mechanical Gatekeeper.",
        ),
    ),
    "Mechanical Gatekeeper": CapabilityProfile(
        activation_criteria=(
            "Use when a repeated rule, artifact contract, or review comment can become an executable check.",
            "Use when validation should reject stale generated files or invalid traces.",
        ),
        input_contract=(
            "Policy text, examples of valid/invalid state, expected error messages, and target command.",
            "Existing validators, schemas, and eval fixtures.",
        ),
        deliverables=(
            "A gate proposal or implementation with command, scope, failure mode, and maintenance owner.",
            "Updated eval fixture when validator behavior changes.",
        ),
        verification_focus=(
            "Gate fails on a representative bad case and passes on a representative good case.",
            "Error messages identify the actionable fix.",
        ),
        risk_flags=(
            "Check is too broad and blocks unrelated local work.",
            "Validator enforces undocumented policy.",
        ),
        collaboration=(
            "Works with Harness Architect on schema and policy ownership.",
            "Asks Verifier to run the full validation set.",
        ),
    ),
    "Trace Auditor": CapabilityProfile(
        activation_criteria=(
            "Use when run replayability, trace completeness, or skill invocation records are central.",
            "Use before trusting a harness run as evidence.",
        ),
        input_contract=(
            "manifest.json, subagents.jsonl, skill_invocations.jsonl, events.jsonl, tool_calls.jsonl, failures.jsonl, metrics.json, and replay.md.",
            "Expected team policy and terminal status.",
        ),
        deliverables=(
            "A trace audit listing missing, stale, inconsistent, or unverifiable artifacts.",
            "Replayability verdict and required repair steps.",
        ),
        verification_focus=(
            "Each tool call has a matching observation when required.",
            "Subagents have creation and terminal events.",
        ),
        risk_flags=(
            "Terminal success without trace evidence.",
            "Skill use outside allowlist or missing skill decision record.",
        ),
        collaboration=(
            "Feeds Verifier and Professor Orchestrator.",
            "Hands repeated trace defects to Mechanical Gatekeeper.",
        ),
    ),
    "Entropy Gardener": CapabilityProfile(
        activation_criteria=(
            "Use when docs, generated files, duplicate helpers, or skill allowlists may have drifted.",
            "Use during maintenance or repository cleanup before broad edits.",
        ),
        input_contract=(
            "Repo or skill package map, generated-file policy, ignore rules, validators, and current status.",
            "Known user-owned or unrelated changes to preserve.",
        ),
        deliverables=(
            "An entropy report ranking drift, duplication, stale docs, and cleanup candidates by risk.",
            "A bounded cleanup plan that separates source changes from generated artifacts.",
        ),
        verification_focus=(
            "Cleanup recommendations are additive or explicitly scoped.",
            "Generated files are refreshed by their owner scripts.",
        ),
        risk_flags=(
            "Deleting useful local state.",
            "Changing behavior while claiming repository hygiene only.",
        ),
        collaboration=(
            "Supplies drift findings to Context Curator and Harness Architect.",
            "Asks Verifier to confirm cleanup gates.",
        ),
    ),
}


DOMAIN_CAPABILITY_HINTS: dict[str, CapabilityProfile] = {
    "research": CapabilityProfile(
        activation_criteria=("Use when novelty, literature, research workflow, or claim boundaries shape the next step.",),
        input_contract=("Research question, target venue or audience, seed papers, known baselines, and evidence constraints.",),
        deliverables=("A research-facing artifact with assumptions, related work boundaries, and next validation step.",),
        verification_focus=("Separate published evidence from engineering inference and untested hypotheses.",),
        risk_flags=("Novelty or claim wording exceeds the evidence gathered.",),
        collaboration=("Coordinate with Verifier / Evidence Auditor before paper or result claims are finalized.",),
    ),
    "paper": CapabilityProfile(
        activation_criteria=("Use when paper text, LaTeX, figures, tables, claims, or submission material is the work product.",),
        input_contract=("Manuscript sources, result artifacts, venue constraints, figure/table inputs, and compile command.",),
        deliverables=("Publication-ready text or assets tied to exact source files and result evidence.",),
        verification_focus=("Claims, numbers, captions, and tables match current artifacts and compile cleanly when applicable.",),
        risk_flags=("Invented results, stale tables, or venue/template drift.",),
        collaboration=("Coordinate with Literature / Novelty Expert and Verifier / Evidence Auditor for claim safety.",),
    ),
    "experiment": CapabilityProfile(
        activation_criteria=("Use when metrics, ablations, training/evaluation runs, or result interpretation drives the task.",),
        input_contract=("Baseline, metric definition, dataset/config, run commands, environment, and output root.",),
        deliverables=("Experiment matrix, run plan, analysis, or monitoring report with reproducible commands.",),
        verification_focus=("Compare like with like: same dataset, environment, metric direction, and source artifacts.",),
        risk_flags=("Partial runs treated as final, environment mismatch, or metric normalization errors.",),
        collaboration=("Coordinate with Runner Coordinator for execution and Verifier / Evidence Auditor for result trust.",),
    ),
    "software": CapabilityProfile(
        activation_criteria=("Use when code, APIs, UI, deployment, CI, security, or repository structure must change.",),
        input_contract=("Repo instructions, current status, relevant files, expected behavior, tests, and rollback constraints.",),
        deliverables=("A scoped implementation or review artifact with changed files, tests, and residual risk.",),
        verification_focus=("Behavior changes are documented, tested, and aligned with existing project conventions.",),
        risk_flags=("Unrelated refactor, hidden fallback, destructive git operation, or unverified UI/deploy state.",),
        collaboration=("Coordinate with Context Curator before edits and Verifier / Evidence Auditor before closeout.",),
    ),
    "ml": CapabilityProfile(
        activation_criteria=("Use when model training, fine-tuning, inference, compression, architecture, or evaluation is central.",),
        input_contract=("Model, data, hardware, environment, config, checkpoint, metric, and budget constraints.",),
        deliverables=("Model workflow plan, code change, run config, or evaluation report with provenance.",),
        verification_focus=("Runtime provenance, model semantics, and metric interpretation are explicit and reproducible.",),
        risk_flags=("Wrong environment, incompatible checkpoint semantics, or comparing non-equivalent model states.",),
        collaboration=("Coordinate with Experiment / Metrics Expert and Verifier / Evidence Auditor.",),
    ),
    "data": CapabilityProfile(
        activation_criteria=("Use when retrieval, data prep, tokenization, documents, or knowledge capture is central.",),
        input_contract=("Data sources, schema, access constraints, freshness requirements, and output format.",),
        deliverables=("Prepared data, retrieval plan, document artifact, or knowledge record with source provenance.",),
        verification_focus=("Source freshness, schema validity, and downstream consumption are checked.",),
        risk_flags=("Stale data, lossy conversion, missing provenance, or private data leakage.",),
        collaboration=("Coordinate with Context Curator and Verifier / Evidence Auditor.",),
    ),
    "ops": CapabilityProfile(
        activation_criteria=("Use when operations, notification, deployment, project reporting, or runtime reliability is central.",),
        input_contract=("Target service or workflow, credentials/connectors available, status, rollback plan, and audience.",),
        deliverables=("Operational action plan, deployment summary, notification, or project report with status and risk.",),
        verification_focus=("External actions are confirmed through their authoritative system when available.",),
        risk_flags=("Assuming remote state from local output alone, or performing irreversible operations without explicit scope.",),
        collaboration=("Coordinate with Professor Orchestrator for approval boundaries and Verifier for final state checks.",),
    ),
}


CORE_ROLES: tuple[RoleDefinition, ...] = (
    RoleDefinition(
        "Professor Orchestrator",
        "Owns final judgment, pipeline choice, expert creation/stop/replacement, approval gates, and execution closeout.",
        "orchestrator_decision",
        preferred_skills=("harness-engineer", "planner", "deep-interview", "software-engineer", "project-phase-report"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Intent Router",
        "Classifies user intent, task class, success criteria, required domain specialists, and whether execution needs approval first.",
        "intent_route",
        preferred_skills=("deep-interview", "planner", "research-refine", "research-survey", "doc"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Context Curator",
        "Builds repo, paper, material, data, and artifact context packets for downstream experts.",
        "context_packet",
        preferred_skills=("software-engineer", "research-survey", "doc", "pdf", "spreadsheet", "jupyter-notebook"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Task Decomposer",
        "Converts goals into task cards, dependencies, budgets, stop conditions, and acceptance checks.",
        "task_card_set",
        preferred_skills=("planner", "waterfall-delivery", "software-engineer", "project-phase-report"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Debate Moderator",
        "Runs internal deliberation: independent positions, rebuttals, revisions, and moderator synthesis.",
        "deliberation_summary",
        preferred_skills=("research-review", "analyze-results", "planner", "deep-interview"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Red Team Critic",
        "Challenges assumptions, hidden risks, overclaiming, missing baselines, irreversible actions, and simpler alternatives.",
        "red_team_report",
        preferred_skills=("research-review", "security-threat-model", "repo-refactor-governance", "analyze-results"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Harness Architect",
        "Designs artifact contracts, state schema, run layout, subagent protocols, and mechanical gates.",
        "harness_design",
        preferred_skills=("skill-creator", "plugin-creator", "software-engineer", "repo-refactor-governance", "waterfall-delivery"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Runner Coordinator",
        "Coordinates baseline, candidate execution, auto-loop iterations, worktree isolation, and command evidence.",
        "run_coordination_report",
        preferred_skills=("run-experiment", "monitor-experiment", "experiment-bridge", "software-engineer"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Verifier / Evidence Auditor",
        "Checks acceptance criteria, metrics, logs, tests, paper evidence, document evidence, and source freshness.",
        "verification_report",
        preferred_skills=("analyze-results", "playwright", "paper-compile", "pdf", "spreadsheet", "software-engineer"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Failure Analyst",
        "Classifies failures as code, context, tool, constraint, metric, environment, team, or policy gaps.",
        "failure_report",
        preferred_skills=("analyze-results", "monitor-experiment", "sentry", "software-engineer", "gh-fix-ci"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Mechanical Gatekeeper",
        "Converts repeated guidance into scripts, schemas, validators, lint checks, CI checks, and artifact gates.",
        "gate_proposal",
        preferred_skills=("software-engineer", "repo-refactor-governance", "gh-fix-ci", "security-best-practices"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Trace Auditor",
        "Checks trace completeness, task-card closure, skill invocation records, escalation records, and replayability.",
        "trace_audit",
        preferred_skills=("software-engineer", "analyze-results", "repo-refactor-governance"),
        role_type="core_council",
    ),
    RoleDefinition(
        "Entropy Gardener",
        "Finds stale docs, duplicate helpers, invalid fallbacks, bloated files, drifted skill allowlists, and repo hygiene gaps.",
        "entropy_report",
        preferred_skills=("repo-refactor-governance", "software-engineer", "doc", "project-phase-report"),
        role_type="core_council",
    ),
)


DOMAIN_ROLES: tuple[RoleDefinition, ...] = (
    RoleDefinition(
        "Research Ideation Expert",
        "Generates and refines research ideas with creativity, novelty pressure, and implementation awareness.",
        "idea_set",
        keywords=("idea", "creative", "brainstorm", "research-refine"),
    ),
    RoleDefinition(
        "Literature / Novelty Expert",
        "Searches related work, closest prior art, novelty gaps, and claim boundaries.",
        "novelty_report",
        keywords=("arxiv", "literature", "lit", "survey", "novelty", "review", "prior art", "comm-lit"),
    ),
    RoleDefinition(
        "Research Pipeline Expert",
        "Plans research ideation, experiment bridging, autonomous review loops, and research workflow handoffs.",
        "research_pipeline_plan",
        keywords=("research-pipeline", "autoresearch", "auto-review", "experiment-bridge", "pipeline"),
    ),
    RoleDefinition(
        "Theory Expert",
        "Formalizes assumptions, formulas, proofs, lemmas, theorem wording, and rigor boundaries.",
        "theory_report",
        keywords=("formula", "proof", "theory", "derivation", "mathematical"),
    ),
    RoleDefinition(
        "Paper-to-Code Expert",
        "Converts a paper method into implementable modules, pseudocode, configs, minimal trials, and tests.",
        "implementation_bridge",
        keywords=("paper-to-code", "implementation", "bridge", "method"),
    ),
    RoleDefinition(
        "Paper Writing Expert",
        "Structures papers, writes sections, compiles LaTeX, and improves submission narratives.",
        "writing_plan",
        keywords=("paper", "latex", "writing", "compile", "ml-paper", "systems-paper"),
    ),
    RoleDefinition(
        "Paper Figures / Talks Expert",
        "Creates paper figures, tables, posters, slides, captions, and conference talk material.",
        "presentation_plan",
        keywords=("figure", "plot", "illustration", "poster", "slides", "presentation", "talk", "academic-plotting"),
    ),
    RoleDefinition(
        "Experiment / Metrics Expert",
        "Designs experiments, ablations, metrics, analysis tables, and reproducibility checks.",
        "experiment_matrix",
        keywords=("experiment", "metric", "monitor", "analyze", "jupyter", "spreadsheet", "swanlab"),
    ),
    RoleDefinition(
        "Algorithm Expert",
        "Diagnoses algorithms, proposes variants, tunes objectives, and designs benchmark-driven improvement loops.",
        "algorithm_plan",
        keywords=("algorithm", "dse", "optimization", "objective", "benchmark"),
    ),
    RoleDefinition(
        "ML Training Expert",
        "Designs model training, distributed training, debugging, throughput optimization, and experiment tracking.",
        "training_plan",
        keywords=("training", "train", "deepspeed", "accelerate", "fsdp", "lightning", "megatron", "torchtitan", "ray-train"),
    ),
    RoleDefinition(
        "LLM Fine-Tuning Expert",
        "Designs supervised fine-tuning, preference optimization, RLHF/GRPO/PPO, LoRA/QLoRA, and post-training.",
        "finetuning_plan",
        keywords=("fine-tuning", "finetuning", "rlhf", "grpo", "ppo", "lora", "peft", "trl", "verl", "unsloth", "simpo"),
    ),
    RoleDefinition(
        "LLM Serving Expert",
        "Designs inference serving, quantized deployment, throughput/latency tuning, and cloud execution.",
        "serving_plan",
        keywords=("serving", "serve", "inference", "vllm", "sglang", "tensorrt", "llama-cpp", "speculative", "modal", "skypilot", "lambda"),
    ),
    RoleDefinition(
        "Compression Expert",
        "Designs quantization, pruning, distillation, sparsity, and model merging plans.",
        "compression_plan",
        keywords=("quant", "pruning", "distillation", "spars", "merging", "awq", "gptq", "hqq", "bitsandbytes", "gguf"),
    ),
    RoleDefinition(
        "Model Architecture Expert",
        "Designs or analyzes LLM architectures, long context, MoE, attention optimization, and model internals.",
        "architecture_research_plan",
        keywords=("architecture", "litgpt", "nanogpt", "mamba", "rwkv", "moe", "long-context", "attention", "flash"),
    ),
    RoleDefinition(
        "Interpretability Expert",
        "Performs mechanistic interpretability, activation interventions, sparse autoencoder analysis, and causal tracing.",
        "interpretability_plan",
        keywords=("interpretability", "intervention", "activation", "sae", "sparse-autoencoder", "nnsight", "pyvene", "transformer-lens"),
    ),
    RoleDefinition(
        "Evaluation / Benchmark Expert",
        "Designs benchmark harnesses, LLM evaluation, BigCode evaluation, run tracking, and result dashboards.",
        "benchmark_report",
        keywords=("evaluation", "evaluator", "benchmark", "bigcode", "lm-evaluation", "weights", "mlflow", "tensorboard", "langsmith", "phoenix"),
    ),
    RoleDefinition(
        "RAG / Agents Expert",
        "Builds RAG, agent workflows, structured outputs, tool calling, and document retrieval pipelines.",
        "rag_agent_plan",
        keywords=("rag", "agent", "langchain", "llamaindex", "dspy", "guidance", "instructor", "outlines", "autogpt", "crewai"),
    ),
    RoleDefinition(
        "Retrieval / Vector DB Expert",
        "Designs vector stores, embedding, retrieval, semantic search, indexing, and production retrieval choices.",
        "retrieval_plan",
        keywords=("vector", "retrieval", "embedding", "semantic", "chroma", "faiss", "qdrant", "pinecone", "sentence-transformers"),
    ),
    RoleDefinition(
        "Tokenizer / Data Expert",
        "Designs tokenization, dataset curation, distributed data processing, and structured data preparation.",
        "data_plan",
        keywords=("token", "data", "dataset", "curator", "ray-data", "sentencepiece", "nemo-curator"),
    ),
    RoleDefinition(
        "Multimodal / Vision Expert",
        "Works on image, vision-language, segmentation, diffusion, and visual asset tasks.",
        "multimodal_plan",
        keywords=("vision", "image", "multimodal", "clip", "blip", "llava", "segment", "diffusion", "pixel", "screenshot"),
    ),
    RoleDefinition(
        "Robotics / Embodied Expert",
        "Handles robotics idea discovery, OpenPI/OpenVLA policy tuning, embodied benchmarks, and sim-to-real constraints.",
        "robotics_plan",
        keywords=("robot", "embodied", "openpi", "openvla", "cosmos"),
    ),
    RoleDefinition(
        "Audio / Speech Expert",
        "Handles transcription, speech generation, audio generation, and video/audio prompt workflows.",
        "audio_plan",
        keywords=("audio", "speech", "transcribe", "whisper", "audiocraft", "sora"),
    ),
    RoleDefinition(
        "Safety / Guardrails Expert",
        "Designs moderation, prompt-injection detection, policy enforcement, and AI guardrails.",
        "guardrails_plan",
        keywords=("guard", "safety", "moderation", "policy", "constitutional", "prompt-injection", "llamaguard"),
    ),
    RoleDefinition(
        "Frontend / Design Expert",
        "Builds frontend UI, Figma integration, design systems, responsive states, and browser verification.",
        "frontend_plan",
        keywords=("frontend", "figma", "design", "ui", "browser", "playwright"),
    ),
    RoleDefinition(
        "Backend / API Expert",
        "Designs backend services, APIs, ChatGPT Apps, CLIs, OpenAI product integration, and server behavior.",
        "api_plan",
        keywords=("backend", "api", "aspnet", "chatgpt", "cli", "openai", "plugin", "software-engineer", "skill-creator", "skill-installer"),
    ),
    RoleDefinition(
        "Game / Desktop Expert",
        "Builds web games, desktop apps, and browser-verified interactive experiences.",
        "interactive_app_plan",
        keywords=("game", "desktop", "winui", "interactive"),
    ),
    RoleDefinition(
        "Security / Reliability Expert",
        "Handles threat models, best practices, ownership maps, production errors, and incident evidence.",
        "security_reliability_review",
        keywords=("security", "reliability", "threat", "sentry", "ownership", "incident"),
    ),
    RoleDefinition(
        "CI / PR Expert",
        "Handles Git/PR discipline, review comments, GitHub CI, and PR-ready delivery.",
        "ci_pr_plan",
        keywords=("git", "github", "pr", "ci", "gh-", "review-comments", "yeet"),
    ),
    RoleDefinition(
        "Deploy Expert",
        "Handles Vercel, Netlify, Cloudflare, Render, preview, production deploy, and rollback.",
        "deploy_plan",
        keywords=("deploy", "vercel", "netlify", "cloudflare", "render"),
    ),
    RoleDefinition(
        "Documents / Materials Expert",
        "Creates and edits documents, PDFs, spreadsheets, slides, grant materials, and progress reports.",
        "material_plan",
        keywords=("doc", "pdf", "spreadsheet", "slides", "grant", "material", "report"),
    ),
    RoleDefinition(
        "Knowledge / Notion Expert",
        "Captures knowledge, researches Notion, prepares meetings, and turns Notion specs into implementation plans.",
        "knowledge_plan",
        keywords=("notion", "knowledge", "meeting"),
    ),
    RoleDefinition(
        "Project Delivery Expert",
        "Creates phase plans, waterfall delivery records, client-facing reports, and milestone acceptance.",
        "delivery_plan",
        keywords=("project", "planner", "phase", "waterfall", "delivery", "milestone"),
    ),
    RoleDefinition(
        "Notification / Ops Expert",
        "Handles Feishu notifications, Linear issue workflows, Sentry summaries, and operational reporting.",
        "ops_plan",
        keywords=(
            "notify",
            "notification",
            "message",
            "messaging",
            "bridge",
            "telegram",
            "discord",
            "feishu",
            "lark",
            "qq",
            "wechat",
            "weixin",
            "linear",
            "ops",
            "sentry",
        ),
    ),
)


DOMAIN_ROLE_PREFERRED_SKILLS: dict[str, tuple[str, ...]] = {
    "Research Ideation Expert": (
        "idea-creator",
        "idea-discovery",
        "brainstorming-research-ideas",
        "creative-thinking-for-research",
        "research-refine-pipeline",
    ),
    "Literature / Novelty Expert": (
        "arxiv",
        "research-lit",
        "research-survey",
        "novelty-check",
        "comm-lit-review",
    ),
    "Research Pipeline Expert": (
        "0-autoresearch-skill",
        "research-pipeline",
        "experiment-plan",
        "experiment-bridge",
        "auto-review-loop",
        "auto-review-loop-llm",
        "auto-review-loop-minimax",
    ),
    "Theory Expert": ("formula-derivation", "proof-writer", "research-refine"),
    "Paper-to-Code Expert": (
        "software-engineer",
        "research-lit",
        "experiment-plan",
        "run-experiment",
        "analyze-results",
        "notion-spec-to-implementation",
    ),
    "Paper Writing Expert": (
        "paper-plan",
        "paper-write",
        "paper-writing",
        "paper-compile",
        "ml-paper-writing",
        "systems-paper-writing",
        "auto-paper-improvement-loop",
    ),
    "Paper Figures / Talks Expert": (
        "paper-figure",
        "paper-illustration",
        "academic-plotting",
        "paper-slides",
        "paper-poster",
        "presenting-conference-talks",
        "slides",
    ),
    "Experiment / Metrics Expert": (
        "experiment-plan",
        "run-experiment",
        "monitor-experiment",
        "analyze-results",
        "jupyter-notebook",
        "spreadsheet",
        "swanlab",
    ),
    "Algorithm Expert": (
        "algorithm-improvement-loop",
        "dse-loop",
        "formula-derivation",
        "proof-writer",
        "analyze-results",
        "software-engineer",
    ),
    "ML Training Expert": (
        "ml-training-recipes",
        "pytorch-lightning",
        "accelerate",
        "deepspeed",
        "pytorch-fsdp2",
        "megatron-core",
        "torchtitan",
        "ray-train",
    ),
    "LLM Fine-Tuning Expert": (
        "axolotl",
        "llama-factory",
        "peft",
        "trl-fine-tuning",
        "verl",
        "openrlhf",
        "grpo-rl-training",
        "simpo",
        "unsloth",
        "slime",
        "miles",
        "torchforge",
    ),
    "LLM Serving Expert": (
        "vllm",
        "sglang",
        "tensorrt-llm",
        "llama-cpp",
        "gguf",
        "speculative-decoding",
        "modal",
        "skypilot",
        "lambda-labs",
    ),
    "Compression Expert": (
        "bitsandbytes",
        "awq",
        "gptq",
        "hqq",
        "model-pruning",
        "knowledge-distillation",
        "model-merging",
        "gguf",
    ),
    "Model Architecture Expert": (
        "litgpt",
        "nanogpt",
        "mamba",
        "rwkv",
        "moe-training",
        "long-context",
        "flash-attention",
    ),
    "Interpretability Expert": ("transformer-lens", "nnsight", "pyvene", "saelens"),
    "Evaluation / Benchmark Expert": (
        "lm-evaluation-harness",
        "bigcode-evaluation-harness",
        "nemo-evaluator",
        "analyze-results",
        "weights-and-biases",
        "mlflow",
        "tensorboard",
        "swanlab",
    ),
    "RAG / Agents Expert": (
        "llamaindex",
        "langchain",
        "dspy",
        "guidance",
        "instructor",
        "outlines",
        "autogpt",
        "crewai",
        "a-evolve",
    ),
    "Retrieval / Vector DB Expert": (
        "chroma",
        "faiss",
        "qdrant",
        "pinecone",
        "sentence-transformers",
    ),
    "Tokenizer / Data Expert": (
        "huggingface-tokenizers",
        "sentencepiece",
        "nemo-curator",
        "ray-data",
        "spreadsheet",
    ),
    "Multimodal / Vision Expert": (
        "clip",
        "blip-2",
        "llava",
        "segment-anything",
        "stable-diffusion",
        "imagegen",
        "pixel-art",
        "screenshot",
    ),
    "Robotics / Embodied Expert": ("idea-discovery-robot", "openpi", "openvla-oft", "cosmos-policy"),
    "Audio / Speech Expert": ("whisper", "transcribe", "speech", "audiocraft", "sora"),
    "Safety / Guardrails Expert": (
        "prompt-guard",
        "llamaguard",
        "nemo-guardrails",
        "constitutional-ai",
        "security-threat-model",
    ),
    "Frontend / Design Expert": (
        "frontend",
        "figma",
        "figma-use",
        "figma-implement-design",
        "figma-generate-design",
        "figma-generate-library",
        "figma-create-design-system-rules",
        "figma-code-connect-components",
        "playwright",
        "playwright-interactive",
    ),
    "Backend / API Expert": (
        "software-engineer",
        "aspnet-core",
        "chatgpt-apps",
        "cli-creator",
        "openai-docs",
        "plugin-creator",
        "skill-creator",
        "skill-installer",
    ),
    "Game / Desktop Expert": ("develop-web-game", "winui-app", "playwright", "software-engineer"),
    "Security / Reliability Expert": (
        "security-threat-model",
        "security-best-practices",
        "security-ownership-map",
        "sentry",
    ),
    "CI / PR Expert": ("git-pr-workflow", "gh-fix-ci", "gh-address-comments", "yeet"),
    "Deploy Expert": ("vercel-deploy", "netlify-deploy", "cloudflare-deploy", "render-deploy"),
    "Documents / Materials Expert": (
        "doc",
        "pdf",
        "spreadsheet",
        "slides",
        "grant-proposal",
        "project-phase-report",
        "notion-knowledge-capture",
    ),
    "Knowledge / Notion Expert": (
        "notion-knowledge-capture",
        "notion-research-documentation",
        "notion-meeting-intelligence",
        "notion-spec-to-implementation",
    ),
    "Project Delivery Expert": (
        "planner",
        "waterfall-delivery",
        "project-phase-report",
        "doc",
        "slides",
        "spreadsheet",
    ),
    "Notification / Ops Expert": ("feishu-notify", "claude-to-im", "linear", "sentry", "project-phase-report"),
}


DOMAIN_ROLE_CAPABILITY_CATEGORY: dict[str, str] = {
    "Research Ideation Expert": "research",
    "Literature / Novelty Expert": "research",
    "Research Pipeline Expert": "research",
    "Theory Expert": "research",
    "Paper-to-Code Expert": "software",
    "Paper Writing Expert": "paper",
    "Paper Figures / Talks Expert": "paper",
    "Experiment / Metrics Expert": "experiment",
    "Algorithm Expert": "experiment",
    "ML Training Expert": "ml",
    "LLM Fine-Tuning Expert": "ml",
    "LLM Serving Expert": "ml",
    "Compression Expert": "ml",
    "Model Architecture Expert": "ml",
    "Interpretability Expert": "ml",
    "Evaluation / Benchmark Expert": "experiment",
    "RAG / Agents Expert": "data",
    "Retrieval / Vector DB Expert": "data",
    "Tokenizer / Data Expert": "data",
    "Multimodal / Vision Expert": "ml",
    "Robotics / Embodied Expert": "ml",
    "Audio / Speech Expert": "ml",
    "Safety / Guardrails Expert": "software",
    "Frontend / Design Expert": "software",
    "Backend / API Expert": "software",
    "Game / Desktop Expert": "software",
    "Security / Reliability Expert": "software",
    "CI / PR Expert": "software",
    "Deploy Expert": "ops",
    "Documents / Materials Expert": "data",
    "Knowledge / Notion Expert": "data",
    "Project Delivery Expert": "ops",
    "Notification / Ops Expert": "ops",
}


FALLBACK_ROLE = RoleDefinition(
    "General / Unclassified Skills Expert",
    "Routes installed skills that do not yet match a domain taxonomy rule and reports taxonomy gaps.",
    "unclassified_skill_routing",
    role_type="domain_specialist",
)

FALLBACK_CAPABILITY = CapabilityProfile(
    activation_criteria=(
        "Use when installed skills do not yet match the deterministic domain taxonomy.",
        "Use as a temporary routing bridge while recording taxonomy gaps for later generator refinement.",
    ),
    input_contract=(
        "Unclassified skill ids, descriptions, user request, and the nearest candidate expert roles.",
        "Reason the existing taxonomy did not match with enough confidence.",
    ),
    deliverables=(
        "A routing recommendation for the current run.",
        "A taxonomy gap note that can be converted into generator keywords or a new specialist role.",
    ),
    verification_focus=(
        "Unclassified skills are still installed and non-reserved.",
        "The temporary route does not silently bypass allowlists or reserved-skill policy.",
    ),
    risk_flags=(
        "Stable repeated routing through fallback instead of updating the taxonomy.",
        "Using fallback as a broad permission bucket.",
    ),
    collaboration=(
        "Reports stable gaps to Harness Architect and Entropy Gardener.",
        "Asks Professor Orchestrator before expanding any allowlist.",
    ),
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def skill_text(skill: dict[str, Any]) -> str:
    fields = [
        skill.get("id", ""),
        skill.get("name", ""),
        skill.get("description", ""),
        skill.get("relative_path", ""),
        skill.get("path", ""),
    ]
    aliases = skill.get("aliases", [])
    if isinstance(aliases, list):
        fields.extend(str(alias) for alias in aliases)
    return " ".join(str(field) for field in fields).lower()


def build_label_index(skills: list[dict[str, Any]]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for skill in skills:
        skill_id = skill.get("id")
        if not isinstance(skill_id, str) or not skill_id:
            continue
        for key in ["id", "name"]:
            value = skill.get(key)
            if isinstance(value, str) and value:
                labels[value] = skill_id
        aliases = skill.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias:
                    labels[alias] = skill_id
    return labels


def resolve_preferred_skills(preferred: tuple[str, ...], label_index: dict[str, str]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for label in preferred:
        skill_id = label_index.get(label)
        if skill_id and skill_id not in seen:
            resolved.append(skill_id)
            seen.add(skill_id)
    return resolved


def keyword_score(role: RoleDefinition, skill: dict[str, Any]) -> int:
    text = skill_text(skill)
    skill_id = str(skill.get("id", "")).lower()
    name = str(skill.get("name", "")).lower()
    aliases = {
        str(alias).lower()
        for alias in skill.get("aliases", [])
        if isinstance(alias, str) and alias
    }
    preferred = {
        label.lower()
        for label in DOMAIN_ROLE_PREFERRED_SKILLS.get(role.role, ())
    }
    score = 0
    if skill_id in preferred or name in preferred or aliases & preferred:
        score += 100
    for keyword in role.keywords:
        keyword_lower = keyword.lower()
        if keyword_lower == skill_id or keyword_lower == name:
            score += 6
        elif re.search(rf"(?<![a-z0-9]){re.escape(keyword_lower)}(?![a-z0-9])", text):
            score += 3
        elif keyword_lower in text:
            score += 1
    return score


def assign_domain_skills(skills: list[dict[str, Any]]) -> dict[str, list[str]]:
    assignments: dict[str, list[str]] = {role.role: [] for role in DOMAIN_ROLES}
    assignments[FALLBACK_ROLE.role] = []
    for skill in skills:
        if skill.get("category") != "external_domain_skill" or skill.get("reserved") is True:
            continue
        best_role: RoleDefinition | None = None
        best_score = 0
        for role in DOMAIN_ROLES:
            score = keyword_score(role, skill)
            if score > best_score:
                best_role = role
                best_score = score
        role_name = best_role.role if best_role and best_score > 0 else FALLBACK_ROLE.role
        assignments[role_name].append(str(skill["id"]))
    for role_name in assignments:
        assignments[role_name] = sorted(set(assignments[role_name]))
    return assignments


def profile_to_record(profile: CapabilityProfile) -> dict[str, list[str]]:
    return {
        "activation_criteria": list(profile.activation_criteria),
        "input_contract": list(profile.input_contract),
        "deliverables": list(profile.deliverables),
        "verification_focus": list(profile.verification_focus),
        "risk_flags": list(profile.risk_flags),
        "collaboration": list(profile.collaboration),
    }


def capability_profile_for_role(role: RoleDefinition) -> CapabilityProfile:
    if role.role in CORE_ROLE_CAPABILITIES:
        return CORE_ROLE_CAPABILITIES[role.role]
    if role.role == FALLBACK_ROLE.role:
        return FALLBACK_CAPABILITY
    category = DOMAIN_ROLE_CAPABILITY_CATEGORY.get(role.role, "software")
    return DOMAIN_CAPABILITY_HINTS[category]


def make_role_record(role: RoleDefinition, allowed_skills: list[str], generated_from: str) -> dict[str, Any]:
    capability_profile = capability_profile_for_role(role)
    return {
        "role": role.role,
        "type": role.role_type,
        "capability": role.capability,
        "capability_profile": profile_to_record(capability_profile),
        "allowed_skills": allowed_skills,
        "forbidden_skills": ["codex-autoresearch", "multi-agent", "expert-debate"],
        "required_skill_check": True,
        "output_schema": role.output_schema,
        "generated_from": generated_from,
        "selection_keywords": list(role.keywords),
    }


def build_expert_library(inventory: dict[str, Any]) -> dict[str, Any]:
    skills = inventory.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    label_index = build_label_index([skill for skill in skills if isinstance(skill, dict)])
    roles: list[dict[str, Any]] = []

    for role in CORE_ROLES:
        roles.append(
            make_role_record(
                role,
                resolve_preferred_skills(role.preferred_skills, label_index),
                "core_role_template",
            )
        )

    assignments = assign_domain_skills([skill for skill in skills if isinstance(skill, dict)])
    domain_by_name = {role.role: role for role in DOMAIN_ROLES}
    for role in DOMAIN_ROLES:
        allowed_skills = sorted(
            set(assignments.get(role.role, []))
            | set(resolve_preferred_skills(DOMAIN_ROLE_PREFERRED_SKILLS.get(role.role, ()), label_index))
        )
        if allowed_skills:
            roles.append(make_role_record(role, allowed_skills, "skill_inventory_taxonomy"))
    fallback_skills = assignments.get(FALLBACK_ROLE.role, [])
    if fallback_skills:
        roles.append(make_role_record(FALLBACK_ROLE, fallback_skills, "skill_inventory_fallback"))

    covered_skills = sorted(
        {
            skill
            for role in roles
            for skill in role.get("allowed_skills", [])
            if isinstance(skill, str)
        }
    )
    external_skills = sorted(
        str(skill["id"])
        for skill in skills
        if isinstance(skill, dict)
        and skill.get("category") == "external_domain_skill"
        and skill.get("reserved") is not True
        and skill.get("id")
    )
    reserved_skills = sorted(
        str(skill["id"])
        for skill in skills
        if isinstance(skill, dict)
        and (skill.get("reserved") is True or skill.get("category") == "reserved_orchestration_skill")
        and skill.get("id")
    )
    coverage_missing = sorted(set(external_skills) - set(covered_skills))

    return {
        "version": 4,
        "capability_schema_version": 1,
        "generated_by": "scripts/update_expert_library.py",
        "expert_library_version": EXPERT_LIBRARY_VERSION,
        "source_inventory_hash": inventory.get("inventory_hash"),
        "source_inventory_version": inventory.get("version"),
        "reserved_orchestration_skills": sorted(set(reserved_skills) | {"codex-autoresearch", "multi-agent", "expert-debate"}),
        "coverage": {
            "external_skill_count": len(external_skills),
            "covered_external_skill_count": len(set(external_skills) & set(covered_skills)),
            "fallback_skill_count": len(fallback_skills),
            "missing_external_skills": coverage_missing,
        },
        "roles": roles,
    }


def format_skill_list(skills: list[str]) -> str:
    if not skills:
        return "`none`"
    return ", ".join(f"`{skill}`" for skill in skills)


def format_profile_field(profile: dict[str, Any], field: str) -> str:
    values = profile.get(field, [])
    if not isinstance(values, list) or not values:
        return "`none`"
    return " | ".join(str(value) for value in values)


def render_markdown(library: dict[str, Any]) -> str:
    roles = library.get("roles", [])
    core_roles = [role for role in roles if role.get("type") == "core_council"]
    domain_roles = [role for role in roles if role.get("type") == "domain_specialist"]
    coverage = library.get("coverage", {})
    source_hash = library.get("source_inventory_hash") or "unknown"

    lines: list[str] = [
        "# Expert Capability Library",
        "",
        f"Version: `{library.get('expert_library_version')}`",
        f"Generated by: `{library.get('generated_by')}`",
        f"Source inventory hash: `{source_hash}`",
        "",
        "This file is generated from `references/skill-inventory.json`. To update it after skills change, run:",
        "",
        "```bash",
        "python scripts/update_skill_inventory.py",
        "python scripts/update_expert_library.py",
        "```",
        "",
        "The library has two layers:",
        "",
        "- `Harness Core Council`: stable experts that plan, orchestrate, debate, verify, route skills, and manage runs.",
        "- `Domain Specialists`: experts generated from the installed skill inventory and a deterministic taxonomy.",
        "",
        "Each role includes a machine-readable `capability_profile` with activation criteria, input contract, deliverables, verification focus, risk flags, and collaboration expectations. Use those fields when creating task cards or deciding whether to add, stop, or replace a specialist.",
        "",
        "Reserved orchestration skills (`codex-autoresearch`, `multi-agent`, `expert-debate`) are not automatically added to ordinary expert allowlists and remain explicit-request-only.",
        "",
        "## Coverage",
        "",
        f"- External skills covered: `{coverage.get('covered_external_skill_count', 0)}` / `{coverage.get('external_skill_count', 0)}`",
        f"- Fallback-routed skills: `{coverage.get('fallback_skill_count', 0)}`",
        "",
        "## Harness Core Council",
        "",
    ]

    for role in core_roles:
        profile = role.get("capability_profile", {})
        lines.extend(
            [
                f"### {role['role']}",
                f"Capability: {role['capability']}",
                f"Activation: {format_profile_field(profile, 'activation_criteria')}",
                f"Inputs: {format_profile_field(profile, 'input_contract')}",
                f"Deliverables: {format_profile_field(profile, 'deliverables')}",
                f"Verification focus: {format_profile_field(profile, 'verification_focus')}",
                f"Risk flags: {format_profile_field(profile, 'risk_flags')}",
                f"Collaboration: {format_profile_field(profile, 'collaboration')}",
                f"Allowed skills: {format_skill_list(role.get('allowed_skills', []))}",
                f"Output schema: `{role['output_schema']}`",
                "",
            ]
        )

    lines.extend(["## Domain Specialists", ""])
    for role in domain_roles:
        profile = role.get("capability_profile", {})
        lines.extend(
            [
                f"### {role['role']}",
                f"Capability: {role['capability']}",
                f"Activation: {format_profile_field(profile, 'activation_criteria')}",
                f"Inputs: {format_profile_field(profile, 'input_contract')}",
                f"Deliverables: {format_profile_field(profile, 'deliverables')}",
                f"Verification focus: {format_profile_field(profile, 'verification_focus')}",
                f"Risk flags: {format_profile_field(profile, 'risk_flags')}",
                f"Collaboration: {format_profile_field(profile, 'collaboration')}",
                f"Allowed skills: {format_skill_list(role.get('allowed_skills', []))}",
                f"Output schema: `{role['output_schema']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Selection Rules",
            "",
            "- Always start with the smallest complete Harness Core Council for the task.",
            "- Add Domain Specialists only after intent routing identifies the domain.",
            "- Use each role's `capability_profile.activation_criteria` before creating or replacing that specialist.",
            "- Copy each role's input contract, deliverables, verification focus, and risk flags into the task card when they are relevant.",
            "- Domain Specialists use their generated `allowed_skills` as hard boundaries.",
            "- If a needed skill is outside the allowlist, the subagent reports `needed_skill`; the orchestrator records the route decision before expanding the allowlist.",
            "- If a skill lands in `General / Unclassified Skills Expert`, treat it as a taxonomy gap and refine the generator when the routing becomes stable.",
            "- Reserved orchestration skills stay blocked unless the user explicitly asks for them.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate harness expert library from skill inventory")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    inventory = load_json(args.inventory)
    library = build_expert_library(inventory)
    args.json_output.write_text(json.dumps(library, indent=2, sort_keys=True) + "\n")
    args.md_output.write_text(render_markdown(library))
    print(
        "Wrote "
        f"{args.json_output} and {args.md_output} "
        f"with {len(library['roles'])} roles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

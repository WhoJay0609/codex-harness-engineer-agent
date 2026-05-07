#!/usr/bin/env python3
"""Generate the harness-engineer expert library from installed skills."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPERT_LIBRARY_VERSION = "harness-experts.v3"
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
        keywords=("notify", "notification", "feishu", "linear", "ops", "sentry"),
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
    "Notification / Ops Expert": ("feishu-notify", "linear", "sentry", "project-phase-report"),
}


FALLBACK_ROLE = RoleDefinition(
    "General / Unclassified Skills Expert",
    "Routes installed skills that do not yet match a domain taxonomy rule and reports taxonomy gaps.",
    "unclassified_skill_routing",
    role_type="domain_specialist",
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


def make_role_record(role: RoleDefinition, allowed_skills: list[str], generated_from: str) -> dict[str, Any]:
    return {
        "role": role.role,
        "type": role.role_type,
        "capability": role.capability,
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
        "version": 3,
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
        lines.extend(
            [
                f"### {role['role']}",
                f"Capability: {role['capability']}",
                f"Allowed skills: {format_skill_list(role.get('allowed_skills', []))}",
                f"Output schema: `{role['output_schema']}`",
                "",
            ]
        )

    lines.extend(["## Domain Specialists", ""])
    for role in domain_roles:
        lines.extend(
            [
                f"### {role['role']}",
                f"Capability: {role['capability']}",
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

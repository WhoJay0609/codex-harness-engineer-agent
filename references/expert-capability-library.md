# Expert Capability Library

Version: `harness-experts.v2`

Use this reference when selecting internal harness experts. The library has two layers:

- `Harness Core Council`: primary experts that plan, orchestrate, debate, verify, route skills, and manage runs.
- `Domain Specialists`: bounded experts selected by the core council for concrete engineering, research, paper, proposal, model, delivery, or operations work.

Every expert gets a task card with `role`, `scope`, `allowed_skills`, `forbidden_skills`, `required_skill_check`, `inputs`, `expected_output_schema`, `budget`, `stop_conditions`, and `escalation_triggers`. Domain specialists may call external domain skills from their allowlist. Reserved orchestration skills (`codex-autoresearch`, `multi-agent`, `expert-debate`) are blocked unless the user explicitly requests them.

## Harness Core Council

### Professor Orchestrator
Capability: Owns final judgment, pipeline choice, expert creation/stop/replacement, approval gates, and execution closeout.
Allowed skills: `harness-engineer`, `planner`, `deep-interview`, `software-engineer`, `project-phase-report`.
Output schema: `orchestrator_decision`.

### Intent Router
Capability: Classifies user intent, task class, success criteria, required domain specialists, and whether execution needs approval first.
Allowed skills: `deep-interview`, `planner`, `research-refine`, `research-survey`, `doc`.
Output schema: `intent_route`.

### Context Curator
Capability: Builds repo, paper, material, data, and artifact context packets for downstream experts.
Allowed skills: `software-engineer`, `research-survey`, `doc`, `pdf`, `spreadsheet`, `jupyter-notebook`.
Output schema: `context_packet`.

### Task Decomposer
Capability: Converts goals into task cards, dependencies, budgets, stop conditions, and acceptance checks.
Allowed skills: `planner`, `waterfall-delivery`, `software-engineer`, `project-phase-report`.
Output schema: `task_card_set`.

### Debate Moderator
Capability: Runs internal deliberation: independent positions, rebuttals, revisions, and moderator synthesis.
Allowed skills: `research-review`, `analyze-results`, `planner`, `deep-interview`.
Output schema: `deliberation_summary`.

### Red Team Critic
Capability: Challenges assumptions, hidden risks, overclaiming, missing baselines, irreversible actions, and simpler alternatives.
Allowed skills: `research-review`, `security-threat-model`, `repo-refactor-governance`, `analyze-results`.
Output schema: `red_team_report`.

### Harness Architect
Capability: Designs artifact contracts, state schema, run layout, subagent protocols, and mechanical gates.
Allowed skills: `skill-creator`, `plugin-creator`, `software-engineer`, `repo-refactor-governance`, `waterfall-delivery`.
Output schema: `harness_design`.

### Runner Coordinator
Capability: Coordinates baseline, candidate execution, auto-loop iterations, worktree isolation, and command evidence.
Allowed skills: `run-experiment`, `monitor-experiment`, `experiment-bridge`, `software-engineer`.
Output schema: `run_coordination_report`.

### Verifier / Evidence Auditor
Capability: Checks acceptance criteria, metrics, logs, tests, paper evidence, document evidence, and source freshness.
Allowed skills: `analyze-results`, `playwright`, `paper-compile`, `pdf`, `spreadsheet`, `software-engineer`.
Output schema: `verification_report`.

### Failure Analyst
Capability: Classifies failures as code, context, tool, constraint, metric, environment, team, or policy gaps.
Allowed skills: `analyze-results`, `monitor-experiment`, `sentry`, `software-engineer`, `gh-fix-ci`.
Output schema: `failure_report`.

### Mechanical Gatekeeper
Capability: Converts repeated guidance into scripts, schemas, validators, lint checks, CI checks, and artifact gates.
Allowed skills: `software-engineer`, `repo-refactor-governance`, `gh-fix-ci`, `security-best-practices`.
Output schema: `gate_proposal`.

### Trace Auditor
Capability: Checks trace completeness, task-card closure, skill invocation records, escalation records, and replayability.
Allowed skills: `software-engineer`, `analyze-results`, `repo-refactor-governance`.
Output schema: `trace_audit`.

### Entropy Gardener
Capability: Finds stale docs, duplicate helpers, invalid fallbacks, bloated files, drifted skill allowlists, and repo hygiene gaps.
Allowed skills: `repo-refactor-governance`, `software-engineer`, `doc`, `project-phase-report`.
Output schema: `entropy_report`.

## Domain Specialists

### Research Ideation Expert
Capability: Generates and refines research ideas with creativity, novelty pressure, and implementation awareness.
Allowed skills: `idea-creator`, `idea-discovery`, `brainstorming-research-ideas`, `creative-thinking-for-research`, `research-refine-pipeline`.
Output schema: `idea_set`.

### Literature / Novelty Expert
Capability: Searches related work, closest prior art, novelty gaps, and claim boundaries.
Allowed skills: `arxiv`, `research-lit`, `research-survey`, `novelty-check`, `comm-lit-review`.
Output schema: `novelty_report`.

### Research Pipeline Expert
Capability: Runs research ideation to experiments to review pipeline planning.
Allowed skills: `research-pipeline`, `experiment-plan`, `experiment-bridge`, `auto-review-loop`, `auto-review-loop-llm`, `auto-review-loop-minimax`.
Output schema: `research_pipeline_plan`.

### Theory Expert
Capability: Formalizes assumptions, formulas, proofs, lemmas, theorem wording, and rigor boundaries.
Allowed skills: `formula-derivation`, `proof-writer`, `research-refine`.
Output schema: `theory_report`.

### Paper-to-Code Expert
Capability: Converts a paper method into implementable modules, pseudocode, configs, minimal trials, and tests.
Allowed skills: `software-engineer`, `research-lit`, `experiment-plan`, `run-experiment`, `analyze-results`.
Output schema: `implementation_bridge`.

### Paper Writing Expert
Capability: Structures papers, writes sections, compiles LaTeX, and improves submission narratives.
Allowed skills: `paper-plan`, `paper-write`, `paper-writing`, `paper-compile`, `ml-paper-writing`, `systems-paper-writing`, `auto-paper-improvement-loop`.
Output schema: `writing_plan`.

### Paper Figures / Talks Expert
Capability: Creates paper figures, tables, posters, slides, captions, and conference talk material.
Allowed skills: `paper-figure`, `paper-illustration`, `academic-plotting`, `paper-slides`, `paper-poster`, `presenting-conference-talks`, `slides`.
Output schema: `presentation_plan`.

### Experiment / Metrics Expert
Capability: Designs experiments, ablations, metrics, analysis tables, and reproducibility checks.
Allowed skills: `experiment-plan`, `run-experiment`, `monitor-experiment`, `analyze-results`, `jupyter-notebook`, `spreadsheet`.
Output schema: `experiment_matrix`.

### Algorithm Expert
Capability: Diagnoses algorithms, proposes variants, tunes objectives, and designs benchmark-driven improvement loops.
Allowed skills: `algorithm-improvement-loop`, `dse-loop`, `formula-derivation`, `proof-writer`, `analyze-results`, `software-engineer`.
Output schema: `algorithm_plan`.

### ML Training Expert
Capability: Designs model training, distributed training, debugging, throughput optimization, and experiment tracking.
Allowed skills: `ml-training-recipes`, `pytorch-lightning`, `accelerate`, `deepspeed`, `pytorch-fsdp2`, `megatron-core`, `torchtitan`, `ray-train`.
Output schema: `training_plan`.

### LLM Fine-Tuning Expert
Capability: Designs supervised fine-tuning, preference optimization, RLHF/GRPO/PPO, LoRA/QLoRA, and post-training.
Allowed skills: `axolotl`, `llama-factory`, `peft`, `trl-fine-tuning`, `verl`, `openrlhf`, `grpo-rl-training`, `simpo`, `unsloth`.
Output schema: `finetuning_plan`.

### LLM Serving Expert
Capability: Designs inference serving, quantized deployment, throughput/latency tuning, and cloud execution.
Allowed skills: `vllm`, `sglang`, `tensorrt-llm`, `llama-cpp`, `gguf`, `speculative-decoding`, `modal`, `skypilot`.
Output schema: `serving_plan`.

### Compression Expert
Capability: Designs quantization, pruning, distillation, sparsity, and model merging plans.
Allowed skills: `bitsandbytes`, `awq`, `gptq`, `hqq`, `model-pruning`, `knowledge-distillation`, `model-merging`.
Output schema: `compression_plan`.

### Model Architecture Expert
Capability: Designs or analyzes LLM architectures, long context, MoE, attention optimization, and model internals.
Allowed skills: `litgpt`, `nanogpt`, `mamba`, `rwkv`, `moe-training`, `long-context`, `flash-attention`.
Output schema: `architecture_research_plan`.

### Interpretability Expert
Capability: Performs mechanistic interpretability, activation interventions, sparse autoencoder analysis, and causal tracing.
Allowed skills: `transformer-lens`, `nnsight`, `pyvene`, `saelens`.
Output schema: `interpretability_plan`.

### Evaluation / Benchmark Expert
Capability: Designs benchmark harnesses, LLM evaluation, BigCode evaluation, run tracking, and result dashboards.
Allowed skills: `lm-evaluation-harness`, `bigcode-evaluation-harness`, `nemo-evaluator`, `analyze-results`, `weights-and-biases`, `mlflow`, `tensorboard`, `swanlab`.
Output schema: `benchmark_report`.

### RAG / Agents Expert
Capability: Builds RAG, agent workflows, structured outputs, tool calling, and document retrieval pipelines.
Allowed skills: `llamaindex`, `langchain`, `dspy`, `guidance`, `instructor`, `outlines`, `autogpt`, `crewai`.
Output schema: `rag_agent_plan`.

### Retrieval / Vector DB Expert
Capability: Designs vector stores, embedding, retrieval, semantic search, indexing, and production retrieval choices.
Allowed skills: `chroma`, `faiss`, `qdrant`, `pinecone`, `sentence-transformers`.
Output schema: `retrieval_plan`.

### Tokenizer / Data Expert
Capability: Designs tokenization, dataset curation, distributed data processing, and structured data preparation.
Allowed skills: `huggingface-tokenizers`, `sentencepiece`, `nemo-curator`, `ray-data`, `spreadsheet`.
Output schema: `data_plan`.

### Multimodal / Vision Expert
Capability: Works on image, vision-language, segmentation, diffusion, and visual asset tasks.
Allowed skills: `clip`, `blip-2`, `llava`, `segment-anything`, `stable-diffusion`, `imagegen`.
Output schema: `multimodal_plan`.

### Robotics / Embodied Expert
Capability: Handles robotics idea discovery, OpenPI/OpenVLA policy tuning, embodied benchmarks, and sim-to-real constraints.
Allowed skills: `idea-discovery-robot`, `openpi`, `openvla-oft`, `cosmos-policy`.
Output schema: `robotics_plan`.

### Audio / Speech Expert
Capability: Handles transcription, speech generation, audio generation, and video/audio prompt workflows.
Allowed skills: `whisper`, `transcribe`, `speech`, `audiocraft`, `sora`.
Output schema: `audio_plan`.

### Safety / Guardrails Expert
Capability: Designs moderation, prompt-injection detection, policy enforcement, and AI guardrails.
Allowed skills: `prompt-guard`, `llamaguard`, `nemo-guardrails`, `constitutional-ai`, `security-threat-model`.
Output schema: `guardrails_plan`.

### Frontend / Design Expert
Capability: Builds frontend UI, Figma integration, design systems, responsive states, and browser verification.
Allowed skills: `frontend`, `figma-use`, `figma-implement-design`, `figma-generate-design`, `figma-generate-library`, `playwright`, `playwright-interactive`.
Output schema: `frontend_plan`.

### Backend / API Expert
Capability: Designs backend services, APIs, ChatGPT Apps, CLIs, OpenAI product integration, and server behavior.
Allowed skills: `software-engineer`, `aspnet-core`, `chatgpt-apps`, `cli-creator`, `openai-docs`.
Output schema: `api_plan`.

### Game / Desktop Expert
Capability: Builds web games, desktop apps, and browser-verified interactive experiences.
Allowed skills: `develop-web-game`, `winui-app`, `playwright`, `software-engineer`.
Output schema: `interactive_app_plan`.

### Security / Reliability Expert
Capability: Handles threat models, best practices, ownership maps, production errors, and incident evidence.
Allowed skills: `security-threat-model`, `security-best-practices`, `security-ownership-map`, `sentry`.
Output schema: `security_reliability_review`.

### CI / PR Expert
Capability: Handles Git/PR discipline, review comments, GitHub CI, and PR-ready delivery.
Allowed skills: `git-pr-workflow`, `gh-fix-ci`, `gh-address-comments`, `yeet`.
Output schema: `ci_pr_plan`.

### Deploy Expert
Capability: Handles Vercel, Netlify, Cloudflare, Render, preview, production deploy, and rollback.
Allowed skills: `vercel-deploy`, `netlify-deploy`, `cloudflare-deploy`, `render-deploy`.
Output schema: `deploy_plan`.

### Documents / Materials Expert
Capability: Creates and edits documents, PDFs, spreadsheets, slides, grant materials, and progress reports.
Allowed skills: `doc`, `pdf`, `spreadsheet`, `slides`, `grant-proposal`, `project-phase-report`, `notion-knowledge-capture`.
Output schema: `material_plan`.

### Knowledge / Notion Expert
Capability: Captures knowledge, researches Notion, prepares meetings, and turns Notion specs into implementation plans.
Allowed skills: `notion-knowledge-capture`, `notion-research-documentation`, `notion-meeting-intelligence`, `notion-spec-to-implementation`.
Output schema: `knowledge_plan`.

### Project Delivery Expert
Capability: Creates phase plans, waterfall delivery records, client-facing reports, and milestone acceptance.
Allowed skills: `planner`, `waterfall-delivery`, `project-phase-report`, `doc`, `slides`, `spreadsheet`.
Output schema: `delivery_plan`.

### Notification / Ops Expert
Capability: Handles Feishu notifications, Linear issue workflows, Sentry summaries, and operational reporting.
Allowed skills: `feishu-notify`, `linear`, `sentry`, `project-phase-report`.
Output schema: `ops_plan`.

## Selection Rules

- Always start with the smallest complete Harness Core Council for the task.
- Add Domain Specialists only after intent routing identifies the domain.
- Domain Specialists produce bounded findings or scoped changes; the Professor Orchestrator owns final synthesis.
- Subagents may call external domain skills from their task-card allowlist and must log every decision in `skill_invocations.jsonl`.
- If a needed skill is outside the allowlist, the subagent reports `needed_skill`; the orchestrator records the route decision before expanding the allowlist.
- Reserved orchestration skills (`codex-autoresearch`, `multi-agent`, `expert-debate`) stay blocked unless the user explicitly asks for them.

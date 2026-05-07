#!/usr/bin/env python3
"""Check consistency of a harness-engineer skill or harness directory."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_REFERENCES = [
    "framework.md",
    "harness-principles.md",
    "auto-harness-mode.md",
    "code-autoresearch-integration.md",
    "expert-capability-library.md",
    "expert-capability-library.json",
    "schemas/harness-event.schema.json",
    "skill-routing-policy.md",
    "skill-inventory.json",
    "team-formation-policy.md",
    "subagent-runtime.md",
    "skill-activation-policy.md",
    "decision-support-policy.md",
    "escalation-policy.md",
    "feedback-loop.md",
    "mechanical-gates.md",
    "entropy-garbage-collection.md",
]

EXPECTED_SCRIPTS = [
    "validate_harness_trace.py",
    "compare_runs.py",
    "summarize_failures.py",
    "check_harness_consistency.py",
    "export_trace_table.py",
    "query_harness_trace.py",
    "replay_harness_run.py",
    "run_harness_evals.py",
    "update_skill_inventory.py",
    "update_expert_library.py",
]

RESERVED_ORCHESTRATION_SKILLS = {"codex-autoresearch", "multi-agent", "expert-debate"}


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON at line {exc.lineno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"{path.name}: cannot read file: {exc}")
    return None


def installed_skill_labels(inventory: dict[str, Any]) -> set[str]:
    labels: set[str] = set()
    for key in ["core_harness_skills", "reserved_orchestration_skills"]:
        values = inventory.get(key)
        if isinstance(values, list):
            labels.update(str(value) for value in values if value)
    skills = inventory.get("skills")
    if isinstance(skills, list):
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            for key in ["id", "name"]:
                value = skill.get(key)
                if isinstance(value, str) and value:
                    labels.add(value)
            aliases = skill.get("aliases")
            if isinstance(aliases, list):
                labels.update(str(alias) for alias in aliases if alias)
    return labels


def check_inventory_freshness(root: Path, inventory: dict[str, Any], errors: list[str]) -> None:
    script_path = root / "scripts" / "update_skill_inventory.py"
    try:
        module = load_module(script_path, "harness_update_skill_inventory")
    except Exception as exc:  # pragma: no cover - surfaced as a consistency error.
        errors.append(f"scripts/update_skill_inventory.py: cannot load generator: {exc}")
        return

    roots = inventory.get("skills_roots")
    if not isinstance(roots, list) or not roots:
        errors.append("skill-inventory.json: skills_roots must be a non-empty list")
        return
    try:
        regenerated = module.build_inventory_data([Path(str(path)) for path in roots])
    except Exception as exc:  # pragma: no cover - surfaced as a consistency error.
        errors.append(f"skill-inventory.json: cannot regenerate inventory: {exc}")
        return
    if regenerated.get("inventory_hash") != inventory.get("inventory_hash"):
        errors.append("skill-inventory.json: installed skills changed; run scripts/update_skill_inventory.py")


def check_expert_library(root: Path, inventory: dict[str, Any], errors: list[str]) -> None:
    library_path = root / "references" / "expert-capability-library.json"
    library = load_json(library_path, errors)
    if not isinstance(library, dict):
        errors.append("expert-capability-library.json: must be a JSON object")
        return

    if library.get("source_inventory_hash") != inventory.get("inventory_hash"):
        errors.append("expert-capability-library.json: source inventory hash is stale; run scripts/update_expert_library.py")
    if library.get("expert_library_version") != "harness-experts.v3":
        errors.append("expert-capability-library.json: expert_library_version must be harness-experts.v3")

    labels = installed_skill_labels(inventory)
    reserved = set(RESERVED_ORCHESTRATION_SKILLS)
    reserved_values = inventory.get("reserved_orchestration_skills")
    if isinstance(reserved_values, list):
        reserved.update(str(value) for value in reserved_values if value)
    for skill in inventory.get("skills", []):
        if isinstance(skill, dict) and (skill.get("reserved") is True or skill.get("category") == "reserved_orchestration_skill"):
            for key in ["id", "name"]:
                value = skill.get(key)
                if isinstance(value, str) and value:
                    reserved.add(value)

    roles = library.get("roles")
    if not isinstance(roles, list) or not roles:
        errors.append("expert-capability-library.json: roles must be a non-empty list")
        return

    covered_external: set[str] = set()
    external_skills = {
        str(skill.get("id"))
        for skill in inventory.get("skills", [])
        if isinstance(skill, dict)
        and skill.get("id")
        and skill.get("category") == "external_domain_skill"
        and skill.get("reserved") is not True
    }
    for index, role in enumerate(roles, start=1):
        if not isinstance(role, dict):
            errors.append(f"expert-capability-library.json: roles[{index}] must be an object")
            continue
        if not role.get("role"):
            errors.append(f"expert-capability-library.json: roles[{index}] missing role")
        allowed_skills = role.get("allowed_skills")
        if not isinstance(allowed_skills, list):
            errors.append(f"expert-capability-library.json: role {role.get('role')} allowed_skills must be a list")
            continue
        for skill in allowed_skills:
            if not isinstance(skill, str) or not skill:
                errors.append(f"expert-capability-library.json: role {role.get('role')} has invalid skill label")
                continue
            if skill not in labels:
                errors.append(f"expert-capability-library.json: role {role.get('role')} references uninstalled skill {skill}")
            if skill in reserved:
                errors.append(f"expert-capability-library.json: role {role.get('role')} must not auto-allow reserved skill {skill}")
            if skill in external_skills:
                covered_external.add(skill)

    missing = sorted(external_skills - covered_external)
    if missing:
        sample = ", ".join(missing[:10])
        suffix = "" if len(missing) <= 10 else f", ... +{len(missing) - 10} more"
        errors.append(f"expert-capability-library.json: external skills missing expert coverage: {sample}{suffix}")

    md_path = root / "references" / "expert-capability-library.md"
    try:
        md_text = md_path.read_text()
    except OSError as exc:
        errors.append(f"expert-capability-library.md: cannot read file: {exc}")
        return
    source_hash = inventory.get("inventory_hash")
    if isinstance(source_hash, str) and source_hash not in md_text:
        errors.append("expert-capability-library.md: source inventory hash is stale; run scripts/update_expert_library.py")
    if "harness-experts.v3" not in md_text:
        errors.append("expert-capability-library.md: must mention harness-experts.v3")


def check_skill_dir(root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing SKILL.md")
        return errors

    content = skill_md.read_text()
    if "name: harness-engineer" not in content:
        errors.append("SKILL.md frontmatter must name harness-engineer")

    for ref in EXPECTED_REFERENCES:
        path = root / "references" / ref
        if not path.exists():
            errors.append(f"missing references/{ref}")
        if f"references/{ref}" not in content:
            errors.append(f"SKILL.md does not link references/{ref}")

    for script in EXPECTED_SCRIPTS:
        path = root / "scripts" / script
        if not path.exists():
            errors.append(f"missing scripts/{script}")
        else:
            text = path.read_text()
            if not text.startswith("#!/usr/bin/env python3"):
                errors.append(f"scripts/{script} missing python shebang")

    openai_yaml = root / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append("missing agents/openai.yaml")
    else:
        yaml_text = openai_yaml.read_text()
        if "$harness-engineer" not in yaml_text:
            errors.append("agents/openai.yaml default prompt must mention $harness-engineer")
        match = re.search(r'short_description:\s*"([^"]+)"', yaml_text)
        if not match:
            errors.append("agents/openai.yaml missing quoted short_description")
        elif not (25 <= len(match.group(1)) <= 64):
            errors.append("agents/openai.yaml short_description should be 25-64 characters")

    inventory_path = root / "references" / "skill-inventory.json"
    inventory = load_json(inventory_path, errors)
    if isinstance(inventory, dict):
        if inventory.get("version") != 2:
            errors.append("skill-inventory.json: version must be 2")
        if not inventory.get("inventory_hash"):
            errors.append("skill-inventory.json: missing inventory_hash")
        check_inventory_freshness(root, inventory, errors)
        check_expert_library(root, inventory, errors)

    evals_root = root / "evals" / "cases"
    if not evals_root.exists():
        errors.append("missing evals/cases")
    else:
        eval_cases = [path for path in evals_root.iterdir() if path.is_dir()]
        if not eval_cases:
            errors.append("evals/cases must include at least one eval case")
        for case in eval_cases:
            if not (case / "expected.json").exists():
                errors.append(f"eval case {case.name} missing expected.json")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check harness-engineer skill consistency")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    errors = check_skill_dir(args.path)
    if errors:
        print("FAIL: harness consistency check failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: harness consistency checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

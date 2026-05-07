#!/usr/bin/env python3
"""Generate the harness-engineer installed skill inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


RESERVED_ORCHESTRATION_SKILLS = {"codex-autoresearch", "multi-agent", "expert-debate"}
CORE_HARNESS_SKILLS = {"harness-engineer"}
SKIP_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            value = match.group(2).strip().strip('"').strip("'")
            meta[match.group(1)] = value
    return meta


def normalize_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def skill_category(labels: set[str]) -> str:
    if labels & RESERVED_ORCHESTRATION_SKILLS:
        return "reserved_orchestration_skill"
    if labels & CORE_HARNESS_SKILLS:
        return "core_harness_skill"
    return "external_domain_skill"


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def build_record(path: Path, skills_root: Path) -> dict[str, Any]:
    meta = parse_frontmatter(path / "SKILL.md")
    skill_id = path.name
    name = normalize_label(meta.get("name")) or skill_id
    description = normalize_label(meta.get("description")) or ""
    aliases = sorted({label for label in [skill_id, name] if label})
    labels = set(aliases)
    category = skill_category(labels)
    resolved_path = path.resolve()

    return {
        "id": skill_id,
        "name": name,
        "description": description,
        "aliases": aliases,
        "category": category,
        "reserved": category == "reserved_orchestration_skill",
        "path": str(path),
        "resolved_path": str(resolved_path),
        "source_root": str(skills_root),
        "relative_path": relative_to_root(path, skills_root),
        "status": "installed",
    }


def discover(skills_roots: list[Path]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for skills_root in skills_roots:
        if not skills_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(skills_root, followlinks=True):
            dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIR_NAMES)
            path = Path(dirpath)
            if "SKILL.md" not in filenames:
                continue
            if path.name in SKIP_DIR_NAMES:
                dirnames[:] = []
                continue
            record = build_record(path, skills_root)
            skill_id = record["id"]
            if skill_id in records:
                records[skill_id].setdefault("duplicate_paths", []).append(str(path))
                dirnames[:] = []
                continue
            records[skill_id] = record
            dirnames[:] = []
    return [records[key] for key in sorted(records)]


def stable_hash(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_inventory_data(skills_roots: list[Path]) -> dict[str, Any]:
    normalized_roots = [Path(root).expanduser() for root in skills_roots]
    data: dict[str, Any] = {
        "version": 2,
        "generated_by": "scripts/update_skill_inventory.py",
        "skills_roots": [str(root) for root in normalized_roots],
        "core_harness_skills": sorted(CORE_HARNESS_SKILLS),
        "reserved_orchestration_skills": sorted(RESERVED_ORCHESTRATION_SKILLS),
        "skills": discover(normalized_roots),
    }
    if len(normalized_roots) == 1:
        data["skills_root"] = str(normalized_roots[0])
    data["inventory_hash"] = stable_hash(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate harness-engineer skill inventory")
    parser.add_argument("paths", nargs="*", help="Skill roots followed by optional output path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path")
    args = parser.parse_args()

    default_roots = [Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"]
    default_output = Path(__file__).resolve().parents[1] / "references" / "skill-inventory.json"

    if args.output:
        skills_roots = [Path(path) for path in args.paths] or default_roots
        output_path = args.output
    elif len(args.paths) >= 2:
        skills_roots = [Path(path) for path in args.paths[:-1]]
        output_path = Path(args.paths[-1])
    elif len(args.paths) == 1:
        skills_roots = [Path(args.paths[0])]
        output_path = default_output
    else:
        skills_roots = default_roots
        output_path = default_output

    data = build_inventory_data(skills_roots)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {output_path} with {len(data['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

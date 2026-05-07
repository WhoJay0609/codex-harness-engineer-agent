#!/usr/bin/env python3
"""Generate the harness-engineer installed skill inventory."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


RESERVED_ORCHESTRATION_SKILLS = {"codex-autoresearch", "multi-agent", "expert-debate"}
CORE_HARNESS_SKILLS = {"harness-engineer"}


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


def skill_category(skill_id: str) -> str:
    if skill_id in RESERVED_ORCHESTRATION_SKILLS:
        return "reserved_orchestration_skill"
    if skill_id in CORE_HARNESS_SKILLS:
        return "core_harness_skill"
    return "external_domain_skill"


def discover(skills_roots: list[Path]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for skills_root in skills_roots:
        if not skills_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(skills_root, followlinks=True):
            path = Path(dirpath)
            if "SKILL.md" not in filenames:
                continue
            if path.name == ".system":
                continue
            skill_id = path.name
            if skill_id in records:
                dirnames[:] = []
                continue
            meta = parse_frontmatter(path / "SKILL.md")
            records[skill_id] = {
                "id": skill_id,
                "name": meta.get("name", skill_id),
                "category": skill_category(skill_id),
                "reserved": skill_id in RESERVED_ORCHESTRATION_SKILLS,
                "path": str(path),
            }
            dirnames[:] = []
    return [records[key] for key in sorted(records)]


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

    data = {
        "version": 1,
        "generated_by": "scripts/update_skill_inventory.py",
        "skills_roots": [str(root) for root in skills_roots],
        "core_harness_skills": sorted(CORE_HARNESS_SKILLS),
        "reserved_orchestration_skills": sorted(RESERVED_ORCHESTRATION_SKILLS),
        "skills": discover(skills_roots),
    }
    if len(skills_roots) == 1:
        data["skills_root"] = str(skills_roots[0])
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {output_path} with {len(data['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

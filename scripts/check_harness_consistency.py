#!/usr/bin/env python3
"""Check consistency of a harness-engineer skill or harness directory."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXPECTED_REFERENCES = [
    "harness-principles.md",
    "auto-harness-mode.md",
    "expert-capability-library.md",
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
    "update_skill_inventory.py",
]


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

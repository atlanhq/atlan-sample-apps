#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILLS = [
    "atlan-fact-verification-gate",
    "atlan-cli-install-configure",
    "atlan-app-scaffold-standard",
    "atlan-sdk-objectstore-io-defaults",
    "atlan-workflow-args-secrets-state",
    "atlan-sql-connector-patterns",
    "atlan-cli-run-test-loop",
    "atlan-e2e-contract-validator",
    "atlan-review-doc-sync",
]


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: verify_skill_pack.py <skills-root>")

    root = Path(sys.argv[1])
    if not root.exists():
        return fail(f"root not found: {root}")

    # Ensure no machine-local hardcoded paths in skill docs/templates
    home_path_pattern = re.compile(r"/" + "Users" + r"/|/" + "home" + r"/")
    windows_path_pattern = re.compile(r"[A-Za-z]:\\")
    for file in root.rglob("*"):
        if file.is_file() and file.suffix in {".md", ".py", ".json", ".yaml", ".yml"}:
            text = file.read_text(encoding="utf-8")
            if home_path_pattern.search(text) or windows_path_pattern.search(text):
                return fail(f"found machine-local path in {file}")

    for skill in SKILLS:
        skill_dir = root / skill
        if not skill_dir.exists():
            return fail(f"missing skill directory: {skill_dir}")

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return fail(f"missing SKILL.md: {skill_md}")

        eval_file = skill_dir / "evals" / "prompts.md"
        if not eval_file.exists():
            return fail(f"missing eval prompts: {eval_file}")

        text = skill_md.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            return fail(f"invalid frontmatter wrapper in {skill_md}")
        if "name:" not in parts[1]:
            return fail(f"missing name frontmatter in {skill_md}")
        if "description:" not in parts[1]:
            return fail(f"missing description frontmatter in {skill_md}")

        n_cases = len(
            re.findall(
                r"^\d+\. ", eval_file.read_text(encoding="utf-8"), flags=re.MULTILINE
            )
        )
        if n_cases < 5:
            return fail(f"expected >=5 eval cases in {eval_file}, found {n_cases}")

    required_shared = [
        root / "_shared" / "references" / "verification-sources.md",
        root / "_shared" / "references" / "cli-change-proposals.md",
        root / "_shared" / "scripts" / "sync_claude_skills.py",
    ]
    for file in required_shared:
        if not file.exists():
            return fail(f"missing shared file: {file}")

    print("PASS: skill pack structure looks valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

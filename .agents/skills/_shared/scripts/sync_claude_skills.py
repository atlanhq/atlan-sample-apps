#!/usr/bin/env python3
"""Sync .agents/skills to .claude/skills for Claude Code compatibility."""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    codex_root = repo_root / ".agents" / "skills"
    claude_root = repo_root / ".claude" / "skills"

    if not codex_root.exists():
        print(f"FAIL: missing source skills root: {codex_root}")
        return 1

    if claude_root.exists():
        shutil.rmtree(claude_root)
    claude_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(codex_root, claude_root)

    print(f"SYNCED: {codex_root} -> {claude_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

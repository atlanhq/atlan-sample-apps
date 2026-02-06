# CLAUDE.md

This file mirrors the root `AGENTS.md` guidance for Claude Code.

This repository contains self-contained Atlan sample apps (quickstart, connectors, utilities) built on the Atlan Application SDK.

## Essentials
- Package manager: `uv` (run commands from the target app directory, not repo root).
- Standard app loop: `uv sync` -> `uv run poe start-deps` -> `uv run main.py` -> `uv run pytest`.
- Pre-commit: `uv run pre-commit run --files <file>` (or `--all-files`).

## Skills First
- Claude Code skill root: `.claude/skills`
- Codex skill root: `.agents/skills`
- Keep both in sync after skill updates:
  - `python .agents/skills/_shared/scripts/sync_claude_skills.py`

Use skills before ad-hoc instructions. Recommended default flow:
1. `atlan-app-scaffold-standard`
2. `atlan-sql-connector-patterns`
3. `atlan-workflow-args-secrets-state`
4. `atlan-sdk-objectstore-io-defaults`
5. `atlan-e2e-contract-validator`
6. `atlan-cli-run-test-loop`
7. `atlan-review-doc-sync`

## Source Verification (Progressive Disclosure)
Start with task defaults in each skill. When behavior is unclear or high-risk:
- discover and fetch only the minimum needed context from sibling repos
- if those repos are unavailable, ask the user for path/context

## Constraints
- Treat SDK and CLI repos as read-only references.
- Log CLI improvement requests in:
  - `.claude/skills/_shared/references/cli-change-proposals.md`
- Never hardcode machine-local absolute paths.

## More Context (Load Only If Needed)
- `.claude/skills/_shared/references/agent-surface-compatibility.md`
- `.claude/skills/_shared/references/verification-sources.md`

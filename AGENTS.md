# AGENTS.md

This repository contains Atlan sample apps built on the Atlan Application SDK.

## Essentials
- Package manager: `uv` (run commands from target app directory).
- Standard fallback loop: `uv sync` -> `uv run poe start-deps` -> `uv run main.py` -> `uv run pytest`.
- Pre-commit: `uv run pre-commit run --files <file>` (or `--all-files`).

## Developer-First Behavior
Treat normal developer prompts as business intent, not command instructions.
- If user asks to create a new app, automatically scaffold with Atlan CLI first.
- Check CLI availability (`atlan`) and handle install/setup when missing.
- Only use manual scaffolding when CLI path is unavailable and explicitly justified.

## Skills First
- Codex skill root: `.agents/skills`
- Claude Code skill root: `.claude/skills`
- Sync after updates:
  - `python .agents/skills/_shared/scripts/sync_claude_skills.py`

Recommended flow:
1. `atlan-cli-install-configure` (only when `atlan` is missing or reinstall is requested)
2. `atlan-app-scaffold-standard`
3. `atlan-fact-verification-gate`
4. `atlan-sql-connector-patterns`
5. `atlan-workflow-args-secrets-state`
6. `atlan-sdk-objectstore-io-defaults`
7. `atlan-e2e-contract-validator`
8. `atlan-cli-run-test-loop`
9. `atlan-review-doc-sync`

## Constraints
- SDK and CLI repos are read-only references.
- Log CLI improvement requests in `.agents/skills/_shared/references/cli-change-proposals.md`.
- Never hardcode machine-local absolute paths.

# CLAUDE.md

This file mirrors root `AGENTS.md` guidance for Claude Code.

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
- Claude Code skill root: `.claude/skills`
- Codex skill root: `.agents/skills`
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
- Log CLI improvement requests in `.claude/skills/_shared/references/cli-change-proposals.md`.
- Never hardcode machine-local absolute paths.

## Security

> Follow these security guidelines for every change to the sample apps.

### Contact

- **Security Team:** #bu-security-and-it on Slack

### Quickstart for Agents

This repo contains sample connectors and quickstart apps demonstrating the Application SDK. Samples use `ATLAN_BASE_URL` and `ATLAN_API_KEY` from environment. Review every change for:

- **API key in sample code** — sample apps must never hardcode `ATLAN_API_KEY` values; always read from environment; sample README files must not include real API keys.
- **Sample credentials** — any credentials shown in templates or documentation must be clearly marked as placeholders (e.g., `<YOUR_API_KEY>`); real secrets must not be committed.

### Security Invariants

- **[MUST]** `ATLAN_API_KEY` must never be hardcoded in sample code or README files.
- **[MUST]** Sample templates must use placeholder values, not real credentials.

### Review Checklist

- [ ] No hardcoded `ATLAN_API_KEY` or real credentials in sample code or templates
- [ ] README and docs use placeholder values (`<YOUR_API_KEY>`)
- [ ] Sample apps read credentials from environment variables only
- [ ] All direct dependencies in `pyproject.toml` pinned exactly

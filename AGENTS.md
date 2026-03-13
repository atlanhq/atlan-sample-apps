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

## Security

> Follow these security guidelines for every change to the sample apps.

### Contact

- **Security Team:** #bu-security-and-it on Slack

### Quickstart for Agents

atlan-sample-apps contains example connectors (`connectors/`), quickstart applications (`quickstart/`), and templates (`templates/`) demonstrating how to build on the Application SDK. Samples run against a live Atlan tenant using `ATLAN_BASE_URL` and `ATLAN_API_KEY` from environment. A `registry.json` catalogs available samples. Review every change for:

- **Hardcoded credentials in samples** — sample code, templates, and scripts must read `ATLAN_BASE_URL` and `ATLAN_API_KEY` from environment variables (`os.environ.get()`), never hardcode them; `registry.json`, connector templates, and any quickstart YAML/config files must use environment variable references or explicit `<PLACEHOLDER>` values, not real credentials.
- **README/documentation credentials** — README files and docs must use placeholder values (e.g., `<YOUR_API_KEY>`, `<YOUR_TENANT_URL>`) for any credential fields shown in commands or config examples; real credentials committed to documentation become permanently visible in git history.
- **Sample data sensitivity** — any sample data files (CSV, JSON, YAML) bundled for demonstration must not contain real customer data, PII, or real asset metadata from production Atlan tenants; use synthetic or anonymized data only.
- **Dependency pinning in samples** — `pyproject.toml` in each sample/connector must use exact dependency pins; samples are often copied as starting points and unpinned versions propagate supply-chain risk.

### Security Invariants

- **[MUST]** `ATLAN_API_KEY` and `ATLAN_BASE_URL` must never be hardcoded — always from environment variables.
- **[MUST]** README and template credential fields must use `<PLACEHOLDER>` values.
- **[MUST]** Sample data files must not contain real customer data or PII.
- **[MUST]** All direct dependency versions in `pyproject.toml` pinned exactly.

### Data Classification

- **CONFIDENTIAL:** `ATLAN_API_KEY` (must never appear in code or docs)
- **INTERNAL:** `ATLAN_BASE_URL`, tenant-specific configurations
- **PUBLIC:** Connector template structure, SDK usage patterns, sample data schemas

### Review Checklist

- [ ] No hardcoded `ATLAN_API_KEY` in any sample code, template, or config file
- [ ] README examples use `<YOUR_API_KEY>` and `<YOUR_TENANT_URL>` placeholders
- [ ] `registry.json` and connector manifests use environment variable references only
- [ ] Sample data files contain only synthetic or anonymized data
- [ ] All `pyproject.toml` dependencies use exact version pins

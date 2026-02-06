# CLI Change Proposals

Record CLI issues here for maintainer discussion. Do not edit the CLI repository from this skill pack.

## Entry Format
- `date`:
- `workflow_step`:
- `current_cli_behavior`:
- `expected_cli_behavior`:
- `why_it_matters`:
- `source_evidence`:
  - file paths, commands, or docs references used during investigation
- `suggested_fix`:
- `priority`:

---

## Proposal 2026-02-06-01
- `date`: 2026-02-06
- `workflow_step`: CLI command discovery for app lifecycle
- `current_cli_behavior`: The root `atlan app` command is hidden in code, which makes command discovery inconsistent for agents relying on docs first.
- `expected_cli_behavior`: Either unhide the command for discoverability or clearly annotate in docs that this command may be hidden and provide the supported fallback workflow.
- `why_it_matters`: Build/test loops can fail early when agents select a documented command path that is not discoverable in current binaries.
- `source_evidence`:
  - atlan-cli/cmd/atlan/app.go
  - atlan-cli/docs/app-command.md
  - application-sdk/docs/guides/sql-application-guide.md
- `suggested_fix`: Align command visibility and docs, or add an explicit fallback section in CLI docs with `uv`-based alternatives.
- `priority`: P2

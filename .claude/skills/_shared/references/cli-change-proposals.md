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

---

## Proposal 2026-02-06-02
- `date`: 2026-02-06
- `workflow_step`: Dependency startup for `atlan app run` and `atlan app test -t e2e`
- `current_cli_behavior`: `app init tools` treats Dapr as initialized when `~/.dapr/bin/daprd` exists, without verifying runtime config state (for example `~/.dapr/config.yaml`). This can leave environments where `start-deps` fails with Dapr config/runtime errors.
- `expected_cli_behavior`: Dapr initialization check should validate runtime readiness, not just binary presence, and auto-recover when runtime config is missing.
- `why_it_matters`: Agents and developers hit startup failures (`ATLAN-CLI-APP-0012`) even after following CLI setup flow, causing false negatives in run/e2e loops.
- `source_evidence`:
  - atlan-cli/pkg/atlan/app_init_tools.go
  - atlan-cli/pkg/atlan/app_run.go
  - atlan-cli/pkg/atlan/app_testing.go
  - atlan-sample-apps/utilities/demo-file-summary/pyproject.toml
- `suggested_fix`: In `initDapr`, verify runtime readiness (`~/.dapr/config.yaml` and/or `dapr --version` + health precheck) and rerun `dapr init --slim` when missing/incomplete.
- `priority`: P1

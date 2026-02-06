# Scaffold Matrix

## Default Bootstrap Contract
For every new app request, scaffold through CLI first.

1. Check CLI availability: `command -v atlan`
2. If missing, install CLI before scaffold:
   - preferred: fetch and run released install flow from `https://developer.atlan.com/sdks/cli/#obtain-the-cli`
   - fallback: `go install github.com/atlanhq/atlan-cli@latest`
   - source fallback: `git clone https://github.com/atlanhq/atlan-cli.git` then `make build && make install`
   - never use `go get` for CLI installation
   - do not begin by searching for local `atlan-cli` clones
   - verify: `command -v atlan && atlan --help`
3. Discover options when needed:
   - `atlan app template list`
   - `atlan app sample list`
4. Scaffold:
   - template path: `atlan app init -o <app_path> -t generic -y`
   - sample path: `atlan app init -o <app_path> -s <sample> -y`

If `atlan` is missing:
- If installation is blocked (network/policy), stop and ask the user to enable installation or provide an existing CLI binary path.
- Report this as an environment-preparation blocker and keep install guidance in the summary.

## Prohibited Path
- Do not hand-create the baseline app tree (`mkdir` + manual file bootstrapping).
- Do not copy an existing quickstart app as scaffold replacement.

## Exit Contract
- After scaffold + implementation, run `atlan-cli-run-test-loop`.
- Do not mark the app complete without unit + e2e run evidence, unless blocked by infra; if blocked, record the blocker and workaround.

## Quality Tier Contract
Choose and apply one tier before implementation:

1. `quickstart-utility` (default)
   - Keep scaffold simple.
   - Workflow should orchestrate at least one dedicated business activity in addition to args retrieval.
   - Avoid putting business file-write side effects entirely inside `get_workflow_args`.
   - Minimum tests: two unit cases (happy + invalid input) and one e2e output assertion.

2. `connector-standard`
   - Use connector-oriented structure and coverage aligned with postgres/redshift patterns.
   - Include appropriate client/handler/workflow/activity split and stronger e2e scenarios.

## postgres-minimal
Use when source is standard SQL and no source-specific workflow overrides are required.

Required files:
- `main.py`
- `app/clients/__init__.py`
- `app/sql/*.sql`
- `tests/e2e/<workflow>/config.yaml`
- `tests/e2e/<workflow>/test_*.py`

## redshift-custom
Use when auth modes, preflight checks, or query extraction require source-specific overrides.

Required additions:
- `app/handlers/*.py`
- `app/workflows/metadata_extraction/*.py`
- `app/workflows/query_extraction/*.py`
- `app/activities/metadata_extraction/*.py`
- `app/activities/query_extraction/*.py`
- `app/templates/*.json`

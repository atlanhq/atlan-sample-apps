# Scaffold Matrix

## Default Bootstrap Contract
For every new app request, scaffold through CLI first.

1. Check CLI availability: `command -v atlan`
2. Discover options when needed:
   - `atlan app template list`
   - `atlan app sample list`
3. Scaffold:
   - template path: `atlan app init -o <app_path> -t generic -y`
   - sample path: `atlan app init -o <app_path> -s <sample> -y`

If `atlan` is missing:
- Ask permission to install CLI using official docs.
- If installation is deferred and sibling `atlan-cli` repo exists, use temporary shim from that repo: `go run main.go app ...`.

## Prohibited Path
- Do not hand-create the baseline app tree (`mkdir` + manual file bootstrapping).
- Do not copy an existing quickstart app as scaffold replacement.

## Exit Contract
- After scaffold + implementation, run `atlan-cli-run-test-loop`.
- Do not mark the app complete without unit + e2e run evidence, unless blocked by infra; if blocked, record the blocker and workaround.

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

# Scaffold Matrix

## Source discovery
When patterns are unclear, inspect existing connector apps in the workspace:
- postgres-like minimal implementations
- redshift-like custom implementations

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

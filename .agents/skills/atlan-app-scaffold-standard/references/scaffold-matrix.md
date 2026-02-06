# Scaffold Matrix

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## postgres-minimal
Use when source is standard SQL and no source-specific workflow overrides are required.

Required files:
- `main.py`
- `app/clients/__init__.py`
- `app/sql/*.sql`
- `tests/e2e/<workflow>/config.yaml`
- `tests/e2e/<workflow>/test_*.py`

Pattern refs:
- `repo://atlan-postgres-app/main.py`
- `repo://atlan-postgres-app/app/clients/__init__.py`

## redshift-custom
Use when auth modes, preflight checks, or query extraction require source-specific overrides.

Required additions:
- `app/handlers/*.py`
- `app/workflows/metadata_extraction/*.py`
- `app/workflows/query_extraction/*.py`
- `app/activities/metadata_extraction/*.py`
- `app/activities/query_extraction/*.py`
- `app/templates/*.json`

Pattern refs:
- `repo://atlan-redshift-app/main.py`
- `repo://atlan-redshift-app/app/handlers/redshift.py`

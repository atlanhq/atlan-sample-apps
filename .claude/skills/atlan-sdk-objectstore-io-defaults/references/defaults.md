# Objectstore Defaults

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## Evidence Sources
- `repo://application-sdk/application_sdk/services/objectstore.py`
- `repo://application-sdk/application_sdk/io/json.py`
- `repo://application-sdk/application_sdk/io/parquet.py`
- `repo://application-sdk/docs/concepts/output_paths.md`

## Required Conventions
1. Keep base path under `artifacts/apps/<application_name>/workflows/<workflow_id>/<run_id>`.
2. Write source extracts under `raw` and transformed entities under `transformed`.
3. Keep naming stable with e2e schema validation paths.

## Anti-Patterns
- Hardcoding `/tmp` as final output destination.
- Mixing app name and connection name in base output prefix.
- Writing transformed outputs without raw counterparts when workflow expects both.

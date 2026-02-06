# Contract Checklist

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## Required API checks
- `auth.success == true`
- `metadata.success == true`
- `preflight_check.success == true` when preflight is relevant

## Required output checks
- Base prefix follows SDK output path pattern
- Raw outputs present for expected entities
- Transformed outputs present for expected entities

## Evidence Sources
- `repo://application-sdk/application_sdk/server/fastapi/models.py`
- `repo://application-sdk/docs/concepts/output_paths.md`
- `repo://atlan-postgres-app/tests/e2e/test_postgres_workflow/config.yaml`
- `repo://atlan-redshift-app/tests/e2e/test_redshift_workflow_mixed_filters/config.yaml`

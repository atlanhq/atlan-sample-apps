# Decision Tree

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## Choose postgres-minimal if all are true
- Basic auth flow is enough.
- No custom handler logic is required.
- Metadata extraction can run using base SQL workflow.
- Query extraction customization is not required.

Pattern refs:
- `repo://atlan-postgres-app/main.py`
- `repo://atlan-postgres-app/app/clients/__init__.py`

## Choose redshift-custom if any are true
- Multiple auth modes required (basic, IAM user, IAM role).
- Miner preflight checks or query history extraction required.
- Source-specific workflow and activity map required.
- Source-specific config maps/templates required.

Pattern refs:
- `repo://atlan-redshift-app/main.py`
- `repo://atlan-redshift-app/app/clients.py`
- `repo://atlan-redshift-app/app/handlers/redshift.py`

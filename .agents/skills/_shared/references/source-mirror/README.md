# Source Mirror

This folder contains copied reference files from sibling repositories:
- `application-sdk`
- `atlan-cli`
- `atlan-postgres-app`
- `atlan-redshift-app`

Purpose:
1. Keep skill behavior portable across machines.
2. Provide fallback sources when sibling repos are not present.
3. Keep verification reproducible in offline or partial workspace setups.

Refresh mirrors:
`python ../../scripts/sync_source_mirrors.py`

Resolve sources (live first, then mirror fallback):
`python ../../scripts/resolve_source.py --source repo://application-sdk/application_sdk/clients/temporal.py`

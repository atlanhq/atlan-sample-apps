# State and Secret Flow

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## Evidence Sources
- `repo://application-sdk/application_sdk/clients/temporal.py`
- `repo://application-sdk/application_sdk/activities/common/utils.py`
- `repo://application-sdk/application_sdk/services/secretstore.py`
- `repo://application-sdk/application_sdk/services/statestore.py`

## Required Flow
1. Start workflow with non-secret workflow args + credential reference.
2. Fetch credentials via SecretStore using `credential_guid`.
3. Compute output paths from workflow context.
4. Save updated workflow state via StateStore when needed.

## Reference Pattern
- Redshift miner flow persists workflow state via activity before child workflow trigger.
  - `repo://atlan-redshift-app/app/activities/metadata_extraction/redshift.py`
  - `repo://atlan-redshift-app/app/workflows/metadata_extraction/redshift.py`

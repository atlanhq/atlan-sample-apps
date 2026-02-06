# State and Secret Flow

## Evidence approach
When needed, inspect SDK workflow client, state store, and secret store implementations.
If local SDK checkout is unavailable, inspect installed package source or remote SDK source/docs.

## Required Flow
1. Start workflow with non-secret workflow args + credential reference.
2. Fetch credentials via SecretStore using `credential_guid`.
3. Retrieve/normalize workflow args first; keep business transformations in separate activities.
4. Compute output paths from workflow context.
5. Save updated workflow state via StateStore when needed.

## Reference pattern
If implementing child-workflow or miner patterns, inspect existing redshift workflow/activity behavior before changing runtime flow.

# Decision Tree

## Choose postgres-minimal if all are true
- Basic auth flow is enough.
- No custom handler logic is required.
- Metadata extraction can run using base SQL workflow.
- Query extraction customization is not required.

## Choose redshift-custom if any are true
- Multiple auth modes required (basic, IAM user, IAM role).
- Miner preflight checks or query history extraction required.
- Source-specific workflow and activity map required.
- Source-specific config maps/templates required.

## Verification approach
If uncertain, inspect existing postgres and redshift app implementations in sibling repos and follow the closest validated pattern.

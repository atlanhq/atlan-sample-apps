# Contract Checklist

## Required API checks
- `auth.success == true`
- `metadata.success == true`
- `preflight_check.success == true` when preflight is relevant

## Required output checks
- Base prefix follows SDK output path pattern
- Raw outputs present for expected entities
- Transformed outputs present for expected entities

## Verification approach
Use existing app e2e configs and SDK API models as references when behavior is unclear.

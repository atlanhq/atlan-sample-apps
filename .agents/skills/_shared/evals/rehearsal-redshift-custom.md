# Rehearsal: Redshift Custom Path

## Goal
Simulate a custom connector loop with auth branching and miner preflight behavior.

## Steps
1. Trigger `atlan-fact-verification-gate` and generate `verification_manifest.json`.
2. Trigger `atlan-app-scaffold-standard` and verify CLI-first scaffold path is used.
3. Trigger `atlan-sql-connector-patterns` in redshift/custom mode.
4. Trigger `atlan-workflow-args-secrets-state` to enforce state + credential_guid flow.
5. Trigger `atlan-sdk-objectstore-io-defaults` to preserve output path defaults.
6. Trigger `atlan-e2e-contract-validator` to produce `e2e_case_contract.yaml` for custom checks.
7. Trigger `atlan-cli-run-test-loop` to create `loop_report.md`.
8. Trigger `atlan-review-doc-sync` for risk review and docs alignment.

## Pass Criteria
- Decision tree selects redshift custom pattern.
- Scaffold path uses CLI commands (or documented install/shim fallback), not manual baseline mkdir/copy.
- Contract includes auth/preflight expectations.
- Loop report captures failures and remediation steps.
- Any CLI mismatch is logged in `cli-change-proposals.md`.

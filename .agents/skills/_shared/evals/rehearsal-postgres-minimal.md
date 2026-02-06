# Rehearsal: Postgres Minimal Path

## Goal
Simulate a minimal SDK-default connector loop using postgres patterns.

## Steps
1. Trigger `atlan-fact-verification-gate` and generate `verification_manifest.json`.
2. Trigger `atlan-app-scaffold-standard` with postgres/minimal mode.
3. Trigger `atlan-sdk-objectstore-io-defaults` for output contract checks.
4. Trigger `atlan-workflow-args-secrets-state` for args/credential handling.
5. Trigger `atlan-e2e-contract-validator` to produce `e2e_case_contract.yaml`.
6. Trigger `atlan-cli-run-test-loop` to generate `loop_report.md`.
7. Trigger `atlan-review-doc-sync` for findings-first review.

## Pass Criteria
- Verification manifest status is `ready`.
- E2E contract has required sections.
- Loop report includes failure or pass summary with next action.
- No SDK/CLI file edits are proposed or implied.

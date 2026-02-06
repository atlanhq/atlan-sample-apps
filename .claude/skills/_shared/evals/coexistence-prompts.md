# Coexistence Prompts

Use these prompts to verify that overlapping skills pick the right primary skill.

1. Prompt: "Build a new Postgres connector app and create the baseline file tree."
Expected primary skill: `atlan-app-scaffold-standard`
Expected secondary skill: `atlan-fact-verification-gate`

2. Prompt: "Fix this workflow so credentials are not passed directly into activity payloads."
Expected primary skill: `atlan-workflow-args-secrets-state`
Expected secondary skill: `atlan-fact-verification-gate`

3. Prompt: "Write raw and transformed outputs to object store using SDK defaults only."
Expected primary skill: `atlan-sdk-objectstore-io-defaults`
Expected secondary skill: `atlan-fact-verification-gate`

4. Prompt: "Run deps, test e2e, summarize failures, and propose patches."
Expected primary skill: `atlan-cli-run-test-loop`
Expected secondary skill: `atlan-e2e-contract-validator`

5. Prompt: "I need a Redshift app with miner query-history flow and IAM auth handling."
Expected primary skill: `atlan-sql-connector-patterns`
Expected secondary skill: `atlan-workflow-args-secrets-state`

6. Prompt: "Review this connector change, call out regressions first, and update docs."
Expected primary skill: `atlan-review-doc-sync`
Expected secondary skill: `atlan-fact-verification-gate`

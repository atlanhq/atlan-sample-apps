# Verification Sources

Use this as the canonical source map for Atlan app generation tasks. All references use portable `repo://...` URIs.

## Resolve sources on any machine
1. Discover live repos:
   `python ../scripts/resolve_source.py --print-map`
2. Resolve a source URI:
   `python ../scripts/resolve_source.py --source repo://application-sdk/application_sdk/clients/temporal.py`
3. Prefer local mirror when reproducibility matters:
   `python ../scripts/resolve_source.py --prefer-mirror --source repo://application-sdk/application_sdk/clients/temporal.py`
4. If live repos are unavailable, local mirror fallback in `source-mirror/` is used automatically.

## SDK Code (primary truth)
- `repo://application-sdk/application_sdk/services/objectstore.py`
- `repo://application-sdk/application_sdk/io/json.py`
- `repo://application-sdk/application_sdk/io/parquet.py`
- `repo://application-sdk/application_sdk/activities/common/utils.py`
- `repo://application-sdk/application_sdk/clients/temporal.py`
- `repo://application-sdk/application_sdk/server/fastapi/models.py`

## SDK Docs (required corroboration)
- `repo://application-sdk/docs/concepts/inputs.md`
- `repo://application-sdk/docs/concepts/outputs.md`
- `repo://application-sdk/docs/concepts/output_paths.md`
- `repo://application-sdk/docs/guides/sql-application-guide.md`

## CLI Usage (required for run/test/release tasks)
- `repo://atlan-cli/docs/app-command.md`
- `repo://atlan-cli/cmd/atlan/app.go`
- `repo://atlan-cli/cmd/atlan/app_run.go`
- `repo://atlan-cli/cmd/atlan/app_test_cmd.go`
- `repo://atlan-cli/cmd/atlan/app_release.go`

## Reference Connectors (pattern sources)
- `repo://atlan-postgres-app/main.py`
- `repo://atlan-postgres-app/app/clients/__init__.py`
- `repo://atlan-postgres-app/tests/e2e/test_postgres_workflow/config.yaml`
- `repo://atlan-redshift-app/main.py`
- `repo://atlan-redshift-app/app/clients.py`
- `repo://atlan-redshift-app/app/handlers/redshift.py`
- `repo://atlan-redshift-app/app/workflows/metadata_extraction/redshift.py`

## Rules
1. Treat SDK and CLI repos as read-only.
2. Apply built-in skill workflow defaults first.
3. Resolve and read sources when behavior is unclear, risky, or command-specific.
4. If SDK code and examples diverge, follow SDK code.
5. If CLI behavior and docs diverge, log a proposal in `cli-change-proposals.md`.
6. Create `verification_manifest.json` for behavior-changing tasks.

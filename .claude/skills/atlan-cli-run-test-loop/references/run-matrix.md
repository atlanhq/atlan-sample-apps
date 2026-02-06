# Run Matrix

Source resolution:
- Resolve any `repo://...` path with `python ../../_shared/scripts/resolve_source.py --source <repo-uri>`.

## Verify first
Read:
- `repo://atlan-cli/docs/app-command.md`
- `repo://atlan-cli/cmd/atlan/app.go`
- `repo://atlan-cli/cmd/atlan/app_run.go`
- `repo://atlan-cli/cmd/atlan/app_test_cmd.go`

## Preferred path (if available)
- `atlan app run`
- `atlan app test --test-type unit`
- `atlan app test --test-type e2e`

## Fallback path (sample-app workflow)
- `uv run poe start-deps`
- `uv run main.py`
- `uv run pytest`

## Reporting
Write `loop_report.md` for each loop.
Log CLI mismatches in `cli-change-proposals.md`.

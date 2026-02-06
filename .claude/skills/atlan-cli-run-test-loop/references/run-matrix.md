# Run Matrix

## Verify when needed
If command behavior is unclear, inspect available CLI docs/code and current app commands before executing.

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

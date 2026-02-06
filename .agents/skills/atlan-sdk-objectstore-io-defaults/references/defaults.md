# Objectstore Defaults

## Evidence approach
When needed, inspect SDK objectstore/io modules and output path docs using this order:
1. local SDK checkout (if present)
2. installed package source
3. remote SDK source/docs

## Required Conventions
1. Keep base path under `artifacts/apps/<application_name>/workflows/<workflow_id>/<run_id>`.
2. Write source extracts under `raw` and transformed entities under `transformed`.
3. Keep naming stable with e2e schema validation paths.

## Anti-Patterns
- Hardcoding `/tmp` as final output destination.
- Mixing app name and connection name in base output prefix.
- Writing transformed outputs without raw counterparts when workflow expects both.

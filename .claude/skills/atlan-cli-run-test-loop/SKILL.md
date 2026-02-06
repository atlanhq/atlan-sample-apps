---
name: atlan-cli-run-test-loop
description: Run Atlan app execution loops using CLI-first commands with automatic CLI availability checks and safe fallbacks.
---

# Atlan CLI Run Test Loop

Execute run/test/fix loops that a developer would expect from a normal app request.

## Workflow
1. Resolve target app path.
2. Verify CLI availability first:
   - Check `command -v atlan`.
   - If missing, ask permission to install CLI via official docs.
   - If install is deferred and sibling `atlan-cli` source exists, use temporary shim (`go run main.go app ...`).
3. Use CLI-first commands:
   - `atlan app run -p <app_path>`
   - `atlan app test -p <app_path> -t unit`
   - `atlan app test -p <app_path> -t e2e`
4. Use fallback commands only when CLI path is unavailable or mismatched:
   - `uv run poe start-deps`
   - `uv run main.py`
   - `uv run pytest`
5. Record each cycle in `loop_report.md` using `../_shared/assets/loop_report.md`.
6. If command behavior is unclear or conflicting, verify against CLI docs/code and run `atlan-fact-verification-gate`.
7. If a CLI mismatch appears, append proposal to `../_shared/references/cli-change-proposals.md`.

## Loop Contract
- Capture commands, failures, root cause, patch plan, and rerun result.
- Prefer deterministic command sequences and explicit paths.
- Do not imply or perform CLI repo edits.

## References
- Run matrix: `references/run-matrix.md`
- CLI proposal log: `../_shared/references/cli-change-proposals.md`

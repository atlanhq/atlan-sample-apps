---
name: atlan-cli-run-test-loop
description: Execute repeatable run/test/fix loops for Atlan apps using verified CLI commands or safe uv fallbacks. Use when running dependencies, app workers, unit tests, e2e tests, and triage iterations.
---

# Atlan CLI Run Test Loop

Run deterministic execution loops and report outcomes.

## Workflow
1. Start with command defaults in `references/run-matrix.md`.
2. Use `python ../_shared/scripts/resolve_source.py --source repo://atlan-cli/docs/app-command.md` when command behavior is unclear.
3. Prefer CLI commands when available and behavior is verified.
4. Use `uv` fallback commands when CLI command is hidden, missing, or mismatched.
5. Record each cycle in `loop_report.md` using template from `../_shared/assets/loop_report.md`.
6. If CLI mismatch appears, append proposal to `../_shared/references/cli-change-proposals.md`.
7. Run `atlan-fact-verification-gate` for behavior-changing loop fixes.

## Loop Contract
- Always capture commands, failures, root cause, patch plan, and rerun result.
- Do not run destructive commands.
- Do not imply or perform CLI repo edits.

## References
- Run matrix: `references/run-matrix.md`
- CLI proposal log: `../_shared/references/cli-change-proposals.md`

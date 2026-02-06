# Verification Sources

Use this guide for on-demand verification. Do not keep static source snapshots in the skill pack.

## Default behavior
1. Start with skill defaults and verified CLI command patterns.
2. Fetch source context only when behavior is unclear, risky, or command-specific.

## Where to fetch from
- SDK behavior: inspect sibling `application-sdk` repo.
- CLI behavior: inspect sibling `atlan-cli` repo (`docs/app-command.md`, `cmd/atlan/*`, `pkg/atlan/*`).
- App patterns: inspect sibling `atlan-postgres-app` and `atlan-redshift-app` repos.

## CLI facts to verify when commands are involved
- Scaffold: `atlan app init ...`
- Run: `atlan app run -p <path>`
- Test: `atlan app test -p <path> -t {unit|e2e|all}`
- Dependency/bootstrap helpers: `atlan app init tools`, `atlan app init dependencies`

## How to fetch
- Use fast local search first (`rg`, `find`, `ls`).
- Read only minimal files needed for current decision.
- If sibling repos are unavailable, ask user for path/context.

## Rules
1. Treat SDK and CLI repos as read-only.
2. If SDK code and examples diverge, follow SDK code.
3. If CLI docs and code diverge, follow CLI code and log a proposal in `cli-change-proposals.md`.
4. Create `verification_manifest.json` for behavior-changing tasks.

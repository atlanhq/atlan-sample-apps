---
name: atlan-app-scaffold-standard
description: Scaffold new Atlan apps from CLI templates as the default behavior when users ask for a new app, then align files to sample-app standards.
---

# Atlan App Scaffold Standard

When a user asks to create a new app, treat CLI bootstrap as implicit. Do not require users to mention CLI commands.

## Workflow
1. Interpret user intent:
   - If request is "create/build/new app" (even without technical detail), trigger this skill first.
2. Resolve app path and slug from user request.
3. Enforce CLI-first bootstrap:
   - Check `atlan` availability (`command -v atlan`).
   - If available: use `atlan app init -o <app_path> -t generic -y` (or `-s <sample>` when requested).
   - If missing: ask permission to install Atlan CLI using official setup docs.
   - If install is deferred but sibling `atlan-cli` source exists: use temporary shim from CLI repo (`go run main.go app ...`) for the same flow.
4. Verify template/sample choices only when needed:
   - `atlan app template list`
   - `atlan app sample list`
5. After scaffold, apply mode-specific structure from `references/scaffold-matrix.md`:
   - `postgres-minimal` by default.
   - `redshift-custom` only when requirements demand custom auth/preflight/miner behavior.
6. If behavior-critical decisions are unclear, run `atlan-fact-verification-gate`.
7. Continue implementation on scaffolded project files; do not hand-create base tree.

## Hard Rules
- Do not manually create baseline app skeleton when CLI scaffold is available.
- Do not copy another quickstart folder as a substitute for scaffold.
- Keep SDK/CLI repositories read-only.
- Keep outputs portable; no machine-local absolute paths.

## References
- Scaffold matrix: `references/scaffold-matrix.md`
- Shared verification map: `../_shared/references/verification-sources.md`

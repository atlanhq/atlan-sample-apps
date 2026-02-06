# Verification Sources

Use this guide for on-demand verification. Do not keep static source snapshots in the skill pack.

## Default behavior
1. Start with the skill's built-in defaults and workflow.
2. Only fetch source context when behavior is unclear, risky, or command-specific.

## Where to fetch from
- SDK behavior: inspect sibling `application-sdk` repo.
- CLI behavior: inspect sibling `atlan-cli` repo.
- App patterns: inspect sibling `atlan-postgres-app` and `atlan-redshift-app` repos.

## How to fetch
- Use fast local search first (`rg`, `find`, `ls`).
- Read only the minimal files needed for the current decision.
- If sibling repos are unavailable in the workspace, ask the user for path/context.

## Rules
1. Treat SDK and CLI repos as read-only.
2. If SDK code and examples diverge, follow SDK code.
3. If CLI behavior and docs diverge, log a proposal in `cli-change-proposals.md`.
4. Create `verification_manifest.json` for behavior-changing tasks.

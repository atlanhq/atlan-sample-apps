# Verification Sources

Use this guide for on-demand verification. Do not keep static source snapshots in the skill pack.

## Default behavior
1. Start with skill defaults and verified CLI command patterns.
2. Fetch source context only when behavior is unclear, risky, or command-specific.
3. Do not assume machine-local sibling repositories exist.

## Where to fetch from
- SDK behavior: Atlan SDK docs and source (`https://github.com/atlanhq/application-sdk`) or an explicitly provided local checkout.
- CLI behavior: Atlan CLI docs (`https://developer.atlan.com/sdks/cli/`) and source (`https://github.com/atlanhq/atlan-cli`) or an explicitly provided local checkout.
- App patterns: current repo samples and public Atlan sample apps, unless user provides local references.

## CLI facts to verify when commands are involved
- Scaffold: `atlan app init ...`
- Run: `atlan app run -p <path>`
- Test: `atlan app test -p <path> -t {unit|e2e|all}`
- Dependency/bootstrap helpers: `atlan app init tools`, `atlan app init dependencies`
- Dependency startup path: `uv run poe start-deps` behind CLI run/e2e
- Dapr initialization behavior in CLI tools flow

## How to fetch
- For install/setup facts, prefer official docs first.
- Use fast local search first (`rg`, `find`, `ls`) only for repositories already present in the current workspace.
- Read only minimal files needed for current decision.
- If required references are unavailable and network is blocked, ask user for path/context.

## Rules
1. Treat SDK and CLI repos as read-only.
2. If SDK code and examples diverge, follow SDK code.
3. If CLI docs and code diverge, follow CLI code and log a proposal in `cli-change-proposals.md`.
4. Create `verification_manifest.json` for behavior-changing tasks.
5. For dependency startup failures, verify both command flow and environment readiness (tool binaries + Dapr runtime state).

# Verification Sources

Use this guide for on-demand verification. Do not keep static source snapshots in the skill pack.

## Default behavior
1. Start with skill defaults and verified CLI command patterns.
2. Fetch source context only when behavior is unclear, risky, or command-specific.
3. Do not assume machine-local sibling repositories exist.

## SDK source resolution order
1. Local checkout if already present in current workspace or explicitly provided by the user.
2. Installed package source via local Python environment:
   - `python -c "import application_sdk,inspect; print(application_sdk.__file__)"`
3. Remote source code: `https://github.com/atlanhq/application-sdk`
4. Remote docs pages (for usage confirmation): `https://developer.atlan.com/` and SDK docs.

## CLI source resolution order
1. Local CLI binary behavior (`atlan --help`, `atlan app --help`, command-level help).
2. Local checkout if already present in current workspace or explicitly provided by the user.
3. Remote docs: `https://developer.atlan.com/sdks/cli/`
4. Remote source code: `https://github.com/atlanhq/atlan-cli`

## App pattern references
- Prefer current repo sample patterns first.
- For connector-standard work, compare against postgres/redshift patterns.
- Use external sample repos only when current repo patterns are insufficient.

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

## Exploration guardrails
1. Start with bounded first-pass exploration; avoid repository-wide sweeps.
2. Do not run recursive wildcard scans (for example full-tree `Search(\"**\")`) unless narrower methods failed.
3. Expand scope only when a specific unresolved fact blocks implementation.
4. Default first-pass budget:
   - `quickstart-utility`: <= 12 file reads
   - `connector-standard`: <= 20 file reads

## Evidence provenance tags
When recording `sdk_sources`, `docs_sources`, `cli_sources`, or fact evidence, prefix entries with one of:
- `[local-checkout]`
- `[installed-package]`
- `[local-binary]`
- `[remote-source]`
- `[remote-doc]`

## Rules
1. Treat SDK and CLI repos as read-only.
2. If SDK code and examples diverge, follow SDK code.
3. If CLI docs and code diverge, follow CLI code and log a proposal in `cli-change-proposals.md`.
4. Create `verification_manifest.json` for behavior-changing tasks.
5. For dependency startup failures, verify both command flow and environment readiness (tool binaries + Dapr runtime state).

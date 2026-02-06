---
name: atlan-fact-verification-gate
description: Verify Atlan app implementation facts against application-sdk code and docs plus atlan-cli usage before generating code. Use for any build, modify, test, review, or release request affecting app behavior.
---

# Atlan Fact Verification Gate

Create a verification checkpoint before generation, edits, or command execution.

## Workflow
1. Classify the task as `build`, `modify`, `test`, `review`, or `release`.
2. Read source map: `../_shared/references/verification-sources.md`.
3. Resolve required sources with `python ../_shared/scripts/resolve_source.py --source repo://...`.
4. Collect task-specific facts from SDK code first, then SDK docs, then CLI usage files if command orchestration is involved.
5. Create `verification_manifest.json` using `../_shared/assets/verification_manifest.json` as template.
6. Validate manifest:
   `python ../_shared/scripts/validate_verification_manifest.py verification_manifest.json`
7. Continue only if manifest status is `ready`.
8. If CLI mismatch is found, append a proposal entry to `../_shared/references/cli-change-proposals.md`.

## Output Contract
- Must produce `verification_manifest.json` for every non-trivial task.
- Must list `repo://...` evidence URIs for SDK/docs/CLI.
- Must never edit SDK or CLI repositories.

## References
- Checklist: `references/checklist.md`
- Artifact schema: `../_shared/references/artifact-templates.md`
- Multi-agent compatibility: `../_shared/references/agent-surface-compatibility.md`

---
name: atlan-fact-verification-gate
description: Verify Atlan app behavior against SDK, docs, and CLI context only when behavior is unclear, risky, or changing. Use for build, modify, test, review, or release tasks that need evidence-backed decisions.
---

# Atlan Fact Verification Gate

Create a lightweight verification checkpoint before behavior-changing decisions.

## Workflow
1. Classify task as `build`, `modify`, `test`, `review`, or `release`.
2. Read source guide: `../_shared/references/verification-sources.md`.
3. Fetch only the minimal source context needed from available repos.
4. Create `verification_manifest.json` using `../_shared/assets/verification_manifest.json` as template.
5. Validate manifest:
   `python ../_shared/scripts/validate_verification_manifest.py verification_manifest.json`
6. Continue if status is `ready`; otherwise resolve unknowns or ask user.
7. If CLI mismatch is found, append proposal entry to `../_shared/references/cli-change-proposals.md`.

## Output Contract
- Produce `verification_manifest.json` for non-trivial behavior changes.
- Record what was inspected; do not hardcode workstation-specific paths.
- Never edit SDK or CLI repositories.

## References
- Checklist: `references/checklist.md`
- Artifact schema: `../_shared/references/artifact-templates.md`
- Multi-agent compatibility: `../_shared/references/agent-surface-compatibility.md`

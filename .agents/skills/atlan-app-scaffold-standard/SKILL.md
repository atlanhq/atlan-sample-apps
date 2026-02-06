---
name: atlan-app-scaffold-standard
description: Scaffold Atlan app repositories with standard structure and starter files aligned to sample-app patterns. Use when creating a new app, connector, or major module skeleton.
---

# Atlan App Scaffold Standard

Generate app structure consistent with Atlan sample apps and connector references.

## Workflow
1. Start with scaffold defaults from `references/scaffold-matrix.md`.
2. Run `atlan-fact-verification-gate` when behavior-critical decisions are unclear or requirements deviate from defaults.
3. Select scaffold mode using `references/scaffold-matrix.md`:
   - `postgres-minimal` for SDK-default path.
   - `redshift-custom` for custom auth, handlers, query extraction, and config maps.
4. Create baseline tree:
   - `main.py`
   - `app/`
   - `frontend/`
   - `tests/unit/`
   - `tests/e2e/`
   - `local/`
5. Ensure command hints align with app repo practices (`uv run poe ...`).
6. Ensure no instructions require SDK/CLI repo edits.

## Constraints
- Prefer minimal scaffold first.
- Use custom scaffold only when requirements force it.
- Keep generated structure test-first (unit + e2e hooks present).

## References
- Scaffold matrix: `references/scaffold-matrix.md`
- Shared verification map: `../_shared/references/verification-sources.md`

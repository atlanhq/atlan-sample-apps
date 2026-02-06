# Trigger Evals

1. Positive: "Run deps, execute tests, and keep patching until e2e passes."
Expected: trigger this skill.

2. Positive: "Use CLI where possible, otherwise fallback to uv commands and report."
Expected: trigger this skill.

3. Negative: "Design a widget for credential input."
Expected: do not trigger this skill.

4. Negative: "Write SQL query templates for table extraction."
Expected: do not trigger this skill.

5. Ambiguous: "Validate app run commands for this repo."
Expected: trigger this skill after verification gate.

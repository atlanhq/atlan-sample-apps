# Trigger Evals

1. Positive: "Fix this connector so output files use SDK default object store paths."
Expected: trigger this skill.

2. Positive: "Review whether our raw/transformed writes follow SDK IO conventions."
Expected: trigger this skill.

3. Negative: "Create a new README for this app."
Expected: do not trigger this skill.

4. Negative: "Tune SQL query performance for metadata fetch."
Expected: do not trigger this skill.

5. Ambiguous: "Generate e2e config with expected output paths."
Expected: trigger this skill with `atlan-e2e-contract-validator`.

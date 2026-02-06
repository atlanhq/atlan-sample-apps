# Trigger Evals

1. Positive: "Create e2e contract and config for a new metadata workflow."
Expected: trigger this skill.

2. Positive: "Validate that expected API responses and schema assertions are complete."
Expected: trigger this skill.

3. Negative: "Implement IAM role auth in Redshift client."
Expected: do not trigger this skill.

4. Negative: "Refactor workflow class names for readability."
Expected: do not trigger this skill.

5. Ambiguous: "Update tests after changing output path logic."
Expected: trigger this skill with `atlan-sdk-objectstore-io-defaults`.

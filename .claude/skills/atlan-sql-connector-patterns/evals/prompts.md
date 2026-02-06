# Trigger Evals

1. Positive: "Build a new SQL connector and decide whether we need source-specific overrides."
Expected: trigger this skill.

2. Positive: "Add Redshift IAM role auth and query-history miner flow."
Expected: trigger this skill.

3. Negative: "Write unit tests for transformer output formatting."
Expected: do not trigger this skill.

4. Negative: "Update CI YAML to pin Python version."
Expected: do not trigger this skill.

5. Ambiguous: "New connector for SQL source with unknown auth constraints."
Expected: trigger this skill and default to minimal unless evidence requires custom.

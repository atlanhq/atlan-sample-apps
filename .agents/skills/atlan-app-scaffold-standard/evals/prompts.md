# Trigger Evals

1. Positive: "Create a new Atlan Postgres app scaffold with tests and frontend stubs."
Expected: trigger this skill.

2. Positive: "Generate a Redshift-style connector skeleton with custom workflows and handlers."
Expected: trigger this skill.

3. Negative: "Update include-filter behavior in this existing config."
Expected: do not trigger this skill.

4. Negative: "Run the existing test suite and summarize failures."
Expected: do not trigger this skill.

5. Ambiguous: "Set up a new app folder and validate run commands."
Expected: trigger this skill first, then `atlan-cli-run-test-loop`.

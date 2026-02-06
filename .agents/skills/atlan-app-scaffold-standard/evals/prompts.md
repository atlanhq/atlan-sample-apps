# Trigger Evals

1. Positive: "Build a new Atlan app that summarizes failed jobs by team."
Expected: trigger this skill.

2. Positive: "Create a starter app for Redshift metadata sync with room for custom auth handling."
Expected: trigger this skill.

3. Negative: "Fix include-filter behavior in this existing workflow config."
Expected: do not trigger this skill.

4. Negative: "Run tests and summarize why e2e is failing."
Expected: do not trigger this skill.

5. Ambiguous: "Set up a new app and get it runnable locally."
Expected: trigger this skill first, ask 1-3 clarifying business-behavior questions, then `atlan-cli-run-test-loop`.

6. Positive: "Create a new app for customer ticket triage and make it runnable."
Expected: if `atlan` is missing, install CLI using web-first flow; do not search for local `atlan-cli` clones.

7. Positive: "Create a small utility app that summarizes alerts and write tests."
Expected: select `quickstart-utility` tier and enforce its minimum quality bar.

# Trigger Evals

1. Positive: "Make this app runnable locally and keep iterating until unit and e2e tests pass."
Expected: trigger this skill.

2. Positive: "Run the app, run tests, fix failures, and report what changed."
Expected: trigger this skill.

3. Negative: "Design a setup form for credentials."
Expected: do not trigger this skill.

4. Negative: "Write SQL templates for table extraction."
Expected: do not trigger this skill.

5. Ambiguous: "I created a new app. Make sure it works end to end."
Expected: trigger this skill after scaffold + verification.

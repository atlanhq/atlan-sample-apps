# Trigger Evals

1. Positive: "Build a new app for monthly data quality checks and start with safe defaults."
Expected: trigger this skill before implementation.

2. Positive: "Create this connector and make sure command usage is actually correct before coding."
Expected: trigger this skill.

3. Negative: "Explain Atlan apps in simple terms."
Expected: do not trigger this skill.

4. Negative: "Rewrite this README section to be shorter."
Expected: do not trigger this skill.

5. Ambiguous: "Set up this new app and get tests running."
Expected: trigger this skill first, then `atlan-app-scaffold-standard` and `atlan-cli-run-test-loop`.

6. Positive: "Build this app on a machine that does not have a local SDK checkout."
Expected: trigger this skill and use portable verification sources (installed package or remote source/docs).

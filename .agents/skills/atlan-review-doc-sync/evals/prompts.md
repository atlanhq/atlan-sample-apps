# Trigger Evals

1. Positive: "Review this connector diff for regressions and update docs accordingly."
Expected: trigger this skill.

2. Positive: "Summarize findings first, then provide a concise change summary."
Expected: trigger this skill.

3. Negative: "Create a new app scaffold from scratch."
Expected: do not trigger this skill.

4. Negative: "Run e2e test contract validation only."
Expected: do not trigger this skill.

5. Ambiguous: "Prepare this app for handoff."
Expected: trigger this skill, optionally chaining run-test loop checks.

# Trigger Evals

1. Positive: "I am on a fresh Mac and `atlan` is not found. Install and configure it."
Expected: trigger this skill.

2. Positive: "Set up Atlan CLI on Linux and configure it for `https://tenant.atlan.com`."
Expected: trigger this skill.

3. Positive: "Reinstall Atlan CLI and reset logs to debug."
Expected: trigger this skill even if `atlan` already exists.

4. Negative: "Create a new app that summarizes incident alerts by team."
Expected: do not trigger this skill first; scaffold skill triggers first and only calls this skill if CLI is missing.

5. Negative: "Fix failing e2e tests in this existing app."
Expected: do not trigger this skill if `atlan` is already available.

6. Ambiguous: "CLI setup is broken; make this machine ready for app development."
Expected: trigger this skill, verify `atlan` availability, then configure minimum `.atlan/config.yaml` and auth path.

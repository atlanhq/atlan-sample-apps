# Trigger Evals

1. Positive: "Before writing any connector code, verify the output path and workflow arg contracts."  
Expected: trigger this skill.

2. Positive: "I need a source-of-truth check across SDK docs and CLI before implementing tests."  
Expected: trigger this skill.

3. Negative: "Explain what Atlan is at a high level."  
Expected: do not trigger this skill.

4. Negative: "Rewrite this paragraph for readability."  
Expected: do not trigger this skill.

5. Ambiguous: "Set up run commands for the app."  
Expected: trigger this skill first, then hand off to `atlan-cli-run-test-loop`.

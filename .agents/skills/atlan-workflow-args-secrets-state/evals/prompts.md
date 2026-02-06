# Trigger Evals

1. Positive: "Refactor this workflow to use credential_guid and secret retrieval."  
Expected: trigger this skill.

2. Positive: "I need to save workflow state before child workflow execution."  
Expected: trigger this skill.

3. Negative: "Add a frontend field for host and port."  
Expected: do not trigger this skill.

4. Negative: "Update SQL table extraction query."  
Expected: do not trigger this skill.

5. Ambiguous: "Fix this activity payload handling bug."  
Expected: trigger this skill after verification.

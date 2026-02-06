# Review Checklist

1. Does behavior match verification manifest facts?
2. Are output paths and schema outputs validated?
3. Are workflow args, secrets, and state handling safe?
4. Are run/test loops reproducible?
5. Are docs updated for changed behavior?
6. Are there any implied SDK/CLI edits? If yes, reject and log proposal.
7. Does workflow use dedicated business activities instead of hiding full behavior in `get_workflow_args` side effects?
8. If tier is `quickstart-utility`, are minimum tests present (two unit cases + e2e artifact assertion)?
9. If tier is `connector-standard`, is structure/test depth aligned with postgres/redshift patterns?
10. Does loop report include rerun evidence after failures are fixed?

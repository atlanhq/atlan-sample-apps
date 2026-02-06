# App Quality Bar

Use this quality bar to decide whether an app is a simple quickstart utility or a connector-standard app.

## Tier Selection
1. `quickstart-utility` (default):
   - User asks for a small business workflow utility (for example summary, alert digest, routing, enrichment).
   - No source-specific auth, miner, metadata extraction, or connector template complexity is required.
2. `connector-standard`:
   - User asks for source connector behavior comparable to postgres/redshift patterns.
   - Source-specific auth, preflight, SQL extraction, metadata/query workflows, or connector templates are required.

## quickstart-utility Minimum Bar
1. Workflow must orchestrate at least:
   - workflow args retrieval activity
   - one dedicated business activity
2. Do not hide business side effects inside `get_workflow_args`.
3. Unit tests must include at least two cases:
   - happy path
   - invalid/edge input path
4. E2E must cover:
   - health check
   - workflow run
   - config fetch
   - output assertion on produced artifact(s)
5. `loop_report.md` must include rerun result after each applied fix.

## connector-standard Minimum Bar
1. Keep connector structure aligned with postgres/redshift conventions:
   - `app/clients*`
   - `app/handlers*` when source-specific behavior exists
   - workflow/activity split for metadata/query extraction where applicable
   - SQL/templates/resources organized for extraction/transformation flows
2. Test coverage should include:
   - client/handler/workflow unit tests
   - e2e scenarios for relevant filter/auth paths
   - output/schema assertions across raw and transformed artifacts
3. Preserve SDK defaults for args/secrets/state and output paths.

## Handoff Gate
Before marking complete, explicitly state:
1. chosen quality tier
2. why this tier is correct for the request
3. which minimum-bar checks were satisfied

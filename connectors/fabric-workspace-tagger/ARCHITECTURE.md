# Architecture: Microsoft Fabric Workspace Tagger

## Overview

This document provides a comprehensive architecture overview of the Fabric Workspace Tagger app, including cross-references to the Atlan Application SDK, pyatlan SDK, and Microsoft Fabric/Power BI APIs.

## Design Goals

1. **Nightly synchronization** of workspace metadata from Fabric to Atlan
2. **Capacity governance** by tagging workspaces with their parent capacity
3. **Idempotent tag management** with namespace isolation
4. **Extensible tag extraction** based on organizational conventions
5. **Resilient execution** with retries and partial failure handling

## System Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│  Atlan Platform                                                         │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Apps Framework Runtime                                           │ │
│  │                                                                    │ │
│  │  ┌─────────────┐        ┌──────────────┐       ┌──────────────┐ │ │
│  │  │  Temporal   │◄───────┤   Workflow   │──────►│    Dapr      │ │ │
│  │  │  (orchestr.)│        │   (business) │       │  (state/msg) │ │ │
│  │  └─────────────┘        └──────────────┘       └──────────────┘ │ │
│  │         │                       │                       │         │ │
│  └─────────┼───────────────────────┼───────────────────────┼─────────┘ │
│            │                       │                       │           │
│            ▼                       ▼                       ▼           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  FabricWorkspaceTagSyncWorkflow                                 │  │
│  │                                                                   │  │
│  │  1. get_workflow_args() ──► Validate config                     │  │
│  │  2. fetch_fabric_workspaces() ──┐                               │  │
│  │  3. update_atlan_workspace_tags()│                              │  │
│  └──────────────────────────────────┼───────────────────────────────┘  │
│                                     │                                  │
└─────────────────────────────────────┼──────────────────────────────────┘
                                      │
                  ┌───────────────────┼────────────────────┐
                  │                   │                    │
                  ▼                   ▼                    ▼
      ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
      │ FabricAPIClient  │  │  Atlan Metadata  │  │  App Config &    │
      │                  │  │  API (pyatlan)   │  │  Secret Store    │
      │ • MSAL auth      │  │                  │  │                  │
      │ • List ws/caps   │  │ • Search assets  │  │ • Tenant ID      │
      │ • Tag extraction │  │ • Update tags    │  │ • Client secret  │
      └────────┬─────────┘  └──────────────────┘  └──────────────────┘
               │
               ▼
      ┌──────────────────┐
      │ Microsoft Fabric │
      │ / Power BI API   │
      │                  │
      │ • Admin/groups   │
      │ • Admin/caps     │
      └──────────────────┘
```

## Data Flow

### 1. Workflow Trigger

**Scheduler** → Temporal → `FabricWorkspaceTagSyncWorkflow.run(workflow_config)`

- Trigger can be:
  - **Cron schedule** (nightly at 2am UTC) via Temporal schedules
  - **Manual execution** via Atlan UI or API
  - **Event-driven** (future: on Power BI workspace creation webhook)

**References**:
- Atlan workflow scheduling: [developer.atlan.com/snippets/workflows/manage/schedules](https://developer.atlan.com/snippets/workflows/manage/schedules/)
- Temporal schedules: [docs.temporal.io/workflows#schedule](https://docs.temporal.io/workflows#schedule)

### 2. Activity: get_workflow_args

**Input**: Raw workflow config dict
**Output**: Validated `AppConfig` model

**Logic**:
```python
config = AppConfig(**workflow_config)  # Pydantic validation
# Validates required fields: tenant_id, client_id, tag_namespace, etc.
```

**References**:
- `application_sdk.activities.ActivitiesInterface`: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- Pydantic validation: [docs.pydantic.dev](https://docs.pydantic.dev/)

### 3. Activity: fetch_fabric_workspaces

**Input**: `AppConfig`
**Output**: `List[FabricWorkspace]`

**Sequence**:

```
1. Get access token via MSAL
   ├─ Authority: https://login.microsoftonline.com/{tenant_id}
   ├─ Scope: https://analysis.windows.net/powerbi/api/.default
   └─ Client credentials flow (client_id + client_secret)

2. Call Power BI Admin API: GET /v1.0/myorg/admin/capacities
   └─ Returns: [{ id, displayName, sku, region, state }]

3. Call Power BI Admin API: GET /v1.0/myorg/admin/groups
   ├─ Returns: [{ id, name, capacityId, state }]
   └─ Join with capacities by capacityId

4. Extract custom tags from workspace metadata
   ├─ Naming conventions (e.g., "Manufacturing BI" → pillar:Manufacturing)
   └─ Description parsing (future: call additional Fabric APIs)

5. Apply workspace_filter_regex (if configured)
   └─ Filter workspaces by name pattern

6. Return normalized FabricWorkspace list
```

**References**:
- MSAL Python: [learn.microsoft.com/entra/msal/python](https://learn.microsoft.com/en-us/entra/msal/python/)
- Power BI Admin API - List Groups: [learn.microsoft.com/rest/api/power-bi/admin/groups-get-groups-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-groups-as-admin)
- Power BI Admin API - List Capacities: [learn.microsoft.com/rest/api/power-bi/admin/get-capacities-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/get-capacities-as-admin)
- Fabric Admin API (alternative): [learn.microsoft.com/rest/api/fabric/admin/workspaces](https://learn.microsoft.com/en-us/rest/api/fabric/admin/workspaces)

### 4. Activity: update_atlan_workspace_tags

**Input**: `AppConfig`, `List[FabricWorkspace]`
**Output**: `WorkspaceTagSyncResult` (counts + errors)

**Sequence**:

```
For each workspace in workspaces:

1. Resolve PowerBIWorkspace asset in Atlan
   ├─ Search by qualifiedName pattern: {connection_qn}/{workspace_name}
   ├─ Fallback: Search by name.keyword + asset type
   └─ Returns: PowerBIWorkspace | None

2. Compute desired tags
   ├─ capacity:{workspace.capacity_name} (if capacity exists)
   ├─ pillar:{tag_value} (from workspace.tags)
   └─ env:{tag_value} (from workspace.tags)

3. Perform namespace-aware tag update
   ├─ Read existing assetTags from PowerBIWorkspace
   ├─ Identify managed tags (in namespace: capacity, pillar, env)
   ├─ Compute new_tags = (existing - managed) | desired
   └─ If changed: persist via pyatlan

4. Update asset using pyatlan
   ├─ PowerBIWorkspace.updater(qualified_name, name)
   ├─ updater.atlan_tags = list(new_tags)
   └─ client.asset.save(updater)

5. Record result (updated / skipped / failed)
```

**References**:
- pyatlan AtlanClient: [developer.atlan.com/snippets/common-examples/tags](https://developer.atlan.com/snippets/common-examples/tags/)
- PowerBIWorkspace model: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- Asset search DSL: `pyatlan.model.search.DSL`, `pyatlan.model.search.Term`
- Asset updater pattern: `PowerBIWorkspace.updater()` → `client.asset.save()`

## Key Design Decisions

### 1. Namespace-Aware Tag Management

**Problem**: Multiple processes may tag the same assets; we need to avoid conflicts.

**Solution**: Tag namespace isolation

```python
# App owns tags in these namespaces:
managed_namespaces = ["capacity", "pillar", "env"]

# On each run:
existing_tags = {"capacity:Old", "pillar:Mfg", "other:UserTag"}
desired_tags = {"capacity:New", "pillar:Mfg"}

# Remove stale managed tags, keep unmanaged tags:
new_tags = (existing_tags - managed) | desired
# Result: {"other:UserTag", "capacity:New", "pillar:Mfg"}
```

**Benefits**:
- Idempotent: repeated runs converge to desired state
- No interference with other tagging workflows
- Users can still manually add tags outside managed namespaces

### 2. Resilient Execution with Temporal Retry Policies

**Configuration**:
```python
retry_policy = RetryPolicy(
    maximum_attempts=3,
    backoff_coefficient=2,
    initial_interval=timedelta(seconds=1),
)
```

**Behavior**:
- Transient Fabric API failures (HTTP 429, 503) → automatic retry with exponential backoff
- Permanent failures (401 Unauthorized) → fail fast after 3 attempts
- Partial failures in `update_atlan_workspace_tags` → continue processing other workspaces, report errors in result

**References**:
- Temporal retry policies: [docs.temporal.io/retry-policies](https://docs.temporal.io/retry-policies)
- `temporalio.common.RetryPolicy`

### 3. Workspace Resolution Strategy

**Challenge**: Match Fabric workspace ID to Atlan PowerBIWorkspace asset

**Strategy**:

1. **Primary**: Search by `qualifiedName` pattern
   - Format: `{connection_qn}/{workspace_name}`
   - Example: `default/powerbi/1234567890/Manufacturing BI`

2. **Fallback**: Search by `name.keyword` + `connectionQualifiedName`
   - Handles cases where workspace name changed in Fabric but not yet re-crawled

**References**:
- PowerBIWorkspace.qualifiedName structure: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- Atlan search DSL: `pyatlan.model.search.DSL`

### 4. Tag Extraction Customization

**Default implementation** (in `fabric_client.py`):
```python
def _extract_tags_from_workspace(workspace: dict) -> dict[str, str]:
    tags = {}
    name = workspace.get("name", "")

    # Heuristic: parse name for pillar
    if "Manufacturing" in name:
        tags["pillar"] = "Manufacturing"

    return tags
```

**Customization options**:
- Parse workspace description field
- Call additional Fabric APIs (e.g., Fabric Workspaces API for extended metadata)
- Integrate with external CMDB or tagging service
- Use regex patterns from config

### 5. Secret Management

**App secrets** (e.g., `FABRIC_CLIENT_SECRET`) are stored in:
- **Local dev**: Environment variables
- **Production (Atlan)**: App Framework secret store (Dapr Secrets API)

**Access pattern**:
```python
client_secret = os.environ.get("FABRIC_CLIENT_SECRET")
if not client_secret:
    raise ValueError("FABRIC_CLIENT_SECRET not found")
```

**References**:
- App Framework secrets: [docs.atlan.com/product/capabilities/build-apps/concepts/apps-framework](https://docs.atlan.com/product/capabilities/build-apps/concepts/apps-framework)
- Dapr secrets: [docs.dapr.io/operations/components/setup-secret-store](https://docs.dapr.io/operations/components/setup-secret-store/)

## Error Handling

### Activity-Level Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `ValueError: Missing required config` | Invalid workflow config | Fail fast, log error, return to user |
| `MSAL token acquisition failure` | Invalid tenant/client ID or secret | Retry 3x, then fail activity |
| `HTTP 429 Rate Limit` | Too many API calls to Fabric | Retry with exponential backoff (Temporal handles) |
| `PowerBIWorkspace not found in Atlan` | Workspace not yet crawled | Log warning, skip workspace, continue processing others |
| `pyatlan save failed` | Atlan API error | Log error, increment `workspaces_failed`, continue |

### Workflow-Level Error Recovery

- **Transient failures**: Temporal automatically retries activities per `RetryPolicy`
- **Partial failures**: Workflow completes successfully even if some workspaces fail; errors reported in `result.errors`
- **Complete failure**: Workflow execution fails; visible in Temporal UI for investigation

## Performance Considerations

### Batching & Pagination

**Fabric API**:
- Power BI Admin API supports `$top` parameter (max 5000)
- For tenants with >5000 workspaces, implement pagination:
  ```python
  response = self._make_request("GET", url, params={"$top": 5000, "$skip": offset})
  ```

**Atlan API**:
- Search results are paginated by default (default: 100 per page)
- For bulk tag updates, consider using `client.asset.save_merges([...])` for batch operations (future optimization)

### Execution Time Estimates

| Step | Time (typical) | Notes |
|------|----------------|-------|
| Fabric auth | 1-2 sec | MSAL token acquisition |
| List capacities | 2-5 sec | ~100 capacities |
| List workspaces | 5-30 sec | Depends on workspace count |
| Update Atlan tags | 0.5 sec/workspace | Sequential; can parallelize in future |
| **Total (100 workspaces)** | **~1-2 min** | |
| **Total (1000 workspaces)** | **~8-10 min** | |

**Timeout settings**:
- `fetch_fabric_workspaces`: 10 min (handles large tenants)
- `update_atlan_workspace_tags`: 30 min (handles 3000+ workspaces)

## Extensibility

### Adding New Tag Sources

**Example**: Add tags from Fabric Workspace API (beyond Power BI API)

1. Update `FabricAPIClient` to call Fabric Admin Workspaces API:
   ```python
   def list_fabric_workspaces_extended(self) -> list:
       url = f"{self.FABRIC_ADMIN_BASE_URL}/workspaces"
       return self._make_request("GET", url).get("value", [])
   ```

2. Merge results with Power BI workspaces:
   ```python
   fabric_metadata = {ws["id"]: ws for ws in fabric_client.list_fabric_workspaces_extended()}
   for ws in workspaces:
       if ws.id in fabric_metadata:
           # Extract additional tags from Fabric metadata
           pass
   ```

**Reference**: [Fabric Admin API - Workspaces](https://learn.microsoft.com/en-us/rest/api/fabric/admin/workspaces/list-workspaces)

### Propagating Tags to Child Assets

**Use case**: Also tag PowerBIDataset and PowerBIReport assets with workspace tags

**Implementation**:
```python
# After updating workspace tags, find child assets
child_assets = client.asset.find_connections_by_guid(
    guid=workspace.guid,
    asset_type=PowerBIDataset,  # or PowerBIReport
)

for child in child_assets:
    child_updater = PowerBIDataset.updater(child.qualified_name, child.name)
    child_updater.atlan_tags = workspace.atlan_tags  # Inherit from workspace
    client.asset.save(child_updater)
```

**Reference**: [pyatlan - Find connections](https://developer.atlan.com/snippets/common-examples/relationships/)

## Testing Strategy

### Unit Tests

- **Models**: Validate Pydantic schemas (see `tests/test_models.py`)
- **Tag computation**: Test `_compute_desired_tags()` logic
- **Tag update**: Test namespace-aware merge logic

### Integration Tests

- **Fabric API client**: Mock MSAL and Fabric API responses
- **Atlan client**: Mock `AtlanClient` search and save operations
- **End-to-end**: Use Temporal test framework to execute workflow with mocked activities

**References**:
- Temporal testing: [docs.temporal.io/develop/python/testing-suite](https://docs.temporal.io/develop/python/testing-suite)
- pytest-asyncio: [pytest-asyncio.readthedocs.io](https://pytest-asyncio.readthedocs.io/)

### E2E Testing (in deployed environment)

1. Deploy app to Atlan sandbox
2. Configure with test tenant (small workspace count)
3. Run workflow manually
4. Verify tags appear on PowerBIWorkspace assets
5. Re-run workflow, verify idempotency (no duplicate tags)

## Monitoring & Observability

### Metrics

App Framework provides built-in observability via OpenTelemetry:

```python
from application_sdk.observability.metrics_adaptor import get_metrics

metrics = get_metrics()
metrics.counter("workspaces_processed").add(1)
metrics.gauge("total_workspaces").set(len(workspaces))
```

**Key metrics**:
- `workspaces_fetched`: Count from Fabric API
- `workspaces_updated`: Count successfully updated in Atlan
- `workspaces_failed`: Count of failures
- `activity_duration_seconds`: Per-activity execution time

**References**:
- App Framework observability: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- OpenTelemetry Python: [opentelemetry.io/docs/languages/python](https://opentelemetry.io/docs/languages/python/)

### Logs

Structured logging via `application_sdk.observability.logger_adaptor`:

```python
logger.info(f"Fetched {len(workspaces)} workspaces from Fabric")
logger.warning(f"Workspace {ws.name} not found in Atlan; skipping")
logger.error(f"Failed to update workspace {ws.name}: {e}", exc_info=True)
```

**Log levels**:
- `INFO`: Workflow progress, counts, successful operations
- `WARNING`: Skipped workspaces, non-critical issues
- `ERROR`: API failures, tag update failures

### Alerting

Set up alerts in Atlan or external monitoring (e.g., Datadog, Grafana):
- **Alert**: `workspaces_failed > 10%` of total
- **Alert**: Workflow execution time > 30 min (indicates performance degradation)
- **Alert**: Workflow failed (no workspaces processed)

## Deployment

### Build & Publish

```bash
# Build Docker image
docker build -t fabric-workspace-tagger:0.1.0 .

# Publish to Atlan container registry (Harbor)
docker tag fabric-workspace-tagger:0.1.0 registry.atlan.com/apps/fabric-workspace-tagger:0.1.0
docker push registry.atlan.com/apps/fabric-workspace-tagger:0.1.0
```

### Deploy to Atlan

1. **Package app** as Atlan workflow package
2. **Configure secrets** in app secret store:
   - `FABRIC_CLIENT_SECRET`
3. **Configure workflow** via UI or API:
   - `fabric_tenant_id`, `fabric_client_id`, etc.
4. **Set up schedule** (cron: `0 2 * * *` for 2am UTC nightly)
5. **Monitor** via Temporal UI and Atlan workflow logs

**References**:
- Atlan app deployment: [docs.atlan.com/product/capabilities/build-apps](https://docs.atlan.com/product/capabilities/build-apps)
- Harbor registry: Internal Atlan documentation

## Cross-Reference Summary

### Atlan Application SDK
- GitHub: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- Workflow base: `application_sdk.workflows.WorkflowInterface`
- Activities base: `application_sdk.activities.ActivitiesInterface`
- App entry point: `application_sdk.application.BaseApplication`

### pyatlan SDK
- Docs: [developer.atlan.com](https://developer.atlan.com/)
- PowerBIWorkspace: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- Tags: [developer.atlan.com/snippets/common-examples/tags](https://developer.atlan.com/snippets/common-examples/tags/)
- Workflow schedules: [developer.atlan.com/snippets/workflows/manage/schedules](https://developer.atlan.com/snippets/workflows/manage/schedules/)

### Microsoft Fabric / Power BI APIs
- Power BI REST API: [learn.microsoft.com/rest/api/power-bi](https://learn.microsoft.com/en-us/rest/api/power-bi/)
- Admin - List Groups: [learn.microsoft.com/rest/api/power-bi/admin/groups-get-groups-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-groups-as-admin)
- Admin - List Capacities: [learn.microsoft.com/rest/api/power-bi/admin/get-capacities-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/get-capacities-as-admin)
- Fabric Admin API: [learn.microsoft.com/rest/api/fabric/admin](https://learn.microsoft.com/en-us/rest/api/fabric/admin/)
- MSAL Python: [learn.microsoft.com/entra/msal/python](https://learn.microsoft.com/en-us/entra/msal/python/)

### Temporal
- Workflows: [docs.temporal.io/workflows](https://docs.temporal.io/workflows)
- Retry policies: [docs.temporal.io/retry-policies](https://docs.temporal.io/retry-policies)
- Schedules: [docs.temporal.io/workflows#schedule](https://docs.temporal.io/workflows#schedule)

## Future Enhancements

1. **PowerBICapacity asset type**: Once Atlan adds native capacity assets, update the app to create/update capacities instead of just tagging workspaces
2. **Tag propagation**: Automatically propagate workspace tags to child datasets/reports
3. **Webhook integration**: React to Fabric workspace creation events in real-time (vs. nightly batch)
4. **Custom metadata**: Store capacity info as custom metadata instead of tags for richer governance
5. **Parallel tag updates**: Use `asyncio.gather()` to update Atlan tags in parallel (currently sequential)
6. **Advanced tag extraction**: Call Fabric Lineage API to derive tags from data sources used by workspace

---

**Version**: 0.1.0
**Last Updated**: 2026-02-19

# Microsoft Fabric Workspace Tagger

Atlan Application Framework app that synchronizes workspace metadata and tags from Microsoft Fabric / Power BI to Atlan, enabling governance and cost management use cases.

## Overview

This app addresses the requirement to track which **Fabric capacity** each Power BI workspace belongs to, and to apply custom tags to workspaces based on their metadata. It runs as a scheduled workflow that:

1. **Fetches workspace metadata** from Microsoft Fabric / Power BI Admin APIs
2. **Enriches workspaces** with capacity information and custom tags
3. **Updates Atlan** by applying tags to `PowerBIWorkspace` assets
4. **Maintains tag namespaces** to avoid conflicts with other tagging processes

## Use Cases

- **Capacity Governance**: Tag workspaces with their parent Fabric capacity (e.g., `capacity:Fabric-Critical-01`) to enable filtering and reporting by capacity
- **Cost Management**: Identify "critical" vs. "non-critical" workspaces for resource allocation and chargeback
- **Organizational Taxonomy**: Apply pillar tags (e.g., `pillar:Manufacturing`, `pillar:Sales`) based on naming conventions
- **Environment Tracking**: Tag workspaces by environment (e.g., `env:prod`, `env:dev`)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Atlan App Framework Runtime (Temporal + Dapr)              │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FabricWorkspaceTagSyncWorkflow                     │   │
│  │                                                       │   │
│  │  1. get_workflow_args()                             │   │
│  │  2. fetch_fabric_workspaces()  ───────────┐        │   │
│  │  3. update_atlan_workspace_tags()          │        │   │
│  └────────────────────────────────────────────┼────────┘   │
│                                                │             │
└────────────────────────────────────────────────┼─────────────┘
                                                 │
                        ┌────────────────────────┼──────────────────────┐
                        │                        │                      │
                        ▼                        ▼                      ▼
            ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
            │ Microsoft Fabric    │  │ Power BI Admin   │  │ Atlan Metadata   │
            │ Admin API           │  │ API              │  │ API (pyatlan)    │
            │                     │  │                  │  │                  │
            │ • Workspaces        │  │ • Capacities     │  │ • Search assets  │
            │ • Metadata          │  │ • Workspace→     │  │ • Update tags    │
            │                     │  │   Capacity map   │  │                  │
            └─────────────────────┘  └──────────────────┘  └──────────────────┘
```

### Workflow Activities

1. **`get_workflow_args`**: Validates configuration (tenant ID, client ID, tag namespace, etc.)
2. **`fetch_fabric_workspaces`**:
   - Authenticates to Azure AD using MSAL (client credentials flow)
   - Calls Power BI Admin API to list workspaces
   - Calls Power BI Admin API to list capacities
   - Joins workspace → capacity mapping
   - Extracts custom tags from workspace metadata (naming conventions, descriptions)
3. **`update_atlan_workspace_tags`**:
   - Searches Atlan for `PowerBIWorkspace` assets by qualified name
   - Computes desired tags (capacity, pillar, env, etc.)
   - Performs namespace-aware tag update (removes stale tags in managed namespace, applies new tags)
   - Uses `pyatlan` SDK to persist tag changes

## Setup

### Prerequisites

- Python 3.11 or 3.12
- `uv` package manager (recommended) or `pip`
- Dapr CLI (for local development)
- Temporal CLI (for local development)
- Azure AD service principal with **Power BI Admin API** permissions

### Azure AD / Service Principal Setup

1. **Create an Azure AD App Registration**:
   - Navigate to [Azure Portal → App Registrations](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps)
   - Create a new registration
   - Note the **Application (client) ID** and **Directory (tenant) ID**

2. **Create a Client Secret**:
   - Go to "Certificates & secrets" → "New client secret"
   - Note the secret value (you won't be able to see it again)

3. **Grant Power BI Admin API Permissions**:
   - Go to "API permissions" → "Add a permission" → "Power BI Service"
   - Add **Tenant.Read.All** and **Workspace.Read.All** permissions
   - Grant admin consent

4. **Configure Power BI Admin Access**:
   - Ensure the service principal is added to a security group with Power BI Admin rights
   - In Power BI Admin Portal → Tenant Settings, enable "Service principals can use Fabric administrator APIs"

### Local Development Installation

```bash
# Navigate to app directory
cd connectors/fabric-workspace-tagger

# Install dependencies
uv sync

# Download SDK components (Dapr configs)
uv run poe download-components

# Start Dapr and Temporal (in background)
uv run poe start-deps

# Run the app
uv run python main.py
```

The app will start a server on `http://localhost:8000`.

### Configuration

Create a workflow configuration JSON (or configure via Atlan UI when deploying):

```json
{
  "fabric_tenant_id": "00000000-0000-0000-0000-000000000000",
  "fabric_client_id": "11111111-1111-1111-1111-111111111111",
  "tag_namespace": "capacity",
  "capacity_tag_key": "capacity",
  "atlan_connection_qualified_name": "default/powerbi/1234567890",
  "workspace_filter_regex": "^(Manufacturing|Sales).*"
}
```

**Set the client secret** as an environment variable:

```bash
export FABRIC_CLIENT_SECRET="your-client-secret-here"
```

When deployed in Atlan, configure the secret via the app's secret store.

### Running the Workflow

**Via API (local)**:

```bash
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "fabric_tenant_id": "...",
    "fabric_client_id": "...",
    "tag_namespace": "capacity",
    "capacity_tag_key": "capacity",
    "atlan_connection_qualified_name": "default/powerbi/1234567890"
  }'
```

**Via pyatlan (scheduled)**:

```python
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.workflow import WorkflowSchedule

client = AtlanClient()

# Find the deployed workflow
workflow = client.workflow.find_by_type(
    prefix="fabric-workspace-tagger"
)[0]

# Schedule nightly at 2am UTC
schedule = WorkflowSchedule(
    cron_schedule="0 2 * * *",
    timezone="UTC"
)

client.workflow.add_schedule(
    workflow=workflow,
    workflow_schedule=schedule,
)
```

## Configuration Reference

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `fabric_tenant_id` | Yes | - | Azure AD tenant ID |
| `fabric_client_id` | Yes | - | Service principal client ID |
| `fabric_authority_url` | No | `https://login.microsoftonline.com` | Azure AD authority URL |
| `fabric_scope` | No | `https://analysis.windows.net/powerbi/api/.default` | OAuth scope for Power BI API |
| `tag_namespace` | Yes | - | Tag namespace managed by this app (e.g., `capacity`) |
| `capacity_tag_key` | Yes | - | Key for capacity tags (e.g., `capacity`) |
| `atlan_connection_qualified_name` | Yes | - | Qualified name of Power BI connection in Atlan |
| `workspace_filter_regex` | No | - | Optional regex to filter workspaces by name |

## Tag Naming Convention

Tags are applied in the format `key:value`:

- **Capacity tags**: `capacity:Fabric-Critical-01`
- **Pillar tags**: `pillar:Manufacturing`
- **Environment tags**: `env:prod`

The app uses **namespace-aware tag management**:
- Only tags in the configured namespace (plus `capacity`, `pillar`, `env`) are managed by the app
- Other tags on the workspace are preserved
- Stale tags in the managed namespace are removed on each run

## Customizing Tag Extraction

The default implementation in `fabric_client.py:_extract_tags_from_workspace()` uses simple naming heuristics:

```python
# Example: "Manufacturing BI" → {"pillar": "Manufacturing"}
if "Manufacturing" in workspace_name:
    tags["pillar"] = "Manufacturing"
```

**To customize**, edit `app/fabric_client.py` and implement your organization's logic:
- Parse workspace descriptions
- Call additional Fabric APIs for metadata
- Use custom attributes or naming conventions

## Cross-References

### Atlan Application SDK
- GitHub: [atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- Workflow patterns: `application_sdk.workflows.WorkflowInterface`
- Activities: `application_sdk.activities.ActivitiesInterface`
- Logger: `application_sdk.observability.logger_adaptor.get_logger`

### pyatlan SDK
- Docs: [developer.atlan.com](https://developer.atlan.com/)
- PowerBIWorkspace model: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- Managing tags: [developer.atlan.com/snippets/common-examples/tags](https://developer.atlan.com/snippets/common-examples/tags/)
- Search assets: `pyatlan.client.atlan.AtlanClient.asset.search()`

### Microsoft Fabric / Power BI APIs
- Power BI Admin API: [learn.microsoft.com/rest/api/power-bi/admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/)
- List workspaces: `GET /v1.0/myorg/admin/groups`
- List capacities: `GET /v1.0/myorg/admin/capacities`
- MSAL Python auth: [learn.microsoft.com/entra/msal/python](https://learn.microsoft.com/en-us/entra/msal/python/)

## Testing

```bash
# Run unit tests
uv run pytest tests/ -v

# Run with coverage
uv run coverage run -m pytest tests/
uv run coverage report
```

## Deployment

1. **Build the app image** using the Apps Framework build pipeline
2. **Deploy to Atlan** via the app marketplace or internal deployment
3. **Configure secrets** in the app's secret store:
   - `FABRIC_CLIENT_SECRET`
4. **Set up the workflow schedule** via Atlan UI or pyatlan
5. **Monitor execution** via Temporal UI and Atlan workflow logs

## Troubleshooting

### Authentication Failures

**Error**: `Token acquisition failed: AADSTS700016: Application with identifier '...' was not found in the directory`

**Fix**: Verify the `fabric_tenant_id` and `fabric_client_id` are correct.

---

**Error**: `AADSTS7000215: Invalid client secret provided`

**Fix**: Regenerate the client secret and update the `FABRIC_CLIENT_SECRET` environment variable.

---

### Workspace Not Found in Atlan

**Error**: `Workspace XYZ (ID: ...) not found in Atlan; skipping`

**Cause**: The Power BI connector in Atlan hasn't crawled this workspace yet, or the `atlan_connection_qualified_name` is incorrect.

**Fix**:
1. Verify the Power BI connector is configured and has run
2. Check the `atlan_connection_qualified_name` matches the connection in Atlan
3. Ensure the workspace exists in Atlan by searching for it manually

---

### No Tags Updated

**Symptom**: Workflow completes but reports `0 workspaces_updated`

**Causes**:
- Workspaces already have the correct tags (idempotent operation)
- Workspace filter regex is too restrictive
- Fabric API returned no workspaces

**Fix**:
- Check workflow logs for "No tag changes for workspace X"
- Review `workspace_filter_regex` if set
- Verify service principal has access to workspaces in Power BI

## License

Apache 2.0

## Support

For issues or questions, please contact the Atlan App Team at `connect@atlan.com`.

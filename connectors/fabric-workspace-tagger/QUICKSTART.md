# Quick Start Guide: Microsoft Fabric Workspace Tagger

This guide walks you through setting up and running the Fabric Workspace Tagger app in under 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.11 or 3.12 installed
- [ ] `uv` package manager installed ([astral.sh/uv](https://astral.sh/uv))
- [ ] Azure AD service principal with Power BI Admin API access
- [ ] Power BI connection already configured in Atlan
- [ ] Dapr CLI installed (for local dev only)
- [ ] Temporal CLI installed (for local dev only)

## Step 1: Azure AD Service Principal Setup (5 min)

### 1.1 Create App Registration

```bash
# Via Azure CLI (or use Azure Portal)
az ad app create \
  --display-name "Atlan-Fabric-Workspace-Tagger" \
  --sign-in-audience AzureADMyOrg

# Note the appId (client ID) and tenant ID from output
```

### 1.2 Create Client Secret

```bash
az ad app credential reset \
  --id <app-id> \
  --append

# Save the "password" value - you won't see it again!
```

### 1.3 Grant API Permissions

```bash
# Add Power BI Service permissions
az ad app permission add \
  --id <app-id> \
  --api 00000009-0000-0000-c000-000000000000 \
  --api-permissions \
    4ae1bf56-f562-4747-b7bc-2fa0874ed46f=Role \
    7f33e027-4039-419b-938e-2f8ca153e68e=Role

# Grant admin consent
az ad app permission admin-consent --id <app-id>
```

**Permissions granted**:
- `Tenant.Read.All`: Read tenant-wide Power BI metadata
- `Workspace.Read.All`: Read all Power BI workspaces

### 1.4 Configure Power BI Tenant Settings

1. Go to [Power BI Admin Portal](https://app.powerbi.com/admin-portal/tenantSettings)
2. Enable "Service principals can use Fabric administrator APIs"
3. Add your service principal to an allowed security group

## Step 2: Install and Run Locally (3 min)

```bash
# Navigate to app directory
cd connectors/fabric-workspace-tagger

# Install dependencies
uv sync

# Download Dapr components
uv run poe download-components

# Start Dapr + Temporal in background
uv run poe start-deps

# Set required environment variables
export FABRIC_CLIENT_SECRET="your-client-secret-from-step-1.2"

# Run the app
uv run python main.py
```

**Expected output**:
```
INFO: Starting Microsoft Fabric Workspace Tagger application
INFO: Starting Temporal worker...
INFO: Starting API server on port 8000...
INFO: Application started successfully
```

## Step 3: Configure and Run Workflow (2 min)

### 3.1 Prepare Configuration

Create `test_config.json`:

```json
{
  "fabric_tenant_id": "00000000-0000-0000-0000-000000000000",
  "fabric_client_id": "11111111-1111-1111-1111-111111111111",
  "tag_namespace": "capacity",
  "capacity_tag_key": "capacity",
  "atlan_connection_qualified_name": "default/powerbi/1234567890"
}
```

**How to find `atlan_connection_qualified_name`**:
1. Go to Atlan UI
2. Navigate to your Power BI connection
3. Click on any PowerBIWorkspace asset
4. Copy the `connectionQualifiedName` from the asset details

### 3.2 Trigger Workflow

```bash
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d @test_config.json
```

**Expected response**:
```json
{
  "workflow_id": "fabric-workspace-tag-sync-20260219-123456",
  "run_id": "abc123...",
  "status": "running"
}
```

### 3.3 Check Workflow Status

```bash
# Via Temporal UI (started by poe start-deps)
open http://localhost:8233

# Search for workflow ID from response
```

## Step 4: Verify Results in Atlan (1 min)

1. Go to Atlan UI
2. Search for a PowerBIWorkspace (e.g., "Manufacturing BI")
3. Check the **Tags** section
4. You should see new tags like:
   - `capacity:Fabric-Critical-01`
   - `pillar:Manufacturing` (if extracted from workspace name)

## Troubleshooting

### Error: "FABRIC_CLIENT_SECRET not found"

**Fix**: Export the environment variable before running:
```bash
export FABRIC_CLIENT_SECRET="your-secret-here"
```

### Error: "Token acquisition failed: AADSTS700016"

**Cause**: Invalid tenant ID or client ID

**Fix**: Double-check `fabric_tenant_id` and `fabric_client_id` in config

### Error: "Workspace not found in Atlan"

**Cause**: Power BI connector hasn't crawled this workspace yet

**Fix**:
1. Verify Power BI connector is running in Atlan
2. Check `atlan_connection_qualified_name` is correct
3. Wait for Power BI connector to complete a crawl

### No Tags Updated (0 workspaces_updated)

**Cause**: Workspaces already have correct tags (idempotent operation)

**Fix**: This is expected behavior on subsequent runs. Check workflow logs for "No tag changes for workspace X"

## Next Steps

### Schedule Nightly Runs

Once tested locally, schedule the workflow to run nightly:

```python
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.workflow import WorkflowSchedule

client = AtlanClient()

workflow = client.workflow.find_by_type(
    prefix="fabric-workspace-tagger"
)[0]

schedule = WorkflowSchedule(
    cron_schedule="0 2 * * *",  # 2am UTC
    timezone="UTC"
)

client.workflow.add_schedule(
    workflow=workflow,
    workflow_schedule=schedule,
)
```

### Customize Tag Extraction

Edit `app/fabric_client.py:_extract_tags_from_workspace()` to implement your organization's tag extraction logic:

```python
def _extract_tags_from_workspace(self, workspace: dict) -> dict[str, str]:
    tags = {}
    name = workspace.get("name", "")
    description = workspace.get("description", "")

    # Example: Parse description for project codes
    if match := re.search(r"Project: (\w+)", description):
        tags["project"] = match.group(1)

    return tags
```

### Deploy to Production

See [README.md](README.md) deployment section for:
- Building Docker image
- Deploying to Atlan
- Configuring secrets in app secret store

## Clean Up (Local Dev)

```bash
# Stop Dapr and Temporal
uv run poe stop-deps

# Remove temporal.db
rm temporal.db
```

## Support

- **Documentation**: See [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: Contact Atlan App Team at connect@atlan.com
- **App Framework**: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)

---

**Total setup time**: ~10 minutes
**First workflow run**: ~1-2 minutes (for 100 workspaces)

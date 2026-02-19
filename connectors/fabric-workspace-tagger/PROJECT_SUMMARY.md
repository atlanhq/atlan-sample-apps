# Project Summary: Microsoft Fabric Workspace Tagger

## Overview

This document summarizes the complete Atlan App Framework application built to synchronize Microsoft Fabric workspace metadata and tags to Atlan.

**Purpose**: Enable capacity-based governance and cost management for Zoetis Power BI workspaces by:
1. Tagging workspaces with their parent Fabric capacity
2. Applying custom tags based on organizational conventions (pillar, environment, etc.)
3. Running as a nightly scheduled workflow

## What Was Built

### Application Components

```
connectors/fabric-workspace-tagger/
├── app/
│   ├── __init__.py                    # Package initialization
│   ├── models.py                      # Pydantic models for config & data
│   ├── fabric_client.py               # Microsoft Fabric/Power BI API client
│   ├── activities.py                  # Temporal activities (fetch & update)
│   ├── workflow.py                    # Temporal workflow orchestration
│   └── templates/
│       └── workflow.json              # Workflow config schema for Atlan UI
├── tests/
│   ├── __init__.py
│   └── test_models.py                 # Unit tests for Pydantic models
├── main.py                            # App entry point (BaseApplication)
├── pyproject.toml                     # Dependencies & build config
├── Dockerfile                         # Container image definition
├── .gitignore                         # Git ignore rules
├── README.md                          # User documentation & setup guide
├── ARCHITECTURE.md                    # Technical architecture & design
├── QUICKSTART.md                      # 10-minute quick start guide
└── PROJECT_SUMMARY.md                 # This file
```

### Key Files & Cross-References

#### 1. **models.py** - Data Models

**Purpose**: Pydantic models for type-safe configuration and data payloads

**Key Models**:
- `AppConfig`: Workflow configuration (tenant ID, client ID, tag namespace, etc.)
- `FabricWorkspace`: Normalized workspace metadata from Fabric API
- `FabricCapacity`: Capacity metadata from Power BI Admin API
- `WorkspaceTagSyncResult`: Summary result of tag sync operation

**Cross-References**:
- Pydantic validation: [docs.pydantic.dev](https://docs.pydantic.dev/)
- Power BI Admin API schemas: [learn.microsoft.com/rest/api/power-bi/admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/)

---

#### 2. **fabric_client.py** - Microsoft Fabric API Client

**Purpose**: Authenticate to Azure AD and fetch workspace/capacity metadata

**Key Methods**:
- `_get_access_token()`: MSAL client credentials flow
- `list_capacities()`: GET /v1.0/myorg/admin/capacities
- `list_workspaces()`: GET /v1.0/myorg/admin/groups
- `_extract_tags_from_workspace()`: Customizable tag extraction logic

**Cross-References**:
- MSAL Python library: [learn.microsoft.com/entra/msal/python](https://learn.microsoft.com/en-us/entra/msal/python/)
- Power BI Admin - List Groups: [learn.microsoft.com/rest/api/power-bi/admin/groups-get-groups-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-groups-as-admin)
- Power BI Admin - List Capacities: [learn.microsoft.com/rest/api/power-bi/admin/get-capacities-as-admin](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/get-capacities-as-admin)
- Fabric Admin API (alternative): [learn.microsoft.com/rest/api/fabric/admin/workspaces](https://learn.microsoft.com/en-us/rest/api/fabric/admin/workspaces)

**Dependencies**:
- `msal>=1.28.0` (Azure AD authentication)
- `requests>=2.31.0` (HTTP client)

---

#### 3. **activities.py** - Temporal Activities

**Purpose**: Business logic for fetching Fabric data and updating Atlan tags

**Key Activities**:
- `get_workflow_args()`: Validates configuration
- `fetch_fabric_workspaces()`: Calls Fabric API, returns workspace list
- `update_atlan_workspace_tags()`: Searches Atlan, updates tags via pyatlan

**Cross-References**:
- App SDK Activities: `application_sdk.activities.ActivitiesInterface` ([github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk))
- Temporal activity decorator: `@activity.defn` ([docs.temporal.io](https://docs.temporal.io))
- pyatlan AtlanClient: [developer.atlan.com](https://developer.atlan.com/)
- PowerBIWorkspace model: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- Managing tags: [developer.atlan.com/snippets/common-examples/tags](https://developer.atlan.com/snippets/common-examples/tags/)

**Key Patterns**:
- **Workspace resolution**: Search by `qualifiedName` pattern, fallback to `name.keyword`
- **Namespace-aware tag update**: Remove stale managed tags, apply desired tags
- **Partial failure handling**: Continue processing on per-workspace errors

---

#### 4. **workflow.py** - Temporal Workflow

**Purpose**: Orchestrates activity execution with retry policies

**Workflow Steps**:
1. Validate configuration (`get_workflow_args`)
2. Fetch workspaces from Fabric (`fetch_fabric_workspaces`)
3. Update Atlan tags (`update_atlan_workspace_tags`)

**Cross-References**:
- App SDK Workflow: `application_sdk.workflows.WorkflowInterface` ([github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk))
- Temporal workflow decorator: `@workflow.defn`, `@workflow.run` ([docs.temporal.io/workflows](https://docs.temporal.io/workflows))
- Retry policies: `temporalio.common.RetryPolicy` ([docs.temporal.io/retry-policies](https://docs.temporal.io/retry-policies))

**Retry Configuration**:
```python
RetryPolicy(
    maximum_attempts=3,
    backoff_coefficient=2,
    initial_interval=timedelta(seconds=1),
)
```

---

#### 5. **main.py** - Application Entry Point

**Purpose**: Initialize and start the app using `BaseApplication`

**Startup Flow**:
1. Create `BaseApplication(name="fabric-workspace-tagger")`
2. Setup workflow and activities: `app.setup_workflow([(WorkflowClass, ActivitiesClass)])`
3. Start Temporal worker: `app.start_worker()`
4. Setup API server: `app.setup_server(workflow_class=...)`
5. Start server: `app.start_server()` (port 8000)

**Cross-References**:
- App SDK BaseApplication: `application_sdk.application.BaseApplication` ([github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk))
- Sample app structure: [github.com/atlanhq/atlan-sample-apps/tree/main/quickstart/polyglot](https://github.com/atlanhq/atlan-sample-apps/tree/main/quickstart/polyglot)

---

#### 6. **pyproject.toml** - Dependencies & Configuration

**Key Dependencies**:
- `atlan-application-sdk[pandas,tests,workflows]==2.3.1` - App Framework SDK
- `pyatlan>=2.0.0` - Atlan Python SDK
- `msal>=1.28.0` - Microsoft Authentication Library
- `requests>=2.31.0` - HTTP client
- `poethepoet` - Task runner

**Poe Tasks**:
- `poe start-deps` - Start Dapr + Temporal locally
- `poe stop-deps` - Stop local services
- `poe download-components` - Download Dapr component configs from SDK repo

**Cross-References**:
- Application SDK GitHub: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- pyatlan SDK: [developer.atlan.com](https://developer.atlan.com/)

---

#### 7. **workflow.json** - Configuration Schema

**Purpose**: JSON Schema for Atlan UI workflow configuration form

**Required Fields**:
- `fabric_tenant_id`: Azure AD tenant ID
- `fabric_client_id`: Service principal client ID
- `tag_namespace`: Tag namespace managed by app
- `capacity_tag_key`: Key for capacity tags
- `atlan_connection_qualified_name`: Power BI connection in Atlan

**Optional Fields**:
- `workspace_filter_regex`: Filter workspaces by name pattern
- `fabric_authority_url`: Custom Azure AD authority
- `fabric_scope`: Custom OAuth scope

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. Scheduler (Temporal Cron)                               │
│     - Nightly at 2am UTC                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. FabricWorkspaceTagSyncWorkflow                          │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Activity: get_workflow_args                           │ │
│  │   → Validate config (Pydantic)                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Activity: fetch_fabric_workspaces                     │ │
│  │   1. MSAL auth (client credentials)                   │ │
│  │   2. GET /admin/capacities                            │ │
│  │   3. GET /admin/groups                                │ │
│  │   4. Join workspace → capacity                        │ │
│  │   5. Extract custom tags (naming conventions)         │ │
│  │   → Returns: List[FabricWorkspace]                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Activity: update_atlan_workspace_tags                 │ │
│  │   For each workspace:                                 │ │
│  │   1. Search Atlan for PowerBIWorkspace by QN          │ │
│  │   2. Compute desired tags (capacity, pillar, env)     │ │
│  │   3. Namespace-aware tag merge                        │ │
│  │   4. Update via pyatlan (if changed)                  │ │
│  │   → Returns: WorkspaceTagSyncResult                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Result (Summary)                                        │
│     - total_workspaces: 100                                 │
│     - workspaces_updated: 95                                │
│     - workspaces_skipped: 4                                 │
│     - workspaces_failed: 1                                  │
│     - errors: ["Workspace X: timeout"]                      │
└─────────────────────────────────────────────────────────────┘
```

## External System Cross-References

### Microsoft Fabric / Power BI APIs

| API Endpoint | Purpose | Reference |
|-------------|---------|-----------|
| **POST** `/token` (MSAL) | Obtain OAuth access token | [MSAL Python](https://learn.microsoft.com/en-us/entra/msal/python/) |
| **GET** `/v1.0/myorg/admin/capacities` | List all capacities | [Admin API - Capacities](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/get-capacities-as-admin) |
| **GET** `/v1.0/myorg/admin/groups` | List all workspaces | [Admin API - Groups](https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-groups-as-admin) |
| **GET** `/v1/admin/workspaces` (Fabric) | Alternative Fabric API | [Fabric Admin API](https://learn.microsoft.com/en-us/rest/api/fabric/admin/workspaces) |

**Authentication**:
- Protocol: OAuth 2.0 client credentials flow
- Authority: `https://login.microsoftonline.com/{tenant_id}`
- Scope: `https://analysis.windows.net/powerbi/api/.default`
- Library: `msal.ConfidentialClientApplication`

---

### Atlan Metadata APIs (via pyatlan)

| Operation | Purpose | Reference |
|-----------|---------|-----------|
| **Search assets** | Find PowerBIWorkspace by qualifiedName | [pyatlan Search](https://developer.atlan.com/snippets/common-examples/search/) |
| **Update tags** | Add/remove assetTags on assets | [Managing Tags](https://developer.atlan.com/snippets/common-examples/tags/) |
| **Asset updater** | Partial update of asset properties | [PowerBIWorkspace.updater()](https://developer.atlan.com/models/entities/powerbiworkspace/) |
| **Search DSL** | Build search queries | `pyatlan.model.search.DSL`, `pyatlan.model.search.Term` |

**Key Models**:
- `PowerBIWorkspace`: [developer.atlan.com/models/entities/powerbiworkspace](https://developer.atlan.com/models/entities/powerbiworkspace/)
- `AtlanClient`: Main entry point for all Atlan API operations

---

### Atlan Application SDK

| Component | Purpose | Reference |
|-----------|---------|-----------|
| **BaseApplication** | App lifecycle management | [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk) |
| **WorkflowInterface** | Base workflow class | `application_sdk.workflows.WorkflowInterface` |
| **ActivitiesInterface** | Base activities class | `application_sdk.activities.ActivitiesInterface` |
| **Logger** | Structured logging | `application_sdk.observability.logger_adaptor.get_logger` |
| **Metrics** | OpenTelemetry metrics | `application_sdk.observability.metrics_adaptor.get_metrics` |
| **Traces** | Distributed tracing | `application_sdk.observability.traces_adaptor.get_traces` |

**Sample Apps**:
- Generic template: [github.com/atlanhq/atlan-sample-apps/tree/main/templates/generic](https://github.com/atlanhq/atlan-sample-apps/tree/main/templates/generic)
- Polyglot sample: [github.com/atlanhq/atlan-sample-apps/tree/main/quickstart/polyglot](https://github.com/atlanhq/atlan-sample-apps/tree/main/quickstart/polyglot)

---

### Temporal Workflow Engine

| Feature | Purpose | Reference |
|---------|---------|-----------|
| **Workflows** | Durable execution orchestration | [docs.temporal.io/workflows](https://docs.temporal.io/workflows) |
| **Activities** | Business logic units | [docs.temporal.io/activities](https://docs.temporal.io/activities) |
| **Retry Policies** | Automatic retry with backoff | [docs.temporal.io/retry-policies](https://docs.temporal.io/retry-policies) |
| **Schedules** | Cron-based workflow triggers | [docs.temporal.io/workflows#schedule](https://docs.temporal.io/workflows#schedule) |
| **Testing** | Workflow unit testing | [docs.temporal.io/develop/python/testing-suite](https://docs.temporal.io/develop/python/testing-suite) |

**Python SDK**: `temporalio` package

---

## Configuration & Deployment

### Local Development

**Prerequisites**:
- Python 3.11+, `uv` package manager
- Dapr CLI, Temporal CLI
- Azure AD service principal with Power BI Admin API access

**Setup**:
```bash
cd connectors/fabric-workspace-tagger
uv sync
uv run poe download-components
uv run poe start-deps
export FABRIC_CLIENT_SECRET="..."
uv run python main.py
```

**Reference**: [QUICKSTART.md](QUICKSTART.md)

---

### Production Deployment (Atlan)

**Build**:
```bash
docker build -t fabric-workspace-tagger:0.1.0 .
docker push registry.atlan.com/apps/fabric-workspace-tagger:0.1.0
```

**Deploy**:
1. Package as Atlan workflow package
2. Configure secrets in app secret store: `FABRIC_CLIENT_SECRET`
3. Configure workflow via Atlan UI (or API)
4. Set schedule: `0 2 * * *` (nightly at 2am UTC)

**Reference**: [README.md - Deployment](README.md#deployment)

---

### Scheduling (Nightly Runs)

**Via pyatlan**:
```python
from pyatlan.client.atlan import AtlanClient
from pyatlan.model.workflow import WorkflowSchedule

client = AtlanClient()
workflow = client.workflow.find_by_type(prefix="fabric-workspace-tagger")[0]
schedule = WorkflowSchedule(cron_schedule="0 2 * * *", timezone="UTC")
client.workflow.add_schedule(workflow=workflow, workflow_schedule=schedule)
```

**Reference**: [developer.atlan.com/snippets/workflows/manage/schedules](https://developer.atlan.com/snippets/workflows/manage/schedules/)

---

## Testing

### Unit Tests

**Run**:
```bash
uv run pytest tests/ -v
uv run coverage run -m pytest tests/
uv run coverage report
```

**Coverage**:
- `test_models.py`: Validates Pydantic model schemas

**Future**:
- Mock `FabricAPIClient` to test API response parsing
- Mock `AtlanClient` to test tag update logic
- End-to-end workflow tests using Temporal test framework

---

## Key Design Patterns

### 1. Namespace-Aware Tag Management

**Problem**: Multiple processes may tag the same assets

**Solution**: Only manage tags in specific namespaces (`capacity`, `pillar`, `env`); preserve other tags

**Implementation** (in `activities.py:_update_workspace_tags`):
```python
existing_tags = set(workspace.atlan_tags or [])
managed_tags = {t for t in existing_tags if t.split(":")[0] in ["capacity", "pillar", "env"]}
new_tags = (existing_tags - managed_tags) | desired_tags
```

---

### 2. Resilient Execution with Retries

**Configuration**:
```python
retry_policy = RetryPolicy(
    maximum_attempts=3,
    backoff_coefficient=2,  # Exponential backoff: 1s, 2s, 4s
    initial_interval=timedelta(seconds=1),
)
```

**Behavior**:
- Transient Fabric API failures (HTTP 429, 503) → automatic retry
- Partial failures (per-workspace errors) → continue processing, report in result
- Complete failures → workflow fails, visible in Temporal UI

---

### 3. Customizable Tag Extraction

**Default** (in `fabric_client.py:_extract_tags_from_workspace`):
```python
if "Manufacturing" in workspace_name:
    tags["pillar"] = "Manufacturing"
```

**Extensibility**:
- Parse workspace description field
- Call additional Fabric APIs for extended metadata
- Integrate with external CMDB or tagging service
- Use regex patterns from config

---

## Future Enhancements

1. **Native Capacity Assets**: Once Atlan adds `PowerBICapacity` / `FabricCapacity` asset types, update app to create/link capacities
2. **Tag Propagation**: Auto-propagate workspace tags to child datasets/reports
3. **Webhook Integration**: React to Fabric workspace creation events in real-time
4. **Custom Metadata**: Store capacity info as custom metadata (richer than tags)
5. **Parallel Updates**: Use `asyncio.gather()` for concurrent Atlan tag updates
6. **Advanced Tag Sources**: Leverage Fabric Lineage API for data-driven tags

---

## Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | User guide, setup, configuration | End users, admins |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical design, cross-references | Developers, architects |
| [QUICKSTART.md](QUICKSTART.md) | 10-minute getting started guide | New users |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | This file - complete reference | All stakeholders |

---

## Support & Contributions

- **Issues**: Contact Atlan App Team at `connect@atlan.com`
- **App Framework SDK**: [github.com/atlanhq/application-sdk](https://github.com/atlanhq/application-sdk)
- **Sample Apps**: [github.com/atlanhq/atlan-sample-apps](https://github.com/atlanhq/atlan-sample-apps)
- **pyatlan SDK**: [developer.atlan.com](https://developer.atlan.com/)

---

**Version**: 0.1.0
**Built for**: Zoetis capacity governance use case
**Framework**: Atlan Application SDK 2.3.1
**Last Updated**: 2026-02-19

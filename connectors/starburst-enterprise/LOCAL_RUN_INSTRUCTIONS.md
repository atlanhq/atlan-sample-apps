# Local Run Instructions — Starburst Enterprise Connector

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker Desktop | latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Dapr CLI | 1.13+ | `brew install dapr/tap/dapr-cli` (macOS) or [docs.dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/) |
| Temporal CLI | latest | `brew install temporal` (macOS) or [temporal.io/cli](https://docs.temporal.io/cli) |

### Platform-Specific Setup

- **macOS**: https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md
- **Linux**: https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md
- **Windows**: https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md

### Installing Temporal & Dapr CLIs (macOS)

```bash
# Install Temporal CLI
brew install temporal

# Install Dapr CLI
brew install dapr/tap/dapr-cli
```

### Initializing Dapr (first-time setup)

Dapr requires Docker to run its sidecar containers. Make sure **Docker Desktop is running** before proceeding.

```bash
dapr init
```

This pulls the required Docker containers (Redis, Zipkin, placement service) and sets up the Dapr runtime.

---

## Step 1: Install Dependencies

```bash
cd starburst-enterprise-connector

# Install Python dependencies via uv
uv sync
```

This reads `pyproject.toml` and installs:
- `atlan-application-sdk[daft,sqlalchemy,tests,workflows]==2.3.1`
- `trino>=0.330.0` (Trino DBAPI driver for SQL extraction)
- `httpx>=0.28.0` (REST API client)

## Step 2: Download Dapr Components

```bash
uv run poe download-components
```

This downloads the required Dapr component YAML files (state store, object store configs) from the Application SDK repository into a `components/` directory.

## Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Starburst Enterprise connection details:

```bash
# Required: SEP connection settings
SEP_HOST=your-sep-instance.example.com
SEP_PORT=443
SEP_HTTP_SCHEME=https
SEP_USER=your_username
SEP_PASSWORD=your_password
SEP_ROLE=sysadmin
SEP_CATALOG=system

# These defaults are usually fine for local development:
ATLAN_APP_HTTP_PORT=8000
ATLAN_DAPR_APP_PORT=3000
ATLAN_DAPR_HTTP_PORT=3500
ATLAN_DAPR_GRPC_PORT=50001
ATLAN_WORKFLOW_HOST=127.0.0.1
ATLAN_WORKFLOW_PORT=7233
ATLAN_WORKFLOW_UI_PORT=8233
ATLAN_TENANT_ID=default
ATLAN_WORKFLOW_NAMESPACE=default
ATLAN_APPLICATION_NAME=starburst-enterprise
ATLAN_LOCAL_DEVELOPMENT=true
```

## Step 4: Start Infrastructure Dependencies

Open a **separate terminal** and run:

```bash
uv run poe start-deps
```

This starts two background processes:
1. **Dapr sidecar** (port 3500) — state store and pub/sub
2. **Temporal dev server** (port 7233) — workflow orchestration

Wait until you see both services are ready before proceeding.

## Step 5: Run the Application

In your **main terminal**:

```bash
uv run main.py
```

The application starts:
1. A **Temporal worker** that listens for workflow execution requests
2. A **FastAPI server** on http://localhost:8000

## Step 6: Access the Application

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Web UI** | http://localhost:8000 | Configure connection and trigger extraction |
| **Temporal UI** | http://localhost:8233 | Monitor workflow execution, view activity logs |
| **Health Check** | http://localhost:8000/server/health | Verify server is running |

### Using the Web UI

1. Open http://localhost:8000
2. Enter your SEP credentials (host, port, username, password)
3. Click **Test Connection** to validate REST + SQL connectivity
4. Click **Start Extraction** to trigger the metadata workflow
5. Monitor progress in the Temporal UI at http://localhost:8233

---

## Running Tests

### Unit Tests (no SEP instance required)

```bash
uv run pytest tests/unit/ -v
```

### E2E Tests (requires running app + SEP instance)

First update `tests/e2e/test_sep_workflow/config.yaml` with your SEP credentials, then:

```bash
# With app already running (steps 4-5 above):
uv run pytest tests/e2e/ -v
```

---

## Output

Extracted metadata is written as JSON files to:

```
local/tmp/artifacts/apps/starburst-enterprise/workflows/<run-id>/raw/
```

Files produced per entity type:

| File Pattern | Entity Type | Source |
|-------------|-------------|--------|
| `domain_*.json` | Domains | REST API |
| `data_product_*.json` | Data Products | REST API |
| `dataset_*.json` | Datasets (Views + MVs) | REST API |
| `dataset_column_*.json` | Dataset Columns | REST API |
| `catalog_*.json` | Catalogs | SQL |
| `schema_*.json` | Schemas | SQL |
| `table_*.json` | Tables | SQL |
| `column_*.json` | Columns | SQL |

---

## Stopping

```bash
# Stop the application: Ctrl+C in the main terminal

# Stop infrastructure dependencies:
uv run poe stop-deps
```

---

## Troubleshooting

### `Failed to spawn: temporal` / `Failed to spawn: dapr`
The Temporal and/or Dapr CLIs are not installed. Install them first:
```bash
brew install temporal
brew install dapr/tap/dapr-cli
dapr init
```

### `dapr init` fails with "could not connect to docker"
Docker Desktop is either not running or the Docker socket is not exposed.

**Fix 1 — Enable the default Docker socket (recommended):**
1. Open **Docker Desktop** → **Settings** (gear icon)
2. Go to **Advanced**
3. Enable **"Allow the default Docker socket to be used"**
4. Click **Apply & Restart**
5. Retry `dapr init`

**Fix 2 — Symlink the socket manually:**
```bash
sudo ln -s "$HOME/.docker/run/docker.sock" /var/run/docker.sock
```
Then retry `dapr init`.

### `dapr init` fails with "unauthorized: incorrect username or password"
Docker is trying to authenticate with invalid cached credentials. Log out and retry:
```bash
docker logout
dapr init
```
No Docker Hub account is needed to pull the public images used by Dapr.

### `OPTIONS /workflows/v1/test_auth` returns 405 Method Not Allowed
This is a CORS issue — the browser sends a preflight `OPTIONS` request that the server doesn't handle. The fix is already applied in `main.py` via `CORSMiddleware`. If you see this error, make sure you're running the latest version of `main.py` that includes the CORS middleware setup.

### "Connection refused" on port 7233
Temporal server hasn't started yet. Wait a few seconds after `poe start-deps`.

### "Failed to connect" in Dapr
Ensure Dapr is initialized: `dapr init` (first-time setup only).

### SQL query timeout
Large catalogs (many schemas/tables) may take longer. The default timeout is 60 seconds per query. Increase it in `sql_client.py` if needed.

### UI session login warning
If you see "UI login returned status 401", the UI API proxy may require different credentials. The connector falls back to the raw REST API automatically — core fields (name, description, status, views, columns) are still extracted. Only supplementary fields (type/visibility) would be missing.

---

## Project Structure

```
starburst-enterprise-connector/
├── app/
│   ├── rest_client.py      # SEP REST API + UI session client
│   ├── sql_client.py       # Trino DBAPI SQL client
│   ├── handler.py          # Hybrid handler (REST + SQL)
│   ├── activities.py       # Temporal activities (extraction tasks)
│   ├── workflows.py        # Workflow orchestration (parallel streams)
│   ├── transformer.py      # Metadata → Atlan entity format
│   └── sql/                # SQL query templates
├── frontend/               # Web UI (HTML/CSS/JS)
├── models/                 # Atlan entity type definitions
├── tests/
│   ├── unit/               # Offline unit tests
│   └── e2e/                # Full integration tests
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies & task runner config
└── .env.example            # Environment variable template
```

## Extraction Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Temporal Workflow                      │
│                                                          │
│  1. get_workflow_args → Retrieve config from state store │
│  2. preflight_check  → Validate REST + SQL connectivity  │
│  3. Parallel fan-out:                                    │
│     ┌────────────────────┐  ┌──────────────────────────┐ │
│     │ REST Stream        │  │ SQL Stream               │ │
│     │ ├─ fetch_domains   │  │ ├─ fetch_catalogs        │ │
│     │ ├─ fetch_products  │  │ └─ parallel:             │ │
│     │ └─ extract_datasets│  │    ├─ fetch_schemas      │ │
│     │    + columns       │  │    ├─ fetch_tables       │ │
│     └────────────────────┘  │    └─ fetch_columns      │ │
│                             └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

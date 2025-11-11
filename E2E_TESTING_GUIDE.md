# E2E Testing Guide

This guide explains how to run end-to-end (e2e) tests locally for all apps in the `atlan-sample-apps` repository.

## Prerequisites

Before running e2e tests, ensure you have the following installed:

1. **Python 3.11+**
2. **[uv](https://docs.astral.sh/uv/)** package manager
3. **[Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)** (version 1.16.2)
4. **[Temporal CLI](https://docs.temporal.io/cli)**

### Installation Quick Links

- **macOS Setup**: [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- **Linux Setup**: [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- **Windows Setup**: [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## General Setup Steps

For each app you want to test, follow these steps:

### 1. Navigate to the App Directory

```bash
cd <app-directory>
# Example: cd quickstart/ai_giphy
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Download Dapr Components

```bash
uv run poe download-components
```

This downloads the required Dapr component YAML files (objectstore, statestore, etc.) from the application-sdk repository.

### 4. Start Dependencies (Dapr & Temporal)

In a **separate terminal**, start the required services:

```bash
uv run poe start-deps
```

This command starts:
- **Dapr** sidecar on port 3500 (HTTP) and 50001 (gRPC)
- **Temporal** server on port 7233 (gRPC) with UI on port 8233

> **Note**: Keep this terminal running while tests are executing. The services need to be running for the tests to work.

### 5. Start the Application

In **another terminal**, start the application:

```bash
# Set required environment variables (if needed)
export ATLAN_LOCAL_DEVELOPMENT=true
export ATLAN_APPLICATION_NAME=<app-name>

# Start the application
uv run main.py
```

The application typically runs on `http://localhost:8000`.

> **Note**: Keep this terminal running as well. The application must be running for the e2e tests to connect to it.

### 6. Run E2E Tests

In a **third terminal**, navigate to the app directory and run:

```bash
cd <app-directory>
uv run pytest tests/e2e -v --log-cli-level=INFO
```

Or run a specific test:

```bash
uv run pytest tests/e2e/test_<workflow_name>/test_<workflow_name>.py -v
```

## App-Specific Instructions

### Quickstart Apps

#### 1. AI Giphy (`quickstart/ai_giphy`)

**Additional Setup:**
- Create a `.env` file with:
  - `GIPHY_API_KEY`
  - SMTP credentials (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER)
  - Azure OpenAI credentials (APP_AZURE_OPENAI_API_KEY, APP_AZURE_OPENAI_API_VERSION, APP_AZURE_OPENAI_ENDPOINT, APP_AZURE_OPENAI_DEPLOYMENT_NAME)

**Run Tests:**
```bash
cd quickstart/ai_giphy
uv run pytest tests/e2e/test_ai_giphy_workflow -v --log-cli-level=INFO
```

#### 2. Giphy (`quickstart/giphy`)

**Run Tests:**
```bash
cd quickstart/giphy
uv run pytest tests/e2e/test_giphy_workflow -v --log-cli-level=INFO
```

#### 3. Hello World (`quickstart/hello_world`)

**Run Tests:**
```bash
cd quickstart/hello_world
uv run pytest tests/e2e/test_hello_world_workflow -v --log-cli-level=INFO
```

#### 4. Polyglot (`quickstart/polyglot`)

**Run Tests:**
```bash
cd quickstart/polyglot
uv run pytest tests/e2e/test_polyglot_workflow -v --log-cli-level=INFO
```

### Connector Apps

#### 1. Anaplan (`connectors/anaplan`)

**Additional Setup:**
- Configure credentials in `tests/e2e/test_anaplan_workflow/config.yaml`

**Run Tests:**
```bash
cd connectors/anaplan
uv run pytest tests/e2e/test_anaplan_workflow -v --log-cli-level=INFO
```

#### 2. MySQL (`connectors/mysql`)

**Additional Setup:**
- Configure database credentials in `tests/e2e/test_mysql_workflow/config.yaml`
- Ensure MySQL database is accessible

**Run Tests:**
```bash
cd connectors/mysql
uv run pytest tests/e2e/test_mysql_workflow -v --log-cli-level=INFO
```

### Utility Apps

#### 1. Asset Descriptor Reminder (`utilities/asset_descriptor_reminder`)

**Run Tests:**
```bash
cd utilities/asset_descriptor_reminder
uv run pytest tests/e2e -v --log-cli-level=INFO
```

#### 2. Freshness Monitor (`utilities/freshness_monitor`)

**Run Tests:**
```bash
cd utilities/freshness_monitor
uv run pytest tests/e2e -v --log-cli-level=INFO
```

#### 3. Workflows Observability (`utilities/workflows_observability`)

**Run Tests:**
```bash
cd utilities/workflows_observability
uv run pytest tests/e2e -v --log-cli-level=INFO
```

### Template Apps

#### 1. Generic Template (`templates/generic`)

**Run Tests:**
```bash
cd templates/generic
uv run pytest tests/e2e/test_generic_workflow -v --log-cli-level=INFO
```

## Test Execution Order

E2E tests follow a specific execution order (enforced by `@pytest.mark.order`):

1. `test_health_check` - Verifies server is running
2. `test_auth` - Tests authentication/connection
3. `test_metadata` - Tests metadata retrieval
4. `test_preflight_check` - Tests preflight validation
5. `test_run_workflow` - Executes the full workflow
6. `test_data_validation` - Validates extracted data (if applicable)
7. Additional custom tests (order > 6)

## Running All Tests for an App

To run all tests (unit + e2e) for an app:

```bash
cd <app-directory>
uv run pytest tests/ -v
```

To run only e2e tests:

```bash
uv run pytest tests/e2e -v
```

To run with coverage:

```bash
uv run coverage run -m pytest tests/e2e -v
uv run coverage report
```

## Troubleshooting

### Issue: Tests fail with "Connection refused"

**Solution:**
- Ensure the application is running (`uv run main.py`)
- Check that the application is listening on `http://localhost:8000`
- Verify the `server_host` in the test config file matches the running application

### Issue: Tests fail with "Dapr connection error"

**Solution:**
- Ensure Dapr is running (`uv run poe start-deps`)
- Check Dapr is listening on port 3500: `curl http://localhost:3500/v1.0/healthz`
- Verify components are downloaded in the `components/` directory

### Issue: Tests fail with "Temporal connection error"

**Solution:**
- Ensure Temporal is running (`uv run poe start-deps`)
- Check Temporal UI is accessible: `http://localhost:8233`
- Verify Temporal server is running: `temporal workflow list`

### Issue: Port already in use

**Solution:**
- Stop existing services: `uv run poe stop-deps`
- Kill processes manually:
  ```bash
  lsof -ti:3000,3500,7233,50001,8000,8233 | xargs kill -9
  ```

### Issue: Tests timeout

**Solution:**
- Increase workflow timeout in test class:
  ```python
  workflow_timeout = 3600  # seconds
  ```
- Check application logs for errors
- Verify external dependencies (APIs, databases) are accessible

### Issue: Missing environment variables

**Solution:**
- Create a `.env` file in the app directory
- Check the app's README.md for required environment variables
- Ensure all required credentials are configured

## Test Configuration

Each e2e test has a `config.yaml` file that contains:

- `test_workflow_args`: Credentials, metadata, and connection details
- `test_name`: Unique identifier for the test
- `server_config`: Server host and version
- `expected_api_responses`: Expected responses for validation

Example config structure:
```yaml
test_workflow_args:
  credentials: {}
  metadata: {}
  connection:
    connection_name: "test_connection"
    connection_qualified_name: "default/app/test"
test_name: "test_workflow_name"
server_config:
  server_host: "http://localhost:8000"
  server_version: "workflows/v1"
expected_api_responses:
  auth:
    success: true
    message: "Authentication successful"
```

## Cleanup

After running tests:

1. Stop the application (Ctrl+C in the terminal running `main.py`)
2. Stop dependencies:
   ```bash
   uv run poe stop-deps
   ```
3. Clean up test artifacts (optional):
   ```bash
   rm -rf local/dapr/objectstore/artifacts
   rm -f temporal.db
   ```

## Additional Resources

- [Application SDK Test Framework Documentation](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/guides/test-framework.md)
- [Temporal Documentation](https://docs.temporal.io/)
- [Dapr Documentation](https://docs.dapr.io/)

## Quick Reference: Running Tests for All Apps

Here's a quick script to test all apps (run from repository root):

```bash
#!/bin/bash

APPS=(
  "quickstart/ai_giphy"
  "quickstart/giphy"
  "quickstart/hello_world"
  "quickstart/polyglot"
  "connectors/anaplan"
  "connectors/mysql"
  "utilities/asset_descriptor_reminder"
  "utilities/freshness_monitor"
  "utilities/workflows_observability"
  "templates/generic"
)

for app in "${APPS[@]}"; do
  echo "========================================="
  echo "Testing: $app"
  echo "========================================="
  cd "$app" || exit
  if [ -d "tests/e2e" ]; then
    uv run pytest tests/e2e -v --tb=short || echo "Tests failed for $app"
  else
    echo "No e2e tests found for $app"
  fi
  cd - || exit
done
```

Save this as `run_all_e2e_tests.sh`, make it executable (`chmod +x run_all_e2e_tests.sh`), and run it:

```bash
./run_all_e2e_tests.sh
```

> **Note**: Make sure to start dependencies and the application for each app before running its tests.


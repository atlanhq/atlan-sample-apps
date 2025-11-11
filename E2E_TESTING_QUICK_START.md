# E2E Testing Quick Start

## Quick Reference

### Prerequisites Check
```bash
# Check if all tools are installed
./run_e2e_tests.sh --check
```

### List All Apps with E2E Tests
```bash
./run_e2e_tests.sh --list
```

### Setup a Single App
```bash
# Setup (install deps, download components)
./run_e2e_tests.sh --setup quickstart/ai_giphy
```

### Run Tests for a Single App

**Step 1: Setup the app** (if not done already)
```bash
cd quickstart/ai_giphy
uv sync
uv run poe download-components
```

**Step 2: Start dependencies** (in Terminal 1)
```bash
cd quickstart/ai_giphy
uv run poe start-deps
```

**Step 3: Start the application** (in Terminal 2)
```bash
cd quickstart/ai_giphy
export ATLAN_LOCAL_DEVELOPMENT=true
export ATLAN_APPLICATION_NAME=ai-giphy
uv run main.py
```

**Step 4: Run tests** (in Terminal 3)
```bash
cd quickstart/ai_giphy
uv run pytest tests/e2e -v --log-cli-level=INFO
```

Or use the helper script:
```bash
./run_e2e_tests.sh quickstart/ai_giphy
```

### Run Tests for All Apps
```bash
./run_e2e_tests.sh --all
```

## Common Commands

### Stop Services
```bash
cd <app-directory>
uv run poe stop-deps
```

### Check Service Status
```bash
# Check Dapr
curl http://localhost:3500/v1.0/healthz

# Check Temporal UI
open http://localhost:8233

# Check Application
curl http://localhost:8000
```

### Clean Up
```bash
# Stop all services
lsof -ti:3000,3500,7233,50001,8000,8233 | xargs kill -9

# Remove test artifacts
rm -rf local/dapr/objectstore/artifacts
rm -f temporal.db
```

## Test Configuration

Each app's e2e tests use a `config.yaml` file located at:
```
<app-directory>/tests/e2e/test_<workflow_name>/config.yaml
```

Edit this file to customize test parameters, credentials, and expected responses.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure app is running on port 8000 |
| Dapr connection error | Start Dapr: `uv run poe start-deps` |
| Temporal connection error | Start Temporal: `uv run poe start-deps` |
| Port already in use | Stop services: `uv run poe stop-deps` |
| Tests timeout | Increase `workflow_timeout` in test class |
| Missing env vars | Create `.env` file (check app README) |

## App-Specific Notes

### Quickstart Apps
- **ai_giphy**: Requires `.env` with Giphy API key, SMTP, and Azure OpenAI credentials
- **giphy**: Requires Giphy API key
- **hello_world**: No additional setup needed
- **polyglot**: Requires Java runtime

### Connector Apps
- **anaplan**: Configure credentials in `config.yaml`
- **mysql**: Requires accessible MySQL database

### Utility Apps
- All utilities follow standard setup process

## Full Documentation

For detailed information, see [E2E_TESTING_GUIDE.md](./E2E_TESTING_GUIDE.md)


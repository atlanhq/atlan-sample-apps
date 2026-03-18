# 📊 Demo File Summary

A minimal demonstration app that reads JSON input containing records with status fields and produces a summary with counts by status.

## Overview

This app demonstrates:
- Reading JSON input from object store
- Processing data with workflows and activities
- Writing JSON output back to object store
- Simple status counting and summarization

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)

### Installation Guides
- [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Download required components:**
   ```bash
   uv run poe download-components
   ```

2. **Start dependencies (in separate terminal):**
   ```bash
   uv run poe start-deps
   ```

3. **Run the application:**
   ```bash
   uv run main.py
   ```

**Access the application:**
- **Web Interface**: http://localhost:8000
- **Temporal UI**: http://localhost:8233

## How It Works

### Input Format

The app expects a JSON file with an array of records, each containing a `status` field:

```json
[
  {"id": 1, "status": "completed"},
  {"id": 2, "status": "pending"},
  {"id": 3, "status": "completed"},
  {"id": 4, "status": "failed"},
  {"id": 5, "status": "pending"}
]
```

### Output Format

The app produces a summary JSON with total count and status breakdown:

```json
{
  "total_records": 5,
  "status_counts": {
    "completed": 2,
    "pending": 2,
    "failed": 1
  }
}
```

### Configuration

When running the workflow, provide these parameters:
- `input_file`: Path to input JSON file in object store (default: `input/records.json`)
- `output_file`: Path where summary will be written (default: `output/summary.json`)

## Running Tests

### E2E Tests

1. **Prepare test data:**

   Create a test input file at `./local/dapr/objectstore/artifacts/apps/default/workflows/input/test_records.json`:

   ```json
   [
     {"id": 1, "status": "active"},
     {"id": 2, "status": "active"},
     {"id": 3, "status": "inactive"}
   ]
   ```

2. **Run tests:**
   ```bash
   uv run pytest tests/e2e/
   ```

### All Tests

```bash
uv run pytest
```

## Development

### Stop Dependencies
```bash
uv run poe stop-deps
```

### Project Structure
```
demo_file_summary/
├── app/                # Core application logic
│   ├── activities.py   # Status counting activity
│   └── workflow.py     # Workflow orchestration
├── frontend/           # Frontend assets (minimal)
│   ├── static/        # Static files
│   └── templates/     # HTML templates
├── tests/              # Test files
│   ├── e2e/           # End-to-end tests
│   └── unit/          # Unit tests
├── main.py            # Application entry point
├── pyproject.toml     # Dependencies and config
└── README.md          # This file
```

## Learning Resources
- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)

## Contributing
We welcome contributions! Please feel free to submit a Pull Request.

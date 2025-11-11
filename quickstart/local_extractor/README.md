# 📊 Local Extractor

A simple extractor application that extracts and transforms Table metadata from JSON files. Built with the Atlan Application SDK and Temporal.

## Overview

This application demonstrates how to build a metadata extractor that:
- Reads Table metadata from JSON files
- Transforms the data into Atlan-compatible format
- Processes owner users and groups
- Outputs transformed metadata to JSON files

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

> [!TIP]
> Want to containerize this app? See the [Build Docker images](https://github.com/atlanhq/atlan-sample-apps/tree/main/README.md#build-docker-images) section in the repository root README for unified build and run instructions.

## Features

- **JSON Metadata Extraction**: Reads Table metadata from JSON input files
- **Data Transformation**: Transforms raw metadata into Atlan-compatible format
- **Owner Processing**: Handles owner users and groups (supports newline-separated values)
- **Workflow Management**: Leverages Temporal for robust workflow orchestration
- **Simple UI**: Web interface to trigger extraction workflows

## Input Format

The application expects JSON input files with the following structure:

```json
[
  {
    "Type": "Table",
    "Name": "example_table",
    "Display_Name": "Example Table",
    "Description": "Table description",
    "User_Description": "User-provided description",
    "Owner_Users": "user1\nuser2",
    "Owner_Groups": "group1\ngroup2",
    "Certificate_Status": "VERIFIED",
    "Schema_Name": "public",
    "Database_Name": "example_db"
  }
]
```

## Output Format

The application outputs transformed metadata in the following format:

```json
{
  "typeName": "Table",
  "name": "example_table",
  "displayName": "Example Table",
  "description": "Table description",
  "userDescription": "User-provided description",
  "ownerUsers": ["user1", "user2"],
  "ownerGroups": ["group1", "group2"],
  "certificateStatus": "VERIFIED",
  "schemaName": "public",
  "databaseName": "example_db"
}
```

## Development

### Stop Dependencies
```bash
uv run poe stop-deps
```

###Run tests
```bash
uv run pytest
```


### Project Structure

```
local_extractor/
├── app/                    # Core application logic
│   ├── activities.py       # Temporal activities (extraction and transformation)
│   ├── client.py           # File handling client
│   ├── handler.py          # SDK handler for workflow coordination
│   ├── workflow.py         # Temporal workflow definition
│   └── frontend/           # Frontend configuration
│       └── workflow.json   # Workflow configuration
├── components/             # Dapr component configurations
├── frontend/              # Frontend assets
│   ├── static/            # Static files (CSS, JS)
│   ├── templates/         # HTML templates
│   └── config.json        # Frontend configuration
├── local/                 # Local data storage
├── tests/                 # Test files
├── main.py                # Application entry point
├── pyproject.toml         # Dependencies and config
└── README.md              # This file
```

## Learning Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs) (Refer to the SDK version you are using)
- [Dapr Documentation](https://docs.dapr.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)


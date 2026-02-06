# Atlan Connector Template

A template for building metadata connectors on the Atlan Application SDK.

## Quick Start

```bash
# Install dependencies
uv sync

# Download SDK components
uv run poe download-components

# Start Temporal and Dapr
uv run poe start-deps

# Run the connector
uv run python main.py
```

## Project Structure

```
├── main.py                 # Application entry point
├── app/
│   ├── clients.py          # API client for your data source
│   ├── handlers.py         # FastAPI handlers for UI
│   ├── activities.py       # Temporal activities (extract, transform, write)
│   ├── workflows.py        # Temporal workflow orchestration
│   ├── transformers/
│   │   ├── __init__.py     # Transformer setup
│   │   └── resource.yaml   # Entity transformation template
│   └── templates/
│       ├── credential.json # UI credential form config
│       └── workflow.json   # UI workflow wizard config
└── frontend/static/        # App playground UI
```

## Customization Guide

### 1. Update Client (`app/clients.py`)

Implement your data source API client:
- `load()` - Extract credentials and setup authentication
- `fetch_metadata()` - Fetch data from your source
- `verify_connection()` - Test connectivity

### 2. Update Activities (`app/activities.py`)

Customize the extraction and transformation logic:
- `extract_metadata` - Call your client to fetch data
- `transform_metadata` - Convert to Atlan format
- `write_output` - Write JSON-L files

### 3. Update Transformer (`app/transformers/`)

Define entity mappings in YAML templates:
- Create a `.yaml` file for each entity type
- Map source fields to Atlan attributes
- Register types in `__init__.py`

### 4. Update UI Config (`app/templates/`)

Configure the UI forms:
- `credential.json` - Credential input fields
- `workflow.json` - Workflow wizard steps

## Output Format

The connector outputs JSON-L files:

```json
{"typeName": "TemplateResource", "attributes": {"name": "...", "qualifiedName": "..."}}
```

# Extractor App 📊

A simple and minimal extractor application built using the Atlan Application SDK that reads Table asset metadata from JSON files and produces transformed data files.

## Overview

The Extractor App demonstrates the core capabilities of the Atlan Application SDK:
- **Data Extraction**: Reads JSON files containing Table asset information
- **Data Transformation**: Converts raw metadata into a standardized format
- **Workflow Orchestration**: Uses Temporal workflows for reliable processing
- **SDK Integration**: Showcases proper handler/client pattern implementation

## Features

- ✅ **Simple JSON File Processing**: Reads Table asset metadata from local JSON files
- ✅ **Data Transformation**: Converts raw data into standardized Table asset format
- ✅ **Error Handling**: Robust error handling with detailed logging
- ✅ **Web Interface**: Clean, modern UI for easy interaction
- ✅ **Workflow Monitoring**: Integration with Temporal UI for process monitoring
- ✅ **Preflight Checks**: Validates file access and JSON parsing capabilities

## Quick Start

### Prerequisites

- Python 3.11+
- uv (Python package manager)
- Dapr and Temporal (for local development)

### Installation

1. **Clone and navigate to the extractor app:**
   ```bash
   cd quickstart/extractor
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start dependencies (Dapr + Temporal):**
   ```bash
   uv run poe start-deps
   ```

4. **Run the application:**
   ```bash
   uv run python main.py
   ```

5. **Access the web interface:**
   - Open http://localhost:3000 in your browser
   - Use the default input file: `extractor-app-input-table.json`

## Usage

### Web Interface

1. **Input File**: Specify the path to your JSON file containing Table asset data
2. **Output File**: Optionally specify where to save the transformed data (auto-generated if empty)
3. **Extract & Transform**: Click the button to start the extraction workflow

### Input Format

The app expects JSON files with Table asset information in this format:

```json
[
  {
    "Type": "Table",
    "Name": "CUSTOMER",
    "Display_Name": "Customer",
    "Description": "Staging table for invoice data.",
    "User_Description": "",
    "Owner_Users": "jsmith\njdoe",
    "Owner_Groups": "",
    "Certificate_Status": "VERIFIED",
    "Schema_Name": "PEOPLE",
    "Database_Name": "TEST_DB"
  }
]
```

### Output Format

The transformed data follows a standardized structure:

```json
[
  {
    "asset_type": "Table",
    "name": "CUSTOMER",
    "display_name": "Customer",
    "description": "Staging table for invoice data.",
    "user_description": "",
    "owners": {
      "users": ["jsmith", "jdoe"],
      "groups": []
    },
    "certification": {
      "status": "VERIFIED"
    },
    "schema": {
      "name": "PEOPLE",
      "database": "TEST_DB"
    },
    "metadata": {
      "source": "extractor_app",
      "extracted_at": "2024-01-01T00:00:00Z"
    }
  }
]
```

## Architecture

The app follows the Atlan Application SDK patterns:

```
Frontend (HTML/CSS/JS)
    ↓
Application SDK (FastAPI)
    ↓
ExtractorHandler (SDK Interface)
    ↓
ExtractorClient (File Operations)
    ↓
Temporal Workflow (Orchestration)
    ↓
ExtractorActivities (Business Logic)
```

### Key Components

- **`main.py`**: Application entrypoint and SDK initialization
- **`app/workflow.py`**: Temporal workflow orchestration
- **`app/activities.py`**: Business logic activities
- **`app/handler.py`**: SDK interface implementation
- **`app/client.py`**: File operations and data transformation
- **`frontend/`**: Web interface (HTML, CSS, JavaScript)

## Development

### Running Tests

```bash
uv run pytest
```

### Code Structure

```
extractor/
├── app/
│   ├── __init__.py
│   ├── activities.py      # Temporal activities
│   ├── client.py         # File operations
│   ├── handler.py        # SDK interface
│   └── workflow.py       # Temporal workflow
├── frontend/
│   ├── static/
│   │   ├── script.js     # Frontend JavaScript
│   │   └── styles.css    # Frontend CSS
│   └── templates/
│       └── index.html    # Frontend HTML
├── main.py              # Application entrypoint
├── pyproject.toml       # Dependencies
├── extractor-app-input-table.json  # Sample input file
└── README.md            # This file
```

## Monitoring

- **Temporal UI**: http://localhost:8080 - Monitor workflow execution
- **Application Logs**: Check console output for detailed processing logs
- **Health Check**: http://localhost:3000/health - Application health status

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure the input JSON file exists and path is correct
2. **JSON Parse Error**: Verify the input file contains valid JSON
3. **Permission Denied**: Check file read/write permissions
4. **Workflow Not Starting**: Verify Dapr and Temporal are running

### Logs

Check the application logs for detailed error information:
- Console output shows workflow execution details
- Temporal UI provides workflow history and debugging
- File system errors are logged with full context

## Contributing

This is a sample application demonstrating Atlan Application SDK capabilities. For production use, consider:

- Adding input validation and sanitization
- Implementing proper error recovery mechanisms
- Adding comprehensive test coverage
- Enhancing security measures
- Adding configuration management

## License

Apache-2.0

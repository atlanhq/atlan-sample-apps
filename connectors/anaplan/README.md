# 📈 Anaplan App

A powerful application that extracts metadata from Anaplan instances and transforms it into a standardized format. Built with Application SDK for robust workflow management.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)
- Anaplan instance access

### Installation Guides
- [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Download required components:**
   ```bash
   uv run poe download-components
   ```

2. **Set up environment variables (see .env.example)**

3. **Start dependencies (in separate terminal):**
   ```bash
   uv run poe start-deps
   ```

4. **Run the application:**
   ```bash
   uv run main.py
   ```

**Access the application:**
- **Web Interface**: http://localhost:8000
- **Temporal UI**: http://localhost:8233

## Features

- Automated metadata extraction from Anaplan instances
- Structured workflow for metadata extraction and transformation
- Real-time workflow status tracking
- Robust error handling and retry mechanisms
- Standardized metadata transformation

## Project Structure

```mermaid
graph TD
    A[main.py] --> B[app/workflows]
    A --> C[app/activities]
    A --> D[app/transformers]
    A --> E[app/clients]
    A --> F[app/handlers]
    B --> C
    C --> E
    D --> E
    F --> E
```

```
anaplan/
├── app/                # Core application logic
│   ├── activities/     # Metadata extraction activities
│   ├── clients/        # Anaplan client implementations
│   ├── handlers/       # FastAPI response handlers
│   ├── transformers/   # Metadata transformation logic
│   └── workflows/      # Workflow definitions and orchestration
├── components/         # Dapr components (auto-downloaded)
├── frontend/           # Web interface assets
├── deploy/            # Installation and deployment files
├── local/              # Local data storage
├── tests/              # Unit and end-to-end tests
├── main.py             # Application entry point and initialization
├── pyproject.toml      # Dependencies and config
└── README.md           # This file
```

## Development

### Stop Dependencies
```bash
uv run poe stop-deps
```

### Run Tests

> [!NOTE]
> Make sure you have a `.env` file that matches the [.env.example](.env.example) file in this directory.

#### Unit Tests
```bash
uv run pytest connectors/anaplan/tests/unit
```

#### End-to-End Tests
Make sure to have these environment variables set:
```bash
export E2E_ANAPLAN_HOST=your-anaplan-host.com
export E2E_ANAPLAN_USERNAME=your-anaplan-username
export E2E_ANAPLAN_PASSWORD=your-anaplan-password
```
Then run the following command:
```bash
uv run pytest connectors/anaplan/tests/e2e
```

## Workflow Process

1. **Initialization**: The application sets up the Anaplan client and workflow components
2. **Preflight Check**: Validates Anaplan connectivity and permissions
3. **Metadata Extraction**: Fetches metadata from Anaplan instance
4. **Transformation**: Converts raw metadata into standardized format
5. **Output**: Saves the transformed metadata to specified location

## Learning Resources

- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Anaplan API Documentation](https://anaplan.docs.apiary.io/)
- [Python FastAPI Documentation](https://fastapi.tiangolo.com/)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

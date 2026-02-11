# Starburst Enterprise (SEP) Connector

A metadata extraction connector for **Starburst Enterprise (SEP)** built with the Atlan Application SDK. Uses a hybrid extraction approach combining REST API and SQL queries.

## Architecture

This connector uses two parallel extraction streams:

| Stream | Objects | Mechanism |
|--------|---------|-----------|
| **REST API** | Domains, Data Products, Datasets, Dataset Columns | SEP REST API (`/api/v1/dataProduct/`) |
| **SQL** | Catalogs, Schemas, Tables, Views, Columns | Trino `INFORMATION_SCHEMA` via `trino` Python driver |

**Key relationship**: Data Products (REST) map 1:1 to Schemas (SQL). Datasets (REST) map to Views/Materialized Views (SQL).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)
- Access to a Starburst Enterprise instance

### Installation Guides
- [macOS Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows Setup Guide](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Download required components:**
   ```bash
   uv run poe download-components
   ```

2. **Set up environment variables** (copy and edit `.env.example`):
   ```bash
   cp .env.example .env
   # Edit .env with your SEP connection details
   ```

3. **Start dependencies** (in a separate terminal):
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

## Project Structure

```
starburst-enterprise/
├── app/
│   ├── rest_client.py     # SEP REST API client (Data Products, Domains)
│   ├── sql_client.py      # Trino SQL client (INFORMATION_SCHEMA)
│   ├── handler.py         # Hybrid handler (REST + SQL)
│   ├── activities.py      # Temporal activities (extraction tasks)
│   ├── workflows.py       # Workflow orchestration (parallel streams)
│   ├── transformer.py     # Metadata transformation to Atlan format
│   └── sql/               # SQL query templates
│       ├── extract_catalog.sql
│       ├── extract_schema.sql
│       ├── extract_table.sql
│       ├── extract_column.sql
│       ├── extract_view.sql
│       └── test_authentication.sql
├── frontend/              # Web UI
├── models/                # Atlan entity type definitions
├── tests/
│   ├── unit/              # Unit tests
│   └── e2e/               # End-to-end tests
├── main.py                # Application entry point
├── pyproject.toml         # Dependencies
└── .env.example           # Environment variable template
```

## Workflow Execution

```
1. get_workflow_args     ─── Retrieve config from state store
2. preflight_check       ─── Validate REST + SQL connectivity
3. Parallel extraction:
   ├── REST Stream:
   │   ├── fetch_domains
   │   ├── fetch_data_products
   │   └── extract_datasets_from_products
   └── SQL Stream:
       ├── fetch_catalogs
       └── fetch_schemas + fetch_tables + fetch_columns (parallel)
```

## Authentication

Supports **Basic** and **LDAP** authentication against Starburst Enterprise. The same credentials are used for both REST API and SQL connections.

## Development

```bash
uv run poe stop-deps     # Stop dependencies
uv run pytest             # Run tests
```

## External References

- [Starburst Enterprise REST API](https://docs.starburst.io/latest/starburst-rest-api.html)
- [Starburst Enterprise Data Products](https://docs.starburst.io/latest/data-products/)
- [Trino Python Client](https://github.com/trinodb/trino-python-client)
- [Atlan Application SDK](https://github.com/atlanhq/application-sdk)

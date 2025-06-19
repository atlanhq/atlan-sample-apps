# 🕒 Freshness Monitor

A powerful application that monitors data freshness across your data assets and automatically flags stale data. Built with Application SDK for automated freshness checks and reporting.

## Features

- Automated Monitoring: Continuous monitoring of data freshness across all tables
- Smart Detection: Configurable threshold for staleness detection
- Automated Announcements: Automatically adds "Stale Data Detected" warnings to outdated tables
- Real-time Updates: Immediate flagging when data becomes stale
- Workflow Management: Leverages Application SDK for robust workflow orchestration
- API Integration: HTTP endpoints for triggering checks and integration
- Scalable Processing: Asynchronous worker for handling large datasets

## Usage

> [!NOTE]
> To run, first see [README.md](../README.md) for prerequisites.

### Environment Variables

Create a `.env` file in the `freshness_monitor` root directory with:

```env
# Freshness Configuration
THRESHOLD_DAYS=30  # Number of days to consider data as stale

# Atlan Configuration
ATLAN_API_KEY=your_atlan_api_key  # Get your API key from Atlan (see below)
ATLAN_BASE_URL=https://your-tenant.atlan.com
```

To obtain your Atlan API key:

1. Log in to your Atlan instance
2. Follow the instructions in the [API Authentication Guide](https://ask.atlan.com/hc/en-us/articles/8312649180049-API-authentication)
3. Copy the generated API key and use it in your `.env` file

### Run the Freshness Monitor

```bash
uv run main.py
```

This will start the workflow worker and the FastAPI web server.

### Access the Application

Once the application is running:

- Web Interface: Open your browser and go to `http://localhost:8000` (or the port configured for `APP_HTTP_PORT`).
- Temporal UI: Access the Temporal Web UI at `http://localhost:8233` (or your Temporal UI address) to monitor workflow executions.

## Project Structure

```mermaid
graph TD
    A[main.py] --> B[workflows/__init__.py]
    A --> C[activities/__init__.py]
    B --> C
    C --> D[Atlan API]
```

```
freshness_monitor/
├── app/
│   ├── activities/     # Task implementations
│   └── workflows/      # Workflow definitions
├── frontend/           # Frontend assets
│   ├── static/        # Static files (CSS, JS)
│   └── templates/     # HTML templates
├── main.py            # Application entry point
└── README.md          # This file
```

## Workflow Process

1. Initialization: Application sets up workflow components and API server
2. Data Discovery: Fetches metadata for tables in Atlan environment
3. Freshness Analysis:
   - Checks last update time for each table
   - Compares against threshold (THRESHOLD_DAYS)
   - Identifies stale tables
4. Announcement Creation:
   - Generates WARNING announcements for stale tables
   - Includes last update time and check date
   - Attaches to affected tables
5. Monitoring: Continuous monitoring and updates

### Announcement Example

```json
{
  "type": "WARNING",
  "title": "Stale Data Detected",
  "message": "This table contains stale data. Last updated: 2024-01-15. Data freshness check performed on 2024-03-20."
}
```

## Learning Resources

- [Atlan Application SDK Documentation](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Temporal Documentation](https://docs.temporal.io/)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

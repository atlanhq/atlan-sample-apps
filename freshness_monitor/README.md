# Freshness Monitor

## Overview
The **Freshness Monitor** is an Atlan app designed to monitor data freshness across your data assets. It leverages Atlan's Application SDK to orchestrate workflows, activities, and API triggers for automated freshness checks and reporting.

## Features
- Automated data freshness monitoring
- Configurable threshold for staleness detection
- **Automatically adds a 'Stale Data Detected' announcement to tables that have not been updated within the threshold number of days**
- Workflow-based execution using Atlan Application SDK
- API server for HTTP triggers and integration
- Asynchronous worker for scalable processing

## How It Works
1. The app fetches metadata for tables in your Atlan environment.
2. It checks the last update time for each table.
3. If a table has not been updated in more than the threshold number of days (set by `THRESHOLD_DAYS`), it is considered stale.
4. For each stale table, the app adds an announcement of type `WARNING` with the title **"Stale Data Detected"** and a message indicating the last update time and the date the freshness check was performed.

**Announcement Example:**
- **Type:** WARNING
- **Title:** Stale Data Detected
- **Message:**
  > This table contains stale data. Last updated: <stale_since>. Data freshness check performed on <check_date>.

## Quickstart / Setup

### Prerequisites
- Python 3.10+
- [Atlan Application SDK](https://github.com/atlanhq/application-sdk)
- `uv` for dependency management
- Parent env set up 

### Environment Variables
Set the following environment variables before running the app:
- `THRESHOLD_DAYS`: Number of days to consider data as stale (default: 30)
- `ATLAN_API_KEY`: Your Atlan API key with appropriate access (required)
- `ATLAN_BASE_URL`: Atlan tenant base URL (required)

Example:
```bash
export THRESHOLD_DAYS=30
export ATLAN_API_KEY="your-atlan-api-key"
export ATLAN_BASE_URL="https://your-tenant.atlan.com"

```

## Usage
Run the main application:
```bash
uv python main.py
```

This will:
- Initialize the application
- Set up the freshness workflow and worker
- Start the API server for HTTP triggers
- Optionally, start the workflow programmatically

## Project Structure
```
freshness_monitor/
├── main.py                # Application entry point
├── application.py         # App orchestration logic
├── workflows/             # Workflow definitions
├── activities/            # Activity/task implementations
├── requirements.txt       # Python dependencies
└── README.md              # This file
```


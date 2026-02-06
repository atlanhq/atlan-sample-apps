# Incident Priority Digest

Daily incident priority digest app built on the Atlan Application SDK.

Ingests incident records from workflow input and produces a digest containing:
- Counts by severity and status
- Top 10 unresolved incidents (ordered by severity)
- Incidents grouped by owning team

## Input Format

The workflow expects a `records_json` field containing a JSON array of incident objects:

```json
[
  {
    "id": "INC-001",
    "title": "Database connection pool exhausted",
    "severity": "critical",
    "status": "open",
    "owning_team": "platform",
    "created_at": "2025-01-15T08:30:00Z"
  },
  {
    "id": "INC-002",
    "title": "Slow API response times",
    "severity": "high",
    "status": "investigating",
    "owning_team": "backend",
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

### Required Fields per Incident

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique incident identifier |
| `title` | string | Short description |
| `severity` | string | One of: `critical`, `high`, `medium`, `low` |
| `status` | string | e.g. `open`, `investigating`, `resolved`, `closed` |
| `owning_team` | string | Team responsible for the incident |

Additional fields are preserved in the raw output.

## Output Format

### Raw Output (`raw/incidents/incidents.json`)

The full incident records as provided, written verbatim.

### Transformed Output (`transformed/digest/digest.json`)

```json
{
  "generated_at": "2025-01-15T12:00:00+00:00",
  "total_incidents": 25,
  "severity_counts": {
    "critical": 3,
    "high": 8,
    "medium": 10,
    "low": 4
  },
  "status_counts": {
    "open": 12,
    "investigating": 5,
    "resolved": 6,
    "closed": 2
  },
  "top_unresolved": [
    { "id": "INC-001", "severity": "critical", "status": "open", "..." : "..." }
  ],
  "by_team": {
    "platform": {
      "count": 5,
      "severity_counts": { "critical": 2, "high": 3 }
    }
  }
}
```

## Usage

```bash
# Install dependencies
uv sync

# Download Dapr components
uv run poe download-components

# Start Temporal + Dapr
uv run poe start-deps

# Run the application
uv run main.py

# Run unit tests (no runtime deps needed)
uv run pytest tests/unit/

# Run e2e tests (requires Temporal + Dapr + app running)
uv run pytest tests/e2e/

# Stop background services
uv run poe stop-deps
```

# Sample Event Processor App

A minimal v3-SDK sample demonstrating the AE-driven event-ingestion pattern:

```
event-ingestion-app  ─►  AE event-consumer-node  ─►  this workflow
```

When AE detects unprocessed rows in its events Iceberg table, it triggers
this workflow with the table name. The workflow uses the SDK's
`events_read` to read pending events, dispatches each to a hello-world
HTTP API + random classifier, and publishes the Parquet ack AE expects via
`events_ack`.

The lakehouse is a blackbox — `events_read` is the only lakehouse
touchpoint; no PyIceberg / pyarrow / daft types appear in app code.

## Pipeline

A single **`handle_events`** activity does the full read → process → ack cycle:

1. **Read in batches** — calls `events_read(namespace, table, handler=...,
   batch_size=1000, max_events=5000)`. The SDK loops internally: fetches up
   to 1000 events per batch, dispatches each batch to the `handler`, and
   stops when the source is exhausted or 5000 total events have been
   processed (whichever comes first).
2. **Handler logic** — POSTs each event to `HELLO_API_URL` (default
   `https://httpbin.org/anything`) and randomly classifies the result as
   `SUCCESS` (50%) / `RETRY` (30%) / `FAILED` (20%).
3. **Publish ack** — calls `events_ack(events, results, app_name, ...)`
   once after the loop, writing a single Parquet at
   `artifacts/sample-event-processor-app/ingestion/<yyyy>/<mm>/<dd>/<run_id>/events_ack.parquet`.

`run()` is a thin workflow body that just delegates to `handle_events`
when the trigger payload includes `iceberg_table_name`. The v3 SDK
auto-generates the underlying Temporal workflow from `run()`.

## Trigger payload

The workflow accepts the AE event-consumer payload directly — no UI form:

```python
class IngestionInput(Input):
    iceberg_table_name: str = ""
    events_namespace: str = "automation_engine"
    workflow_id: str = ""
    triggered_by: str = ""
    trigger_id: str = ""
    trigger_name: str = ""
    event_cleanup_max_retries: int = 5
    event_cleanup_ack_source: str = ""
```

## Layout

```
sample_event_processor_app/
├── app/
│   ├── application.py   # v3 App subclass (handle_events + run)
│   ├── api_client.py    # HelloApiCaller (httpx)
│   ├── lakehouse.py     # reference EVENTS_SCHEMA for local seeding
│   └── models.py        # EventRecord, ResultRecord, RandomClassifier
├── contract/            # pkl manifest for AE / Marketplace
│   ├── PklProject
│   ├── PklProject.deps.json
│   └── ingestion.pkl
├── scripts/
│   └── seed_events.py   # Local seeding into automation_engine.<table>
├── tests/unit/          # Unit tests
├── main.py              # Local-dev entrypoint
├── atlan.yaml           # App deployment manifest
├── atlan-app-registry.json
└── pyproject.toml
```

## Setup

Prereqs:

- `uv` (package manager)
- A reachable Iceberg REST catalog (e.g. local Polaris via `kubectl port-forward`)
- A local Temporal dev server

```bash
cd quickstart/sample_event_processor_app
uv sync --all-extras --all-groups
uv run poe download-components   # if you need the SDK Dapr components
```

Required environment variables:

| Variable | Description |
|---|---|
| `ICEBERG_CATALOG_URI` | Iceberg REST catalog endpoint |
| `ICEBERG_CLIENT_ID` | Catalog OAuth client id |
| `ICEBERG_CLIENT_SECRET` | Catalog OAuth client secret |
| `ICEBERG_WAREHOUSE` | Catalog warehouse name (default `context_store`) |
| `HELLO_API_URL` | Optional override for the demo API |

Atlan platform credentials (`ATLAN_API_KEY`, `ATLAN_BASE_URL`) are **not**
needed — this sample doesn't call the Atlan platform.

## Run

```bash
# 1. Start Temporal + Dapr (in a separate shell)
uv run poe start-deps

# 2. Seed some unprocessed events into automation_engine.<table>
ICEBERG_CATALOG_URI=<...> ICEBERG_CLIENT_ID=<...> ICEBERG_CLIENT_SECRET=<...> \
    uv run poe seed -- --count 25

# 3. Start the app worker + handler
ICEBERG_CATALOG_URI=<...> ICEBERG_CLIENT_ID=<...> ICEBERG_CLIENT_SECRET=<...> \
    uv run python main.py

# 4. Trigger the workflow with the AE payload shape:
#    {"iceberg_table_name": "lakehouse_batch_events"}
```

In production AE's event-consumer-node triggers this workflow automatically
when its events table receives unprocessed rows; step 4 is for local
testing only.

## Generate marketplace manifest

```bash
uv run poe generate          # requires the pkl CLI
# → app/generated/ingestion/{manifest.json, sample-event-processor-app.json, _input.py}
```

## Tests

```bash
uv run poe test
```

Unit tests cover the random classifier distribution and the `run()`
orchestration with mocked tasks — no Iceberg or HTTP access required.

## Notes

- The random classifier and hello-world API call have no business meaning;
  they exist only to demonstrate the AE event-driven ingestion pattern
  end-to-end against a real lakehouse via `events_read` + `events_ack`.
- `events_read` builds its `LakehouseReader` from `ICEBERG_*` env vars on
  each call — apps never pass a catalog or credentials in code.
- The Parquet ack path layout matches what AE consumes downstream:
  `artifacts/<app>/<workflow>/<yyyy>/<mm>/<dd>/<run_id>/events_ack.parquet`.

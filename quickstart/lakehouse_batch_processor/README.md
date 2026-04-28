# Lakehouse Batch Processor (sample)

A minimal v3-SDK sample app that demonstrates the same shape as the
Databricks reverse-sync workflow but does nothing useful — it reads
"events" from an Iceberg lakehouse, calls a public hello-world API,
randomly classifies the outcome as `SUCCESS` / `RETRY` / `FAILED`, and
appends a batch of outcomes to a results Iceberg table.

```
events Iceberg table  →  hello API  →  random classifier  →  outcomes Iceberg table
```

## Pipeline

1. `fetch_events` – PyIceberg scan of `<events_namespace>.<events_table>`.
2. `process_events` – POST each event to `HELLO_API_URL`
   (default `https://httpbin.org/anything`), then classify the response
   randomly (50% `SUCCESS` / 30% `RETRY` / 20% `FAILED`).
3. `write_outcomes` – Append outcome rows to
   `<outcomes_namespace>.<outcomes_table>` (Iceberg, partitioned by
   `status`). The table + namespace are auto-created on first write.

The `run()` method on `LakehouseBatchProcessorApp` orchestrates these
three `@task` methods; v3 SDK auto-generates the underlying Temporal
workflow from `run()`.

## Layout

```
lakehouse_batch_processor/
├── app/
│   ├── application.py   # v3 App subclass (3 @task methods + run())
│   ├── api_client.py    # HelloApiCaller (httpx)
│   ├── lakehouse.py     # IcebergReader + IcebergWriter
│   └── models.py        # EventRecord, OutcomeRecord, RandomClassifier
├── scripts/
│   └── seed_events.py   # Seed sample events into the events table
├── tests/unit/          # Unit tests
├── main.py              # Local-dev entrypoint
├── atlan.yaml           # App manifest
├── atlan-app-registry.json
└── pyproject.toml
```

## Setup

Prereqs:

- `uv` (package manager)
- A reachable Iceberg REST catalog (e.g. local Polaris via `kubectl port-forward`)
- A local Temporal dev server

```bash
cd quickstart/lakehouse_batch_processor
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
needed for this sample — it does not call the Atlan platform.

## Run

```bash
# 1. Start Temporal + Dapr (in a separate shell)
uv run poe start-deps

# 2. Seed some events
ICEBERG_CATALOG_URI=<...> ICEBERG_CLIENT_ID=<...> ICEBERG_CLIENT_SECRET=<...> \
    uv run poe seed -- --count 25

# 3. Start the app worker + handler
ICEBERG_CATALOG_URI=<...> ICEBERG_CLIENT_ID=<...> ICEBERG_CLIENT_SECRET=<...> \
    uv run python main.py
```

Trigger a workflow via the SDK handler (default port 8000) or by calling
the app's input class directly from a script.

## Tests

```bash
uv run poe test
```

The unit tests cover the random classifier distribution and the
`run()` orchestration with mocked tasks — no Iceberg or HTTP access required.

## Notes

- This is a **sample**. The random classifier is intentionally non-deterministic
  and the API call has no business meaning — both exist only to demonstrate
  the v3 SDK App + `@task` pattern end-to-end against a real lakehouse.
- The outcomes table is **append-only** and partitioned by `status` so a
  consumer can scan `WHERE status = 'RETRY'` cheaply.

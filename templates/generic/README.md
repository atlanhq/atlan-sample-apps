# Generic Connector Template

A minimal v3 scaffold for building Atlan connector apps with the
[Application SDK](https://github.com/atlanhq/application-sdk).

## Structure

```
templates/generic/
├── pyproject.toml              # Project config and dependencies
├── Dockerfile                  # Container image (extends app-runtime-base:3)
├── atlan.yaml                  # App registry metadata
├── main.py                     # Production entry point
├── .env.example                # Required environment variables
├── app/
│   ├── connector.py            # Main App class — implement your logic here
│   ├── contracts.py            # Input / Output data contracts
│   └── run_dev.py              # Local development server
└── tests/
    ├── unit/test_contracts.py  # Contract round-trip tests
    └── integration/
        ├── conftest.py         # Mock infrastructure + Temporal wiring
        └── test_generic.py     # Full workflow integration tests
```

## Quick start

```bash
# 1. Install dependencies
uv sync --all-extras --all-groups

# 2. Copy and configure environment
cp .env.example .env

# 3. Start Temporal dev server (in a separate terminal)
temporal server start-dev --dynamic-config-value frontend.WorkerHeartbeatsEnabled=true

# 4. Start the dev server
python -m app.run_dev

# 5. Trigger a test workflow
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {"qualifiedName": "default/generic/test", "name": "test"},
    "source": "https://example.com/data",
    "load_to_atlan": false
  }'

# 6. Check the result
curl http://localhost:8000/workflows/v1/result/<workflow_id>
```

## Implementing your connector

1. **Extract** (`app/connector.py → extract()`): fetch data from your source and write
   one JSON object per line to `output_file`.

2. **Transform** (`app/connector.py → transform()`): read raw records from
   `input.raw_file` and write Atlan asset JSONL using `pyatlan` asset types.

3. **Contracts** (`app/contracts.py`): add input fields specific to your source system
   (credentials, filters, connection strings, etc.).

4. **Contract skill**: run `/contract` to generate `contract/app.pkl` and
   `app/generated/` artifacts that wire the workflow to the Atlan UI.

5. **Tests**: add unit tests in `tests/unit/` and integration tests in
   `tests/integration/`.

## Key concepts

| Concept | Description |
|---|---|
| `@task` | Temporal activity — all I/O and side-effects go here |
| `run()` | Workflow orchestrator — must be deterministic; only calls tasks |
| `FileReference` | Typed file handle managed by the SDK (local ↔ object storage) |
| `ConnectionRef` | Typed Atlan connection reference passed from the workflow UI |
| `self.upload()` | Built-in task that uploads a local file to object storage |
| `self.require()` | Raises `NonRetryableError` if a required value is `None` |

See the [Application SDK docs](https://github.com/atlanhq/application-sdk) for full reference.

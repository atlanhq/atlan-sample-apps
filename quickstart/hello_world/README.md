# Hello World

A minimal starter app demonstrating how to build applications with the Atlan Application SDK (v3).

The pattern here is the foundation for every app you'll build:
- `app/contracts.py` — typed `Input` / `Output` models
- `app/connector.py` — an `App` subclass with `@task`-decorated methods and a `run()` orchestrator

For a full scaffold (auth, handler, Dapr secret store, SQL client), run the [`/scaffold-app`](https://github.com/atlanhq/application-sdk/blob/main/.claude/skills/scaffold-app/SKILL.md) skill.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/)
- [Temporal CLI](https://docs.temporal.io/cli)

### Setup guides
- [macOS](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md)
- [Linux](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md)
- [Windows](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Download Dapr components:**
   ```bash
   uv run poe download-components
   ```

3. **Start Temporal + Dapr (separate terminal):**
   ```bash
   uv run poe start-deps
   ```

4. **Run the app:**
   ```bash
   uv run python run_dev.py
   ```

The app listens on **http://localhost:8000**. Trigger a run via:
```bash
curl -X POST http://localhost:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

Watch the Temporal UI at **http://localhost:8233**.

## Project Structure

```
hello_world/
├── app/
│   ├── contracts.py    # HelloInput / HelloOutput models
│   └── connector.py    # HelloWorldApp with @task + run()
├── tests/
│   └── unit/           # Unit tests for the App class
├── run_dev.py          # Local dev entry point (worker + handler combined)
├── atlan.yaml          # App manifest (execution_mode, dapr config)
├── Dockerfile          # Container image definition
├── .env.example        # Required environment variables
└── pyproject.toml      # Dependencies and poe tasks
```

## Running Tests

```bash
uv run pytest tests/unit/
```

## Stop Dependencies

```bash
uv run poe stop-deps
```

## Learning Resources

- [Atlan Application SDK docs](https://github.com/atlanhq/application-sdk/tree/main/docs)
- [Temporal documentation](https://docs.temporal.io/)

> [!TIP]
> Want to containerize this app? See [Build Docker images](https://github.com/atlanhq/atlan-sample-apps/tree/main/README.md#build-docker-images) in the repo root README.

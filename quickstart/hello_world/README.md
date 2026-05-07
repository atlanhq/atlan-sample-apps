# Hello World

A minimal starter app demonstrating how to build applications with the Atlan Application SDK (v3).

Two files are all you need:

| File | Purpose |
|---|---|
| `app/contracts.py` | Typed `Input` / `Output` models |
| `app/connector.py` | `App` subclass with `@task` methods and a `run()` orchestrator |

The SDK handles Temporal workflow execution, the HTTP handler, retries, heartbeating, and observability — your code just defines the logic.

> Want a full scaffold with auth, secrets, and a SQL client? Use the [`/scaffold-app`](https://github.com/atlanhq/application-sdk/blob/main/.claude/skills/scaffold-app/SKILL.md) skill.

## Prerequisites

| Tool | Install |
|---|---|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) |
| uv | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| Dapr CLI | [docs.dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/) |
| Temporal CLI | [docs.temporal.io/cli](https://docs.temporal.io/cli) |

Platform-specific setup: [macOS](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md) · [Linux](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md) · [Windows](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

**1. Install dependencies**
```bash
uv sync
```

**2. Download Dapr components**
```bash
uv run poe download-components
```

**3. Start Temporal + Dapr** (leave this terminal running)
```bash
uv run poe start-deps
```

**4. Run the app** (new terminal)
```bash
uv run python main.py
```

**5. Trigger a run**
```bash
curl -X POST http://localhost:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

- App: **http://localhost:8000**
- Temporal UI: **http://localhost:8233**

## Project Structure

```
hello_world/
├── app/
│   ├── contracts.py          # HelloInput / HelloOutput models
│   └── connector.py          # HelloWorldApp: @task + run()
├── tests/
│   └── unit/                 # Unit tests (no Temporal needed)
├── main.py                   # Local entry point (worker + handler in one process)
├── Dockerfile                # Production image
├── atlan.yaml                # App manifest
├── atlan-scaffold-overrides.json  # Scaffold config (execution_mode, split_deployment)
├── .env.example              # Required env vars
└── pyproject.toml            # Dependencies and dev tasks
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

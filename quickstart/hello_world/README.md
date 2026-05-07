# Hello World

A minimal starter app demonstrating how to build applications with the Atlan Application SDK (v3).

| File | Purpose |
|---|---|
| `contract/app.pkl` | PKL contract — defines the workflow input UI config |
| `app/generated/_input.py` | Auto-generated from `app.pkl` via `make generate` — never edit manually |
| `app/contracts.py` | Re-exports `AppInputContract` as `HelloWorldInput`; defines task-level `HelloInput` / `HelloOutput` |
| `app/connector.py` | `App` subclass with `@task` methods and a `run()` orchestrator |

The SDK handles Temporal workflow execution, the HTTP handler, retries, heartbeating, and observability — your code just defines the logic.

> Want a full scaffold with auth, secrets, and a SQL client? Use the [`/scaffold-app`](https://github.com/atlanhq/application-sdk/blob/main/.claude/skills/scaffold-app/SKILL.md) skill.

## Prerequisites

| Tool | Install |
|---|---|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) |
| uv | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| Pkl CLI | [pkl-lang.org](https://pkl-lang.org/main/current/pkl-cli/index.html) |
| Dapr CLI | [docs.dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/) |
| Temporal CLI | [docs.temporal.io/cli](https://docs.temporal.io/cli) |

Platform-specific setup: [macOS](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/MAC.md) · [Linux](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/LINUX.md) · [Windows](https://github.com/atlanhq/application-sdk/blob/main/docs/docs/setup/WINDOWS.md)

## Quick Start

**1. Install dependencies**
```bash
uv sync
```

**2. Regenerate the input contract** (only needed after editing `contract/app.pkl`)
```bash
make generate
```

**3. Download Dapr components**
```bash
uv run poe download-components
```

**4. Start Temporal + Dapr** (leave this terminal running)
```bash
uv run poe start-deps
```

**5. Run the app** (new terminal)
```bash
uv run python main.py
```

**6. Trigger a run**
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
├── contract/
│   ├── app.pkl               # PKL contract — edit this to change the workflow input
│   ├── PklProject            # PKL project (declares app-contract-toolkit dependency)
│   └── PklProject.deps.json  # Resolved PKL dependency checksums
├── app/
│   ├── generated/
│   │   └── _input.py         # AUTO-GENERATED — do not edit
│   ├── contracts.py          # HelloWorldInput / HelloInput / HelloOutput
│   └── connector.py          # HelloWorldApp: @task + run()
├── tests/
│   └── unit/                 # Unit tests (no Temporal needed)
├── main.py                   # Local entry point (worker + handler in one process)
├── Makefile                  # make generate / make check-generate
├── Dockerfile                # Production image
├── atlan.yaml                # App manifest
└── pyproject.toml            # Dependencies and dev tasks
```

## Regenerating the Contract

Edit `contract/app.pkl` to add or change workflow inputs, then run:

```bash
make generate
```

Commit both `contract/app.pkl` and the updated `app/generated/` files together.

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
- [Pkl language](https://pkl-lang.org/)

> [!TIP]
> Want to containerize this app? See [Build Docker images](https://github.com/atlanhq/atlan-sample-apps/tree/main/README.md#build-docker-images) in the repo root README.

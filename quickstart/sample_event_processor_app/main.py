"""Local-dev entrypoint for the Sample Event Processor App.

In production the SDK CLI runs the app:

    application-sdk --mode combined

When run directly (``uv run python main.py``) we use the SDK's
``run_combined_mode`` to start a single-process Temporal worker + FastAPI
server.
"""

from __future__ import annotations

import asyncio
import os

# Pin the application name BEFORE importing the SDK; constants are read
# at import time.
os.environ.setdefault("ATLAN_APPLICATION_NAME", "sample-event-processor-app")
os.environ.setdefault("ATLAN_LOCAL_DEVELOPMENT", "true")

# Importing the App class triggers SDK auto-registration via __init_subclass__.
from app.application import SampleEventProcessorApp  # noqa: E402, F401
from application_sdk.main import AppConfig, run_combined_mode  # noqa: E402


async def main() -> None:
    config = AppConfig(
        mode="combined",
        app_module="app.application:SampleEventProcessorApp",
        task_queue="sample-event-processor-app-queue",
        handler_host="127.0.0.1",
        handler_port=int(os.environ.get("ATLAN_APP_HTTP_PORT", "8000")),
    )
    await run_combined_mode(config)


if __name__ == "__main__":
    asyncio.run(main())

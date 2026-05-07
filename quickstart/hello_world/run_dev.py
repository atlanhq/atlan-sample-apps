"""Local development entry point.

Boots the worker and handler in a single process so you can test
the full request→workflow→task round-trip without separate terminals.

Usage:
    uv run python run_dev.py
"""

import asyncio

from app.connector import HelloWorldApp

from application_sdk.main import run_dev_combined

if __name__ == "__main__":
    asyncio.run(
        run_dev_combined(
            HelloWorldApp,
            example_input={"name": "World"},
        )
    )
